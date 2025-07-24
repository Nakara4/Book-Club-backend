# Book Club Django Models

This document provides an overview of the comprehensive Django models created for a book club application.

## Models Overview

### Core Models

#### 1. **Author**
- Stores book author information
- Fields: `first_name`, `last_name`, `bio`, `birth_date`, `death_date`, `website`
- Properties: `full_name`
- Meta: Ordered by last name, unique together constraint

#### 2. **Genre**
- Categorizes books by genre
- Fields: `name`, `description`
- Meta: Ordered by name, unique name constraint

#### 3. **Book**
- Central model for book information
- Fields: `title`, `subtitle`, `isbn`, `description`, `publication_date`, `publisher`, `page_count`, `language`, `cover_image`
- Relationships: Many-to-many with `Author` and `Genre`
- Properties: `author_names`, `average_rating`

### Book Club Models

#### 4. **BookClub**
- Represents a book club
- Fields: `name`, `description`, `is_private`, `max_members`, `location`, `meeting_frequency`
- Relationships: ForeignKey to `User` (creator), Many-to-many with `User` (members through Membership)
- Properties: `member_count`, `current_book`

#### 5. **Membership**
- Through model for BookClub-User relationship
- Fields: `role` (member/moderator/admin), `joined_at`, `is_active`
- Relationships: ForeignKey to `User` and `BookClub`

#### 6. **ReadingSession**
- Tracks books being read by a book club
- Fields: `start_date`, `end_date`, `status`, `notes`, `meeting_date`, `meeting_location`, `meeting_notes`
- Relationships: ForeignKey to `BookClub` and `Book`
- Properties: `is_current`, `progress_percentage`

### User Interaction Models

#### 7. **Review**
- Book reviews by users
- Fields: `rating` (1-5), `title`, `content`, `is_spoiler`
- Relationships: ForeignKey to `User`, `Book`, and optionally `ReadingSession`
- Meta: Unique constraint (user, book)

#### 8. **ReadingProgress**
- Tracks individual user's reading progress
- Fields: `current_page`, `is_finished`, `started_at`, `finished_at`, `notes`
- Relationships: ForeignKey to `User`, `Book`, and optionally `ReadingSession`
- Properties: `progress_percentage`
- Custom save method for auto-setting timestamps

#### 9. **Discussion**
- Book club discussions
- Fields: `title`, `content`, `discussion_type`, `chapter_number`, `is_pinned`, `is_spoiler`
- Relationships: ForeignKey to `BookClub`, `User` (author), optionally `Book` and `ReadingSession`
- Properties: `reply_count`

#### 10. **DiscussionReply**
- Replies to discussions
- Fields: `content`, `is_spoiler`
- Relationships: ForeignKey to `Discussion`, `User` (author), and optionally `parent_reply` (self-referencing)

### Recommendation System

#### 11. **BookRecommendation**
- Book recommendations within clubs
- Fields: `reason`, `status`, `votes_for`, `votes_against`
- Relationships: ForeignKey to `BookClub`, `Book`, and `User` (recommended_by)
- Properties: `total_votes`, `approval_ratio`

#### 12. **BookList**
- User-created book lists (e.g., "Want to Read", "Favorites")
- Fields: `name`, `description`, `is_public`
- Relationships: ForeignKey to `User` (owner), Many-to-many with `Book`
- Properties: `book_count`

## Key Features

### Model Relationships
- **Many-to-Many**: Book ↔ Author, Book ↔ Genre, BookClub ↔ User (through Membership), BookList ↔ Book
- **One-to-Many**: User → Reviews, User → ReadingProgress, BookClub → ReadingSession
- **Self-referencing**: DiscussionReply can reference parent replies

### Built-in Properties
- Calculated fields like `average_rating`, `progress_percentage`, `member_count`
- Dynamic status tracking (e.g., `is_current` for reading sessions)

### Validation & Constraints
- Rating validation (1-5 stars)
- Unique constraints to prevent duplicates
- Choice fields for status and role management

### Timestamps
- All models include `created_at` and `updated_at` timestamps where appropriate
- Custom save methods for automatic timestamp management

## Admin Interface

The models are registered in Django admin with:
- Custom list displays showing relevant fields
- Search functionality across key fields
- Filtering options for dates, status, and categories
- Inline editing for related models (e.g., Membership in BookClub)
- Read-only computed fields

## Serializers

Comprehensive DRF serializers are provided:
- **List serializers**: Simplified data for listing views
- **Detail serializers**: Complete data for individual item views
- **Create/Update serializers**: Optimized for data modification
- **Nested serializers**: Related model data included appropriately

## Usage Examples

### Creating a Book Club
```python
club = BookClub.objects.create(
    name="Mystery Lovers",
    description="A club for mystery novel enthusiasts",
    creator=user,
    max_members=25
)
```

### Adding a Reading Session
```python
session = ReadingSession.objects.create(
    book_club=club,
    book=book,
    start_date=date.today(),
    end_date=date.today() + timedelta(days=30),
    status='current'
)
```

### Tracking Reading Progress
```python
progress = ReadingProgress.objects.create(
    user=user,
    book=book,
    reading_session=session,
    current_page=150
)
```

This model structure provides a solid foundation for a full-featured book club application with user management, book tracking, discussions, and progress monitoring.
