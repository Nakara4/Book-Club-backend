# Book Club Models Specification

## Author

- **Fields**:
  - `first_name`: CharField, max_length=100
  - `last_name`: CharField, max_length=100
  - `bio`: TextField, optional
  - `birth_date`: DateField, optional
  - `death_date`: DateField, optional
  - `website`: URLField, optional
  - `created_at`: DateTimeField, auto_now_add=True
  - `updated_at`: DateTimeField, auto_now=True

- **Constraints**:
  - Unique combination of `first_name` and `last_name`

## Genre

- **Fields**:
  - `name`: CharField, max_length=100, unique
  - `description`: TextField, optional
  - `created_at`: DateTimeField, auto_now_add=True

## Book

- **Fields**:
  - `title`: CharField, max_length=200
  - `subtitle`: CharField, optional
  - `authors`: ManyToMany with Author
  - `isbn`: CharField, unique, optional
  - `isbn_10`: CharField, optional
  - `description`: TextField, optional
  - `publication_date`: DateField, optional
  - `publisher`: CharField, optional
  - `page_count`: PositiveIntegerField, optional
  - `language`: CharField, default='English'
  - `cover_image`: ImageField, optional
  - `goodreads_url`: URLField, optional
  - `amazon_url`: URLField, optional
  - `created_at`: DateTimeField, auto_now_add=True
  - `updated_at`: DateTimeField, auto_now=True

- **Relationships**:
  - `ManyToMany` with Genre
  - Related through Review, Recommendation, ReadingSession

## BookClub

- **Fields**:
  - `name`: CharField, max_length=200
  - `description`: TextField
  - `creator`: ForeignKey to User
  - `members`: ManyToMany with User through Membership
  - `image`: ImageField, optional
  - `category`: CharField, optional
  - `is_private`: BooleanField, default=False
  - `max_members`: PositiveIntegerField, default=50
  - `location`: CharField, optional
  - `meeting_frequency`: CharField, optional
  - `created_at`: DateTimeField, auto_now_add=True
  - `updated_at`: DateTimeField, auto_now=True

- **Relationships**:
  - Related through ReadingSession, Discussion, Recommendation

## Membership

- **Fields**:
  - `user`: ForeignKey to User
  - `book_club`: ForeignKey to BookClub
  - `role`: CharField
  - `joined_at`: DateTimeField, auto_now_add=True
  - `is_active`: BooleanField, default=True

- **Constraints**:
  - Unique combination of `user` and `book_club`

## ReadingSession

- **Fields**:
  - `book_club`: ForeignKey to BookClub, related_name='reading_sessions'
  - `book`: ForeignKey to Book, related_name='reading_sessions'
  - `start_date`: DateField
  - `end_date`: DateField
  - `status`: CharField
  - `notes`: TextField, optional
  - `meeting_date`: DateTimeField, optional
  - `meeting_location`: CharField, optional
  - `meeting_notes`: TextField, optional
  - `created_at`: DateTimeField, auto_now_add=True
  - `updated_at`: DateTimeField, auto_now=True

- **Constraints**:
  - Unique combination of `book_club`, `book`, and `start_date`

## Review

- **Fields**:
  - `user`: ForeignKey to User, related_name='reviews'
  - `book`: ForeignKey to Book, related_name='reviews'
  - `rating`: IntegerField
  - `title`: CharField, optional
  - `content`: TextField
  - `is_spoiler`: BooleanField, default=False
  - `reading_session`: ForeignKey to ReadingSession, optional
  - `created_at`: DateTimeField, auto_now_add=True
  - `updated_at`: DateTimeField, auto_now=True

- **Constraints**:
  - Unique combination of `user` and `book`

## ReadingProgress

- **Fields**:
  - `user`: ForeignKey to User, related_name='reading_progress'
  - `book`: ForeignKey to Book, related_name='reading_progress'
  - `reading_session`: ForeignKey to ReadingSession, optional
  - `current_page`: PositiveIntegerField, default=0
  - `is_finished`: BooleanField, default=False
  - `started_at`: DateTimeField, optional
  - `finished_at`: DateTimeField, optional
  - `notes`: TextField, optional
  - `updated_at`: DateTimeField, auto_now=True

- **Constraints**:
  - Unique combination of `user`, `book`, and `reading_session`

## Discussion

- **Fields**:
  - `book_club`: ForeignKey to BookClub, related_name='discussions'
  - `book`: ForeignKey to Book, optional
  - `reading_session`: ForeignKey to ReadingSession, optional
  - `author`: ForeignKey to User
  - `title`: CharField, max_length=200
  - `content`: TextField
  - `discussion_type`: CharField
  - `chapter_number`: PositiveIntegerField, optional
  - `is_pinned`: BooleanField, default=False
  - `is_spoiler`: BooleanField, default=False
  - `created_at`: DateTimeField, auto_now_add=True
  - `updated_at`: DateTimeField, auto_now=True

## DiscussionReply

- **Fields**:
  - `discussion`: ForeignKey to Discussion, related_name='replies'
  - `author`: ForeignKey to User
  - `content`: TextField
  - `parent_reply`: ForeignKey to self, optional
  - `is_spoiler`: BooleanField, default=False
  - `created_at`: DateTimeField, auto_now_add=True
  - `updated_at`: DateTimeField, auto_now=True

## BookRecommendation

- **Fields**:
  - `book_club`: ForeignKey to BookClub, related_name='recommendations'
  - `book`: ForeignKey to Book
  - `recommended_by`: ForeignKey to User
  - `reason`: TextField
  - `status`: CharField
  - `votes_for`: PositiveIntegerField, default=0
  - `votes_against`: PositiveIntegerField, default=0
  - `created_at`: DateTimeField, auto_now_add=True
  - `updated_at`: DateTimeField, auto_now=True

- **Constraints**:
  - Unique combination of `book_club` and `book`

## BookList

- **Fields**:
  - `name`: CharField, max_length=200
  - `description`: TextField, optional
  - `owner`: ForeignKey to User
  - `books`: ManyToMany with Book
  - `is_public`: BooleanField, default=True
  - `created_at`: DateTimeField, auto_now_add=True
  - `updated_at`: DateTimeField, auto_now=True

- **Constraints**:
  - Unique combination of `owner` and `name`

## Follow

- **Fields**:
  - `follower`: ForeignKey to User
  - `following`: ForeignKey to User
  - `created_at`: DateTimeField, auto_now_add=True

- **Constraints**:
  - Unique combination of `follower` and `following`

# Needs Change Checklist

- Ensure `Book` has consistent `cover_image` field.
- Verify `BookClub` images are correctly linked.
- Confirm unique constraints are enforced correctly.
- Ensure all image fields are populated where necessary.

