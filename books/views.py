from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import datetime
from .models import Book, UserBook, ReadingGoal
from .serializers import (
    BookSerializer, UserBookSerializer, UserBookCreateSerializer,
    ReadingGoalSerializer, GoogleBookSerializer
)
from .services import GoogleBooksService

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    
    @action(detail=False, methods=['get'])
    def search_google_books(self, request):
        """Search books using Google Books API"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Query parameter q is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        books = GoogleBooksService.search_books(query)
        serializer = GoogleBookSerializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_from_google(self, request):
        """Add a book from Google Books to local database"""
        google_book_id = request.data.get('google_book_id')
        if not google_book_id:
            return Response({'error': 'google_book_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Get book details from Google Books API
        book_data = GoogleBooksService.get_book_details(google_book_id)
        if not book_data:
            return Response({'error': 'Book not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # Create or get existing book
        book = GoogleBooksService.create_or_update_book(book_data)
        serializer = BookSerializer(book)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UserBookViewSet(viewsets.ModelViewSet):
    serializer_class = UserBookSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserBook.objects.filter(user=self.request.user).select_related('book')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserBookCreateSerializer
        return UserBookSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def currently_reading(self, request):
        """Get books currently being read"""
        books = self.get_queryset().filter(status='reading')
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get completed books"""
        books = self.get_queryset().filter(status='completed')
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def want_to_read(self, request):
        """Get books in want to read list"""
        books = self.get_queryset().filter(status='want_to_read')
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get reading statistics"""
        year = request.query_params.get('year', timezone.now().year)
        
        # Books completed this year
        completed_books = self.get_queryset().filter(
            status='completed',
            finish_date__year=year
        )
        
        # Genre distribution
        genre_stats = completed_books.values('book__genre').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Monthly reading stats
        monthly_stats = []
        for month in range(1, 13):
            count = completed_books.filter(finish_date__month=month).count()
            monthly_stats.append({
                'month': datetime(int(year), month, 1).strftime('%b'),
                'books_read': count
            })
        
        # Total pages read
        total_pages = sum(
            ub.book.pages for ub in completed_books 
            if ub.book.pages
        )
        
        # Average rating
        avg_rating = completed_books.filter(
            rating__isnull=False
        ).aggregate(avg_rating=Avg('rating'))['avg_rating']
        
        return Response({
            'year': year,
            'total_books_completed': completed_books.count(),
            'total_pages_read': total_pages,
            'average_rating': round(avg_rating, 2) if avg_rating else None,
            'genre_distribution': genre_stats,
            'monthly_reading': monthly_stats,
            'currently_reading_count': self.get_queryset().filter(status='reading').count(),
            'want_to_read_count': self.get_queryset().filter(status='want_to_read').count()
        })
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """Get book recommendations based on user's reading history"""
        # Get user's favorite genres
        favorite_genres = self.get_queryset().filter(
            status='completed',
            rating__gte=4
        ).values('book__genre').annotate(
            count=Count('id')
        ).order_by('-count')[:3]
        
        if not favorite_genres:
            return Response({'recommendations': []})
        
        # Search for books in favorite genres
        recommendations = []
        for genre_data in favorite_genres:
            genre = genre_data['book__genre']
            if genre:
                books = GoogleBooksService.search_books(f"subject:{genre}", max_results=5)
                recommendations.extend(books[:2])  # Limit to 2 per genre
        
        return Response({'recommendations': recommendations[:6]})

class ReadingGoalViewSet(viewsets.ModelViewSet):
    serializer_class = ReadingGoalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ReadingGoal.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def current_year(self, request):
        """Get current year's reading goal"""
        current_year = timezone.now().year
        try:
            goal = self.get_queryset().get(year=current_year)
            serializer = self.get_serializer(goal)
            return Response(serializer.data)
        except ReadingGoal.DoesNotExist:
            return Response({'error': 'No goal set for current year'}, 
                          status=status.HTTP_404_NOT_FOUND)