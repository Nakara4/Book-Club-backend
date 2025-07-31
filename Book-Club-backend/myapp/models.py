from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


class UserProfile(models.Model):
    """User profile model to extend User with additional fields"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True, null=True, help_text="URL for external profile image")
    image_updated_at = models.DateTimeField(blank=True, null=True, help_text="When the profile image was last updated")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__username']
    
    def __str__(self):
        return f"{self.user.username}'s Profile"


class BookManager(models.Manager):
    """Custom manager for Book model with external ID support"""
    
    def get_or_create_by_external_id(self, external_id, source, defaults=None):
        """
        Get or create a book by external ID and source.
        Returns tuple (book, created)
        """
        if defaults is None:
            defaults = {}
        
        try:
            book = self.get(external_id=external_id, source=source)
            return book, False
        except self.model.DoesNotExist:
            book = self.create(external_id=external_id, source=source, **defaults)
            return book, True


class Author(models.Model):
    """Model to store book authors"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    death_date = models.DateField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        unique_together = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Genre(models.Model):
    """Model to categorize books by genre"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    """Model to store book information"""
    # Source choices for external IDs
    SOURCE_CHOICES = [
        ('openlibrary', 'Open Library'),
        ('googlebooks', 'Google Books'),
        ('goodreads', 'Goodreads'),
        ('manual', 'Manual Entry'),
    ]
    
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True, null=True)
    authors = models.ManyToManyField(Author, related_name='books')
    isbn = models.CharField(max_length=13, unique=True, blank=True, null=True)
    isbn_10 = models.CharField(max_length=10, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    publication_date = models.DateField(blank=True, null=True)
    publisher = models.CharField(max_length=200, blank=True, null=True)
    page_count = models.PositiveIntegerField(blank=True, null=True)
    language = models.CharField(max_length=50, default='English')
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True, null=True, help_text="URL for external book cover image")
    image_updated_at = models.DateTimeField(blank=True, null=True, help_text="When the book cover image was last updated")
    genres = models.ManyToManyField(Genre, related_name='books', blank=True)
    goodreads_url = models.URLField(blank=True, null=True)
    amazon_url = models.URLField(blank=True, null=True)
    # External ID fields for idempotent seeding
    external_id = models.CharField(max_length=100, blank=True, null=True, help_text="External API ID (Open Library, Google Books, etc.)")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual', help_text="Source of the book data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Use custom manager
    objects = BookManager()

    class Meta:
        ordering = ['title']
        constraints = [
            models.UniqueConstraint(
                fields=['external_id', 'source'],
                condition=models.Q(external_id__isnull=False),
                name='unique_external_id_source'
            )
        ]

    def __str__(self):
        return self.title

    @property
    def author_names(self):
        return ", ".join([author.full_name for author in self.authors.all()])

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum([review.rating for review in reviews]) / len(reviews)
        return None


class BookClubManager(models.Manager):
    """Custom manager for BookClub model"""
    
    def get_or_create_by_external_id(self, external_id, source, defaults=None):
        """
        Get or create a book club by external ID and source.
        Returns tuple (book_club, created)
        """
        if defaults is None:
            defaults = {}
        
        try:
            book_club = self.get(external_id=external_id, source=source)
            return book_club, False
        except self.model.DoesNotExist:
            book_club = self.create(external_id=external_id, source=source, **defaults)
            return book_club, True


class BookClub(models.Model):
    """Model to represent a book club"""
    # Source choices for external IDs (if importing from other platforms)
    SOURCE_CHOICES = [
        ('goodreads', 'Goodreads'),
        ('facebook', 'Facebook Groups'),
        ('meetup', 'Meetup'),
        ('manual', 'Manual Entry'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_clubs')
    members = models.ManyToManyField(User, related_name='book_clubs', through='Membership')
    image = models.ImageField(upload_to='bookclub_images/', blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True, null=True, help_text="URL for external book club image")
    image_updated_at = models.DateTimeField(blank=True, null=True, help_text="When the book club image was last updated")
    category = models.CharField(max_length=100, blank=True, null=True)
    is_private = models.BooleanField(default=False)
    max_members = models.PositiveIntegerField(default=50)
    location = models.CharField(max_length=200, blank=True, null=True)
    meeting_frequency = models.CharField(max_length=100, blank=True, null=True)  # e.g., "Monthly", "Bi-weekly"
    # External ID fields for idempotent seeding
    external_id = models.CharField(max_length=100, blank=True, null=True, help_text="External platform ID")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual', help_text="Source of the book club data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Use custom manager
    objects = BookClubManager()

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['external_id', 'source'],
                condition=models.Q(external_id__isnull=False),
                name='unique_bookclub_external_id_source'
            )
        ]

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.count()

    @property
    def current_book(self):
        current_reading = self.reading_sessions.filter(
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        ).first()
        return current_reading.book if current_reading else None


class Membership(models.Model):
    """Through model for BookClub-User relationship"""
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book_club = models.ForeignKey(BookClub, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['user', 'book_club']
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} - {self.book_club.name} ({self.role})"


class ReadingSession(models.Model):
    """Model to track books being read by a book club"""
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('current', 'Currently Reading'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    book_club = models.ForeignKey(BookClub, on_delete=models.CASCADE, related_name='reading_sessions')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reading_sessions')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    notes = models.TextField(blank=True, null=True)
    meeting_date = models.DateTimeField(blank=True, null=True)
    meeting_location = models.CharField(max_length=200, blank=True, null=True)
    meeting_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        unique_together = ['book_club', 'book', 'start_date']

    def __str__(self):
        return f"{self.book_club.name} - {self.book.title} ({self.status})"

    @property
    def is_current(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

    @property
    def progress_percentage(self):
        if self.status == 'completed':
            return 100
        elif self.status == 'upcoming':
            return 0
        
        today = timezone.now().date()
        total_days = (self.end_date - self.start_date).days
        elapsed_days = (today - self.start_date).days
        
        if total_days > 0:
            return min(100, max(0, (elapsed_days / total_days) * 100))
        return 0


class Review(models.Model):
    """Model for book reviews by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField()
    is_spoiler = models.BooleanField(default=False)
    reading_session = models.ForeignKey(
        ReadingSession, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='reviews'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'book']

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.rating}/5)"


class ReadingProgress(models.Model):
    """Model to track individual user's reading progress for a book"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_progress')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reading_progress')
    reading_session = models.ForeignKey(
        ReadingSession, 
        on_delete=models.CASCADE, 
        related_name='user_progress',
        blank=True,
        null=True
    )
    current_page = models.PositiveIntegerField(default=0)
    is_finished = models.BooleanField(default=False)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'book', 'reading_session']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.book.title} (Page {self.current_page})"

    @property
    def progress_percentage(self):
        if self.book.page_count and self.book.page_count > 0:
            return min(100, (self.current_page / self.book.page_count) * 100)
        return 0

    def save(self, *args, **kwargs):
        # Auto-set started_at when first page is recorded
        if self.current_page > 0 and not self.started_at:
            self.started_at = timezone.now()
        
        # Auto-set finished_at when book is marked as finished
        if self.is_finished and not self.finished_at:
            self.finished_at = timezone.now()
            if self.book.page_count:
                self.current_page = self.book.page_count
        
        super().save(*args, **kwargs)


class Discussion(models.Model):
    """Model for book club discussions"""
    DISCUSSION_TYPES = [
        ('general', 'General Discussion'),
        ('chapter', 'Chapter Discussion'),
        ('review', 'Book Review Discussion'),
        ('meeting', 'Meeting Discussion'),
    ]
    
    book_club = models.ForeignKey(BookClub, on_delete=models.CASCADE, related_name='discussions')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='discussions', blank=True, null=True)
    reading_session = models.ForeignKey(
        ReadingSession, 
        on_delete=models.CASCADE, 
        related_name='discussions',
        blank=True,
        null=True
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussions')
    title = models.CharField(max_length=200)
    content = models.TextField()
    discussion_type = models.CharField(max_length=20, choices=DISCUSSION_TYPES, default='general')
    chapter_number = models.PositiveIntegerField(blank=True, null=True)
    is_pinned = models.BooleanField(default=False)
    is_spoiler = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"{self.book_club.name} - {self.title}"

    @property
    def reply_count(self):
        return self.replies.count()


class DiscussionReply(models.Model):
    """Model for replies to discussions"""
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_replies')
    content = models.TextField()
    parent_reply = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True, 
        related_name='child_replies'
    )
    is_spoiler = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Reply to {self.discussion.title} by {self.author.username}"


class BookRecommendation(models.Model):
    """Model for book recommendations within a club"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('selected', 'Selected for Reading'),
    ]
    
    book_club = models.ForeignKey(BookClub, on_delete=models.CASCADE, related_name='recommendations')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='recommendations')
    recommended_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    reason = models.TextField(help_text="Why do you recommend this book?")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    votes_for = models.PositiveIntegerField(default=0)
    votes_against = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['book_club', 'book']

    def __str__(self):
        return f"{self.book.title} recommended to {self.book_club.name}"

    @property
    def total_votes(self):
        return self.votes_for + self.votes_against

    @property
    def approval_ratio(self):
        if self.total_votes > 0:
            return self.votes_for / self.total_votes
        return 0


class BookList(models.Model):
    """Model for user-created book lists (e.g., 'Want to Read', 'Favorites')"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_lists')
    books = models.ManyToManyField(Book, related_name='book_lists', blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['owner', 'name']

    def __str__(self):
        return f"{self.owner.username}'s {self.name}"

    @property
    def book_count(self):
        return self.books.count()


class Follow(models.Model):
    """Model for user following system"""
    follower = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='following'
    )
    following = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['follower', 'following']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

    def save(self, *args, **kwargs):
        # Prevent users from following themselves
        if self.follower == self.following:
            raise ValidationError("Users cannot follow themselves")
        super().save(*args, **kwargs)
