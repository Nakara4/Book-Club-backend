from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
    Author, Genre, Book, BookClub, Membership, ReadingSession,
    Review, ReadingProgress, Discussion, DiscussionReply,
    BookRecommendation, BookList, Follow
)


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password', 'first_name', 'last_name')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'is_staff', 'is_superuser')
        read_only_fields = ('id', 'date_joined', 'is_staff', 'is_superuser')


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin user operations (promoting users to staff)"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'date_joined')
        read_only_fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_superuser', 'date_joined')
    
    def update(self, instance, validated_data):
        """Only allow updating is_staff field"""
        instance.is_staff = validated_data.get('is_staff', instance.is_staff)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that includes is_staff in the token payload
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['is_staff'] = user.is_staff
        
        return token


# Author Serializers
class AuthorSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Author
        fields = ['id', 'first_name', 'last_name', 'full_name', 'bio', 'birth_date', 'death_date', 'website']


# Genre Serializers
class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'description']


# Book Serializers
class BookSimpleSerializer(serializers.ModelSerializer):
    """Simplified serializer for book lists"""
    authors = AuthorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()
    
    class Meta:
        model = Book
        fields = ['id', 'title', 'authors', 'cover_image', 'genres', 'average_rating', 'publication_date']


class BookDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual book views"""
    authors = AuthorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    author_names = serializers.ReadOnlyField()
    average_rating = serializers.ReadOnlyField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'subtitle', 'authors', 'author_names', 'isbn', 'isbn_10',
            'description', 'publication_date', 'publisher', 'page_count', 'language',
            'cover_image', 'genres', 'goodreads_url', 'amazon_url', 'average_rating'
        ]


class BookCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating books"""
    authors = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), many=True)
    genres = serializers.PrimaryKeyRelatedField(queryset=Genre.objects.all(), many=True, required=False)
    
    class Meta:
        model = Book
        fields = [
            'title', 'subtitle', 'authors', 'isbn', 'isbn_10', 'description',
            'publication_date', 'publisher', 'page_count', 'language',
            'cover_image', 'genres', 'goodreads_url', 'amazon_url'
        ]


# Membership Serializers
class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Membership
        fields = ['id', 'user', 'role', 'joined_at', 'is_active']


# Book Club Serializers
class BookClubListSerializer(serializers.ModelSerializer):
    """Simplified serializer for book club lists"""
    creator = UserSerializer(read_only=True)
    member_count = serializers.ReadOnlyField()
    current_book = BookSimpleSerializer(read_only=True)
    is_member = serializers.SerializerMethodField()
    image = serializers.ImageField(use_url=True, read_only=True)
    
    def get_is_member(self, obj):
        """Check if current user is a member"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Membership.objects.filter(
                user=request.user,
                book_club=obj,
                is_active=True
            ).exists()
        return False

    class Meta:
        model = BookClub
        fields = [
            'id', 'name', 'description', 'creator', 'image', 'category', 'is_private',
            'member_count', 'current_book', 'created_at', 'is_member'
        ]


class BookClubDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual book club views"""
    creator = UserSerializer(read_only=True)
    members = MembershipSerializer(source='membership_set', many=True, read_only=True)
    member_count = serializers.ReadOnlyField()
    current_book = BookSimpleSerializer(read_only=True)
    is_member = serializers.SerializerMethodField()
    image = serializers.ImageField(use_url=True, read_only=True)

    def get_is_member(self, obj):
        """Check if current user is a member"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Membership.objects.filter(
                user=request.user,
                book_club=obj,
                is_active=True
            ).exists()
        return False
    
    class Meta:
        model = BookClub
        fields = [
            'id', 'name', 'description', 'creator', 'image', 'category', 'members', 'is_private',
            'max_members', 'location', 'meeting_frequency', 'member_count',
            'current_book', 'created_at', 'updated_at', 'is_member'
        ]


class BookClubCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating book clubs"""
    image = serializers.ImageField(use_url=True, required=False)
    
    class Meta:
        model = BookClub
        fields = [
            'name', 'description', 'image', 'category', 'is_private', 'max_members',
            'location', 'meeting_frequency'
        ]
    
    def validate_name(self, value):
        """Ensure book club name is unique for the user"""
        user = self.context['request'].user
        if BookClub.objects.filter(name=value, creator=user).exists():
            raise serializers.ValidationError("You already have a book club with this name.")
        return value
    
    def validate_max_members(self, value):
        """Ensure max_members is reasonable"""
        if value < 2:
            raise serializers.ValidationError("A book club must allow at least 2 members.")
        if value > 1000:
            raise serializers.ValidationError("Maximum members cannot exceed 1000.")
        return value
    
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        book_club = super().create(validated_data)
        
        # Automatically add creator as admin member
        Membership.objects.create(
            user=book_club.creator,
            book_club=book_club,
            role='admin'
        )
        
        return book_club


class BookClubMembershipSerializer(serializers.ModelSerializer):
    """Serializer for managing book club memberships"""
    user = UserSerializer(read_only=True)
    book_club = BookClubListSerializer(read_only=True)
    
    class Meta:
        model = Membership
        fields = ['id', 'user', 'book_club', 'role', 'joined_at', 'is_active']
        read_only_fields = ['joined_at']


class BookClubJoinSerializer(serializers.Serializer):
    """Serializer for joining a book club"""
    book_club_id = serializers.IntegerField()
    
    def validate_book_club_id(self, value):
        """Validate that the book club exists and is joinable"""
        try:
            book_club = BookClub.objects.get(id=value)
        except BookClub.DoesNotExist:
            raise serializers.ValidationError("Book club does not exist.")
        
        user = self.context['request'].user
        
        # Check if user is already a member
        if Membership.objects.filter(user=user, book_club=book_club).exists():
            raise serializers.ValidationError("You are already a member of this book club.")
        
        # Check if club is at capacity
        if book_club.member_count >= book_club.max_members:
            raise serializers.ValidationError("This book club is at full capacity.")
        
        return value
    
    def create(self, validated_data):
        book_club = BookClub.objects.get(id=validated_data['book_club_id'])
        user = self.context['request'].user
        
        membership = Membership.objects.create(
            user=user,
            book_club=book_club,
            role='member'
        )
        
        return membership


class BookClubInviteSerializer(serializers.Serializer):
    """Serializer for inviting users to a book club"""
    email = serializers.EmailField()
    message = serializers.CharField(max_length=500, required=False)
    
    def validate_email(self, value):
        """Validate that the user exists and is not already a member"""
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        
        book_club_id = self.context.get('book_club_id')
        if Membership.objects.filter(user=user, book_club_id=book_club_id).exists():
            raise serializers.ValidationError("This user is already a member of the book club.")
        
        return value


class BookClubStatsSerializer(serializers.ModelSerializer):
    """Serializer for book club statistics"""
    creator = UserSerializer(read_only=True)
    member_count = serializers.ReadOnlyField()
    current_book = BookSimpleSerializer(read_only=True)
    total_books_read = serializers.SerializerMethodField()
    active_discussions = serializers.SerializerMethodField()
    recent_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = BookClub
        fields = [
            'id', 'name', 'description', 'creator', 'member_count',
            'current_book', 'total_books_read', 'active_discussions',
            'recent_activity', 'created_at'
        ]
    
    def get_total_books_read(self, obj):
        """Get total number of completed reading sessions"""
        return obj.reading_sessions.filter(status='completed').count()
    
    def get_active_discussions(self, obj):
        """Get number of active discussions"""
        from datetime import datetime, timedelta
        last_week = datetime.now() - timedelta(days=7)
        return obj.discussions.filter(created_at__gte=last_week).count()
    
    def get_recent_activity(self, obj):
        """Get recent activity summary"""
        from datetime import datetime, timedelta
        last_week = datetime.now() - timedelta(days=7)
        
        recent_discussions = obj.discussions.filter(created_at__gte=last_week).count()
        recent_reviews = Review.objects.filter(
            reading_session__book_club=obj,
            created_at__gte=last_week
        ).count()
        
        return {
            'new_discussions': recent_discussions,
            'new_reviews': recent_reviews,
            'period': 'last_7_days'
        }


class BookClubSearchSerializer(serializers.ModelSerializer):
    """Serializer for book club search results"""
    creator = UserSerializer(read_only=True)
    member_count = serializers.ReadOnlyField()
    current_book = BookSimpleSerializer(read_only=True)
    is_member = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()
    
    class Meta:
        model = BookClub
        fields = [
            'id', 'name', 'description', 'creator', 'is_private',
            'member_count', 'max_members', 'current_book',
            'is_member', 'can_join', 'created_at'
        ]
    
    def get_is_member(self, obj):
        """Check if current user is a member"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Membership.objects.filter(
                user=request.user,
                book_club=obj,
                is_active=True
            ).exists()
        return False
    
    def get_can_join(self, obj):
        """Check if current user can join this club"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Can't join if already a member
        if self.get_is_member(obj):
            return False
        
        # Can't join if at capacity
        if obj.member_count >= obj.max_members:
            return False
        
        # Can't join private clubs without invitation (simplified logic here)
        if obj.is_private:
            return False
        
        return True


# Reading Session Serializers
class ReadingSessionSerializer(serializers.ModelSerializer):
    book = BookSimpleSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all(), source='book', write_only=True)
    is_current = serializers.ReadOnlyField()
    progress_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = ReadingSession
        fields = [
            'id', 'book', 'book_id', 'start_date', 'end_date', 'status',
            'notes', 'meeting_date', 'meeting_location', 'meeting_notes',
            'is_current', 'progress_percentage'
        ]


# Review Serializers
class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    book = BookSimpleSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'book', 'rating', 'title', 'content',
            'is_spoiler', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user']


class ReviewCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating reviews"""
    
    class Meta:
        model = Review
        fields = ['book', 'rating', 'title', 'content', 'is_spoiler', 'reading_session']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# Reading Progress Serializers
class ReadingProgressSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    book = BookSimpleSerializer(read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = ReadingProgress
        fields = [
            'id', 'user', 'book', 'current_page', 'is_finished',
            'started_at', 'finished_at', 'notes', 'progress_percentage', 'updated_at'
        ]
        read_only_fields = ['user']


class ReadingProgressUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating reading progress"""
    
    class Meta:
        model = ReadingProgress
        fields = ['current_page', 'is_finished', 'notes']


# Discussion Serializers
class DiscussionReplySerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = DiscussionReply
        fields = [
            'id', 'author', 'content', 'parent_reply', 'is_spoiler',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['author']


class DiscussionSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    book = BookSimpleSerializer(read_only=True)
    replies = DiscussionReplySerializer(many=True, read_only=True)
    reply_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Discussion
        fields = [
            'id', 'author', 'book', 'title', 'content', 'discussion_type',
            'chapter_number', 'is_pinned', 'is_spoiler', 'replies', 'reply_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['author']


class DiscussionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating discussions"""
    
    class Meta:
        model = Discussion
        fields = [
            'book', 'reading_session', 'title', 'content', 'discussion_type',
            'chapter_number', 'is_spoiler'
        ]
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        validated_data['book_club_id'] = self.context['book_club_id']
        return super().create(validated_data)


# Book Recommendation Serializers
class BookRecommendationSerializer(serializers.ModelSerializer):
    book = BookSimpleSerializer(read_only=True)
    recommended_by = UserSerializer(read_only=True)
    total_votes = serializers.ReadOnlyField()
    approval_ratio = serializers.ReadOnlyField()
    
    class Meta:
        model = BookRecommendation
        fields = [
            'id', 'book', 'recommended_by', 'reason', 'status',
            'votes_for', 'votes_against', 'total_votes', 'approval_ratio',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['recommended_by', 'votes_for', 'votes_against']


class BookRecommendationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating book recommendations"""
    
    class Meta:
        model = BookRecommendation
        fields = ['book', 'reason']
    
    def create(self, validated_data):
        validated_data['recommended_by'] = self.context['request'].user
        validated_data['book_club_id'] = self.context['book_club_id']
        return super().create(validated_data)


# Book List Serializers
class BookListSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    books = BookSimpleSerializer(many=True, read_only=True)
    book_count = serializers.ReadOnlyField()
    
    class Meta:
        model = BookList
        fields = [
            'id', 'name', 'description', 'owner', 'books', 'is_public',
            'book_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['owner']


class BookListCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating book lists"""
    books = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all(), many=True, required=False)
    
    class Meta:
        model = BookList
        fields = ['name', 'description', 'books', 'is_public']
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


# Analytics Serializers - Read-only for analytics data
class BookClubBooksSerializer(serializers.Serializer):
    """Serializer for book club books analytics data"""
    book_club_id = serializers.IntegerField(read_only=True)
    book_club_name = serializers.CharField(read_only=True)
    book_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        read_only_fields = ['book_club_id', 'book_club_name', 'book_count']


class BookSummariesSerializer(serializers.Serializer):
    """Serializer for book summaries analytics data"""
    book_id = serializers.IntegerField(read_only=True)
    book_title = serializers.CharField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        read_only_fields = ['book_id', 'book_title', 'review_count']


class ActiveClubsSerializer(serializers.Serializer):
    """Serializer for active clubs analytics data"""
    active_club_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        read_only_fields = ['active_club_count']


# Follow Serializers
class UserProfileSerializer(serializers.ModelSerializer):
    """Enhanced user serializer with follow stats"""
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    is_followed_by = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'date_joined',
            'followers_count', 'following_count', 'is_following', 'is_followed_by'
        ]
        read_only_fields = [
            'id', 'username', 'email', 'date_joined', 'followers_count', 
            'following_count', 'is_following', 'is_followed_by'
        ]
    
    def get_followers_count(self, obj):
        """Get number of followers"""
        return obj.followers.count()
    
    def get_following_count(self, obj):
        """Get number of users this user is following"""
        return obj.following.count()
    
    def get_is_following(self, obj):
        """Check if current user is following this user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user != obj:
            return Follow.objects.filter(
                follower=request.user, 
                following=obj
            ).exists()
        return False
    
    def get_is_followed_by(self, obj):
        """Check if this user is following the current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user != obj:
            return Follow.objects.filter(
                follower=obj, 
                following=request.user
            ).exists()
        return False


class FollowSerializer(serializers.ModelSerializer):
    """Serializer for Follow model"""
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']
        read_only_fields = ['id', 'follower', 'following', 'created_at']


class FollowActionSerializer(serializers.Serializer):
    """Serializer for follow/unfollow actions"""
    user_id = serializers.IntegerField()
    
    def validate_user_id(self, value):
        """Validate that the user exists and is not the current user"""
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        
        request = self.context.get('request')
        if request and request.user.id == value:
            raise serializers.ValidationError("You cannot follow yourself.")
        
        return value


class FollowListSerializer(serializers.ModelSerializer):
    """Serializer for listing followers/following"""
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
