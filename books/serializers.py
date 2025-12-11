from rest_framework import serializers
from .models import Book, UserBook, ReadingGoal

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class UserBookSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    book_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = UserBook
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

class UserBookCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBook
        fields = ['book', 'status', 'rating', 'start_date', 'finish_date', 'notes', 'progress_percentage']

class ReadingGoalSerializer(serializers.ModelSerializer):
    books_completed = serializers.SerializerMethodField()
    pages_read = serializers.SerializerMethodField()
    
    class Meta:
        model = ReadingGoal
        fields = '__all__'
        read_only_fields = ('user', 'created_at')
    
    def get_books_completed(self, obj):
        return UserBook.objects.filter(
            user=obj.user, 
            status='completed',
            finish_date__year=obj.year
        ).count()
    
    def get_pages_read(self, obj):
        completed_books = UserBook.objects.filter(
            user=obj.user,
            status='completed',
            finish_date__year=obj.year,
            book__pages__isnull=False
        )
        return sum(ub.book.pages for ub in completed_books)

class GoogleBookSerializer(serializers.Serializer):
    google_book_id = serializers.CharField()
    title = serializers.CharField()
    authors = serializers.ListField(child=serializers.CharField())
    description = serializers.CharField(required=False)
    page_count = serializers.IntegerField(required=False)
    categories = serializers.ListField(child=serializers.CharField(), required=False)
    image_links = serializers.DictField(required=False)
    published_date = serializers.CharField(required=False)
    average_rating = serializers.FloatField(required=False)