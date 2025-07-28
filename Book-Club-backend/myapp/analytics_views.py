from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from django.db.models import Count, Q
from .models import BookClub, Book, Review, Discussion, ReadingSession
from .serializers import (
    BookClubBooksSerializer, 
    BookSummariesSerializer, 
    ActiveClubsSerializer
)


class BooksPerClubView(APIView):
    """
    Admin-only analytics view that returns book clubs with count of completed books.
    GET /api/admin/analytics/books/
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Annotate book clubs with count of completed reading sessions
        book_clubs_data = BookClub.objects.annotate(
            book_count=Count(
                'reading_sessions',
                filter=Q(reading_sessions__status='completed')
            )
        ).values(
            'id',
            'name', 
            'book_count'
        ).order_by('-book_count')
        
        # Transform data to match serializer fields
        serialized_data = []
        for club in book_clubs_data:
            serialized_data.append({
                'book_club_id': club['id'],
                'book_club_name': club['name'],
                'book_count': club['book_count']
            })
        
        serializer = BookClubBooksSerializer(serialized_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SummariesPerBookView(APIView):
    """
    Admin-only analytics view that returns books with count of associated reviews.
    GET /api/admin/analytics/summaries/
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Annotate books with count of reviews
        books_data = Book.objects.annotate(
            review_count=Count('reviews')
        ).values(
            'id',
            'title',
            'review_count'
        ).filter(
            review_count__gt=0  # Only include books with at least one review
        ).order_by('-review_count')
        
        # Transform data to match serializer fields
        serialized_data = []
        for book in books_data:
            serialized_data.append({
                'book_id': book['id'],
                'book_title': book['title'],
                'review_count': book['review_count']
            })
        
        serializer = BookSummariesSerializer(serialized_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ActiveClubsView(APIView):
    """
    Admin-only analytics view that returns count of active book clubs.
    Active clubs are defined as having at least one Review or Discussion.
    GET /api/admin/analytics/active-clubs/
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Count book clubs that have either reviews or discussions
        active_clubs_count = BookClub.objects.filter(
            Q(reading_sessions__reviews__isnull=False) | 
            Q(discussions__isnull=False)
        ).distinct().count()
        
        # Prepare data for serializer
        data = {
            'active_club_count': active_clubs_count
        }
        
        serializer = ActiveClubsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
