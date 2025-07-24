from django.contrib import admin
from .models import (
    Author, Genre, Book, BookClub, Membership, ReadingSession,
    Review, ReadingProgress, Discussion, DiscussionReply,
    BookRecommendation, BookList
)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'birth_date', 'created_at']
    list_filter = ['birth_date', 'created_at']
    search_fields = ['first_name', 'last_name']
    ordering = ['last_name', 'first_name']


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author_names', 'publication_date', 'page_count', 'average_rating']
    list_filter = ['publication_date', 'language', 'genres', 'created_at']
    search_fields = ['title', 'authors__first_name', 'authors__last_name', 'isbn']
    filter_horizontal = ['authors', 'genres']
    readonly_fields = ['average_rating', 'author_names']
    ordering = ['title']


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    readonly_fields = ['joined_at']


@admin.register(BookClub)
class BookClubAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'member_count', 'is_private', 'created_at']
    list_filter = ['is_private', 'meeting_frequency', 'created_at']
    search_fields = ['name', 'description', 'creator__username']
    readonly_fields = ['member_count', 'current_book']
    inlines = [MembershipInline]
    ordering = ['name']


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'book_club', 'role', 'joined_at', 'is_active']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['user__username', 'book_club__name']
    ordering = ['-joined_at']


@admin.register(ReadingSession)
class ReadingSessionAdmin(admin.ModelAdmin):
    list_display = ['book_club', 'book', 'status', 'start_date', 'end_date', 'is_current']
    list_filter = ['status', 'start_date', 'end_date']
    search_fields = ['book_club__name', 'book__title']
    readonly_fields = ['is_current', 'progress_percentage']
    ordering = ['-start_date']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'rating', 'title', 'is_spoiler', 'created_at']
    list_filter = ['rating', 'is_spoiler', 'created_at']
    search_fields = ['user__username', 'book__title', 'title']
    ordering = ['-created_at']


@admin.register(ReadingProgress)
class ReadingProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'current_page', 'progress_percentage', 'is_finished', 'updated_at']
    list_filter = ['is_finished', 'started_at', 'finished_at']
    search_fields = ['user__username', 'book__title']
    readonly_fields = ['progress_percentage']
    ordering = ['-updated_at']


@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ['title', 'book_club', 'author', 'discussion_type', 'is_pinned', 'reply_count', 'created_at']
    list_filter = ['discussion_type', 'is_pinned', 'is_spoiler', 'created_at']
    search_fields = ['title', 'book_club__name', 'author__username']
    readonly_fields = ['reply_count']
    ordering = ['-is_pinned', '-created_at']


@admin.register(DiscussionReply)
class DiscussionReplyAdmin(admin.ModelAdmin):
    list_display = ['discussion', 'author', 'parent_reply', 'is_spoiler', 'created_at']
    list_filter = ['is_spoiler', 'created_at']
    search_fields = ['discussion__title', 'author__username']
    ordering = ['created_at']


@admin.register(BookRecommendation)
class BookRecommendationAdmin(admin.ModelAdmin):
    list_display = ['book', 'book_club', 'recommended_by', 'status', 'votes_for', 'votes_against', 'approval_ratio']
    list_filter = ['status', 'created_at']
    search_fields = ['book__title', 'book_club__name', 'recommended_by__username']
    readonly_fields = ['total_votes', 'approval_ratio']
    ordering = ['-created_at']


@admin.register(BookList)
class BookListAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'book_count', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['name', 'owner__username']
    filter_horizontal = ['books']
    readonly_fields = ['book_count']
    ordering = ['name']
