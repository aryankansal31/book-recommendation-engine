from django.contrib import admin
from .models import Book, UserBook, ReadingGoal

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'genre', 'pages', 'created_at']
    search_fields = ['title', 'author', 'google_book_id']
    list_filter = ['genre', 'created_at']

@admin.register(UserBook)
class UserBookAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'status', 'rating', 'progress_percentage']
    list_filter = ['status', 'rating', 'created_at']
    search_fields = ['user__username', 'book__title']

@admin.register(ReadingGoal)
class ReadingGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'year', 'target_books', 'target_pages']
    list_filter = ['year']
    search_fields = ['user__username']
