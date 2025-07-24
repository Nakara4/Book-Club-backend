from django.shortcuts import render
from rest_framework import status, permissions, generics, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from .models import BookClub, Membership
from .serializers import (
    UserRegistrationSerializer, UserSerializer, LoginSerializer,
    BookClubListSerializer, BookClubDetailSerializer, BookClubCreateUpdateSerializer,
    BookClubMembershipSerializer, BookClubJoinSerializer, BookClubInviteSerializer,
    BookClubStatsSerializer, BookClubSearchSerializer
)


def home(request):
    return render(request, 'myapp/home.html', {'message': 'Welcome to My Django App!'})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """
    Register a new user
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        return Response({
            'message': 'User created successfully',
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
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
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except User.DoesNotExist:
            return Response({
                'error': 'User with this email does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# BOOK CLUB VIEWS
# ============================================================================

class BookClubViewSet(ModelViewSet):
    """
    A comprehensive ViewSet for managing book clubs.
    
    Provides:
    - GET /book-clubs/ - List all book clubs
    - POST /book-clubs/ - Create a new book club
    - GET /book-clubs/{id}/ - Get specific book club details
    - PUT/PATCH /book-clubs/{id}/ - Update book club
    - DELETE /book-clubs/{id}/ - Delete book club
    - GET /book-clubs/my-clubs/ - Get user's book clubs
    - POST /book-clubs/{id}/join/ - Join a book club
    - POST /book-clubs/{id}/leave/ - Leave a book club
    - GET /book-clubs/{id}/stats/ - Get club statistics
    - POST /book-clubs/{id}/invite/ - Invite user to club
    """
    queryset = BookClub.objects.all()
    permission_classes = [permissions.IsAuthenticated]
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
                {'error': 'Only the creator can delete this book club.'},
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
                {'error': 'You are already a member of this book club.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if club is at capacity
        if book_club.member_count >= book_club.max_members:
            return Response(
                {'error': 'This book club is at full capacity.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if it's a private club (simplified - in real app you'd check invitations)
        if book_club.is_private and book_club.creator != user:
            return Response(
                {'error': 'This is a private book club. You need an invitation to join.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create membership
        membership = Membership.objects.create(
            user=user,
            book_club=book_club,
            role='member'
        )
        
        serializer = BookClubMembershipSerializer(membership, context={'request': request})
        return Response({
            'message': f'Successfully joined {book_club.name}!',
            'membership': serializer.data
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
                {'error': 'Club creators cannot leave their own clubs. Delete the club instead.'},
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
                {'error': 'You are not a member of this book club.'},
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
                {'error': 'You do not have permission to view statistics for this private club.'},
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
                {'error': 'You do not have permission to invite users to this book club.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BookClubInviteSerializer(
            data=request.data,
            context={'request': request, 'book_club_id': book_club.id}
        )
        
        if serializer.is_valid():
            # In a real application, you would send an email invitation here
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
    """
    Advanced search view for book clubs with filters and user context
    """
    serializer_class = BookClubSearchSerializer
    permission_classes = [permissions.AllowAny]  # Allow anonymous users to search
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
