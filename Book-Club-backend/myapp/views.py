from django.shortcuts import render, get_object_or_404
from rest_framework import status, permissions, generics, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .serializers import CustomTokenObtainPairSerializer
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from .models import BookClub, Membership
from .serializers import (
    UserRegistrationSerializer, UserSerializer, LoginSerializer,
    BookClubListSerializer, BookClubDetailSerializer, BookClubCreateUpdateSerializer,
    BookClubMembershipSerializer, BookClubJoinSerializer, BookClubInviteSerializer,
    BookClubStatsSerializer, BookClubSearchSerializer, AdminUserSerializer
)
from rest_framework.exceptions import ValidationError

from django.http import JsonResponse
from .pagination import StandardResultsSetPagination, SearchResultsPagination
from .api_settings import PAGINATION_CONFIG, DEFAULT_FILTER_BACKENDS, DEFAULT_PERMISSION_CLASSES
from .exceptions import custom_exception_handler


def home(request):
    return JsonResponse({
        'message': 'Welcome to Book Club API!',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': {
            'auth': {
                'register': '/auth/register/',
                'login': '/auth/login/',
                'logout': '/auth/logout/',
                'profile': '/auth/profile/',
                'token': '/api/token/',
                'token_refresh': '/api/token/refresh/',
                'token_verify': '/api/token/verify/'
            },
            'bookclubs': {
                'list': '/api/bookclubs/',
                'search': '/api/book-clubs/search/',
                'discover': '/api/book-clubs/discover/',
                'my_memberships': '/api/my-memberships/'
            }
        }
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """
    Register a new user
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate JWT tokens with custom claims
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        access_token = refresh.access_token
        
        return Response({
            'message': 'User created successfully',
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)
    
    # Manually trigger custom exception handler for validation errors
    exc = ValidationError(serializer.errors)
    return custom_exception_handler(exc, {'request': request})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    """
    Login user with email and password
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        try:
            # Find user by email
            user = User.objects.get(email=email)
            
            # Authenticate with username and password
            user = authenticate(username=user.username, password=password)
            
            if user:
                # Generate JWT tokens with custom claims
                refresh = CustomTokenObtainPairSerializer.get_token(user)
                access_token = refresh.access_token
                
                return Response({
                    'message': 'Login successful',
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'access': str(access_token),
                        'refresh': str(refresh),
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'detail': 'Invalid credentials'  # Changed from 'error' to 'detail'
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except User.DoesNotExist:
            return Response({
                'detail': 'User with this email does not exist'  # Changed from 'error' to 'detail'
            }, status=status.HTTP_404_NOT_FOUND)
    
    # Manually trigger custom exception handler for validation errors
    exc = ValidationError(serializer.errors)
    return custom_exception_handler(exc, {'request': request})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile(request):
    """
    Get current user profile
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout(request):
    """
    Logout user by blacklisting the refresh token
    """
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)  # Changed from 'error' to 'detail'


# ============================================================================
# BOOK CLUB VIEWS
# ============================================================================

class BookClubViewSet(ModelViewSet):
    queryset = BookClub.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_private', 'creator']
    search_fields = ['name', 'description', 'location']
    ordering_fields = ['created_at', 'name', 'member_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        Return different serializers based on the action
        """
        if self.action == 'list':
            return BookClubListSerializer
        elif self.action == 'retrieve':
            return BookClubDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BookClubCreateUpdateSerializer
        elif self.action == 'stats':
            return BookClubStatsSerializer
        elif self.action == 'search':
            return BookClubSearchSerializer
        return BookClubListSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions and privacy settings
        """
        queryset = BookClub.objects.select_related('creator').prefetch_related(
            'members', 'reading_sessions__book'
        )
        
        # If user is not authenticated, only show public clubs
        if not self.request.user.is_authenticated:
            return queryset.filter(is_private=False)
        
        # For authenticated users, show:
        # 1. All public clubs
        # 2. Private clubs they're members of
        # 3. Private clubs they created
        user = self.request.user
        user_memberships = Membership.objects.filter(user=user, is_active=True).values_list('book_club_id', flat=True)
        
        return queryset.filter(
            Q(is_private=False) |  # Public clubs
            Q(creator=user) |      # User's own clubs
            Q(id__in=user_memberships)  # Clubs user is member of
        ).distinct()
    
    def perform_create(self, serializer):
        """
        Set the creator when creating a book club
        """
        serializer.save(creator=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """
        Only allow creators to delete their book clubs
        """
        book_club = self.get_object()
        if book_club.creator != request.user:
            return Response(
                {'detail': 'Only the creator can delete this book club.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def my_clubs(self, request):
        """
        Get all book clubs for the current user (created + member of)
        """
        user = request.user
        
        # Get clubs user created
        created_clubs = BookClub.objects.filter(creator=user)
        
        # Get clubs user is a member of
        member_clubs = BookClub.objects.filter(
            members=user,
            membership__is_active=True
        ).exclude(creator=user)
        
        # Combine and serialize
        all_clubs = created_clubs.union(member_clubs).order_by('-created_at')
        serializer = BookClubListSerializer(all_clubs, many=True, context={'request': request})
        
        return Response({
            'created_count': created_clubs.count(),
            'member_count': member_clubs.count(),
            'total_count': all_clubs.count(),
            'clubs': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """
        Join a book club
        """
        book_club = self.get_object()
        user = request.user
        
        # Check if user is already a member
        if Membership.objects.filter(user=user, book_club=book_club, is_active=True).exists():
            return Response(
                {'detail': 'You are already a member of this book club.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if club is at capacity
        if book_club.member_count >= book_club.max_members:
            return Response(
                {'detail': 'This book club is at full capacity.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if it's a private club (simplified - in real app you'd check invitations)
        if book_club.is_private and book_club.creator != user:
            return Response(
                {'detail': 'This is a private book club. You need an invitation to join.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create membership
        membership = Membership.objects.create(
            user=user,
            book_club=book_club,
            role='member'
        )
        
        # Get updated book club data with is_member flag
        club_serializer = BookClubDetailSerializer(book_club, context={'request': request})
        membership_serializer = BookClubMembershipSerializer(membership, context={'request': request})
        
        return Response({
            'message': f'Successfully joined {book_club.name}!',
            'membership': membership_serializer.data,
            'book_club': club_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """
        Leave a book club
        """
        book_club = self.get_object()
        user = request.user
        
        # Check if user is the creator
        if book_club.creator == user:
            return Response(
                {'detail': 'Club creators cannot leave their own clubs. Delete the club instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find and deactivate membership
        try:
            membership = Membership.objects.get(user=user, book_club=book_club, is_active=True)
            membership.is_active = False
            membership.save()
            
            return Response({
                'message': f'Successfully left {book_club.name}.'
            }, status=status.HTTP_200_OK)
        
        except Membership.DoesNotExist:
            return Response(
                {'detail': 'You are not a member of this book club.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get detailed statistics for a book club
        """
        book_club = self.get_object()
        
        # Check if user has permission to view stats
        if book_club.is_private and not Membership.objects.filter(
            user=request.user, book_club=book_club, is_active=True
        ).exists() and book_club.creator != request.user:
            return Response(
                {'detail': 'You do not have permission to view statistics for this private club.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BookClubStatsSerializer(book_club, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def invite(self, request, pk=None):
        """
        Invite a user to join the book club
        """
        book_club = self.get_object()
        user = request.user
        
        # Check if user has permission to invite (creator or admin/moderator)
        membership = Membership.objects.filter(
            user=user, book_club=book_club, is_active=True
        ).first()
        
        if not membership or (membership.role == 'member' and book_club.creator != user):
            return Response(
                {'detail': 'You do not have permission to invite users to this book club.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BookClubInviteSerializer(
            data=request.data,
            context={'request': request, 'book_club_id': book_club.id}
        )
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            message = serializer.validated_data.get('message', '')
            
            # For now, just return success message
            return Response({
                'message': f'Invitation sent to {email}',
                'book_club': book_club.name,
                'invited_by': user.get_full_name() or user.username
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookClubSearchView(generics.ListAPIView):
    serializer_class = BookClubSearchSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = SearchResultsPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['name', 'description', 'location', 'creator__username']
    filterset_fields = ['is_private']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return searchable book clubs based on user permissions
        """
        queryset = BookClub.objects.select_related('creator').prefetch_related('members')
        
        # Anonymous users can only see public clubs
        if not self.request.user.is_authenticated:
            return queryset.filter(is_private=False)
        
        # Authenticated users can see all public clubs and their private clubs
        user = self.request.user
        user_memberships = Membership.objects.filter(user=user, is_active=True).values_list('book_club_id', flat=True)
        
        return queryset.filter(
            Q(is_private=False) |
            Q(creator=user) |
            Q(id__in=user_memberships)
        ).distinct()


    def get_exception_handler(self):
        return custom_exception_handler


# ============================================================================
# ADMIN VIEWS
# ============================================================================

class AdminUserView(generics.ListAPIView, generics.UpdateAPIView):
    """View for admin to list and promote users"""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination
    lookup_url_kwarg = 'user_id'
    
    def get_queryset(self):
        """Exclude superusers from the list"""
        return User.objects.filter(is_superuser=False).order_by('-date_joined')
    
    def get_object(self):
        """Get user object for updating"""
        if 'user_id' not in self.kwargs:
            return super().get_object()
        
        obj = get_object_or_404(self.get_queryset(), pk=self.kwargs['user_id'])
        self.check_object_permissions(self.request, obj)
        return obj
    
    def update(self, request, *args, **kwargs):
        """Promote or demote a user to/from staff"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        action = "promoted to staff" if instance.is_staff else "demoted from staff"
        return Response({
            **serializer.data,
            'message': f'User {instance.username} successfully {action}.'
        })



# ============================================================================
# ADDITIONAL BOOK CLUB API VIEWS
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_club_memberships(request):
    """
    Get all memberships for the current user with role information
    """
    user = request.user
    memberships = Membership.objects.filter(
        user=user, is_active=True
    ).select_related('book_club__creator').order_by('-joined_at')
    
    serializer = BookClubMembershipSerializer(memberships, many=True, context={'request': request})
    
    return Response({
        'count': memberships.count(),
        'memberships': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def book_club_discovery(request):
    """
    Discover book clubs - featured, popular, and recent
    """
    # Featured clubs (public clubs with most members)
    featured_clubs = BookClub.objects.filter(
        is_private=False
    ).annotate(
        member_count_annotated=Count('members')
    ).order_by('-member_count_annotated')[:5]
    
    # Recent clubs (newest public clubs)
    recent_clubs = BookClub.objects.filter(
        is_private=False
    ).order_by('-created_at')[:5]
    
    # Popular clubs (most active discussions)
    popular_clubs = BookClub.objects.filter(
        is_private=False
    ).annotate(
        discussion_count=Count('discussions')
    ).order_by('-discussion_count')[:5]
    
    context = {'request': request}
    
    return Response({
        'featured': BookClubSearchSerializer(featured_clubs, many=True, context=context).data,
        'recent': BookClubSearchSerializer(recent_clubs, many=True, context=context).data,
        'popular': BookClubSearchSerializer(popular_clubs, many=True, context=context).data,
        'total_public_clubs': BookClub.objects.filter(is_private=False).count()
    })
