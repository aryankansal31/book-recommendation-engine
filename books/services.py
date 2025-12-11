import requests
from django.conf import settings
from .models import Book

class GoogleBooksService:
    @staticmethod
    def search_books(query, max_results=20):
        """Search books using Google Books API"""
        url = f"{settings.GOOGLE_BOOKS_BASE_URL}"
        params = {
            'q': query,
            'maxResults': max_results,
            'key': settings.GOOGLE_BOOKS_API_KEY
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            books = []
            for item in data.get('items', []):
                volume_info = item.get('volumeInfo', {})
                book_data = {
                    'google_book_id': item.get('id'),
                    'title': volume_info.get('title', ''),
                    'authors': volume_info.get('authors', []),
                    'description': volume_info.get('description', ''),
                    'page_count': volume_info.get('pageCount'),
                    'categories': volume_info.get('categories', []),
                    'image_links': volume_info.get('imageLinks', {}),
                    'published_date': volume_info.get('publishedDate', ''),
                    'average_rating': volume_info.get('averageRating')
                }
                books.append(book_data)
            
            return books
        except requests.RequestException as e:
            return []

    @staticmethod
    def get_book_details(google_book_id):
        """Get detailed book information by Google Books ID"""
        url = f"{settings.GOOGLE_BOOKS_BASE_URL}/{google_book_id}"
        params = {'key': settings.GOOGLE_BOOKS_API_KEY}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            volume_info = data.get('volumeInfo', {})
            return {
                'google_book_id': data.get('id'),
                'title': volume_info.get('title', ''),
                'authors': volume_info.get('authors', []),
                'description': volume_info.get('description', ''),
                'page_count': volume_info.get('pageCount'),
                'categories': volume_info.get('categories', []),
                'image_links': volume_info.get('imageLinks', {}),
                'published_date': volume_info.get('publishedDate', ''),
                'average_rating': volume_info.get('averageRating')
            }
        except requests.RequestException:
            return None

    @staticmethod
    def create_or_update_book(google_book_data):
        """Create or update a Book instance from Google Books data"""
        book, created = Book.objects.get_or_create(
            google_book_id=google_book_data['google_book_id'],
            defaults={
                'title': google_book_data['title'],
                'author': ', '.join(google_book_data.get('authors', [])),
                'genre': ', '.join(google_book_data.get('categories', [])[:2]),
                'pages': google_book_data.get('page_count'),
                'cover_url': google_book_data.get('image_links', {}).get('thumbnail', ''),
                'description': google_book_data.get('description', ''),
                'published_date': google_book_data.get('published_date', ''),
                'average_rating': google_book_data.get('average_rating')
            }
        )
        return book