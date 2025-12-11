from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, UserBookViewSet, ReadingGoalViewSet

router = DefaultRouter()
router.register(r'books', BookViewSet)
router.register(r'user-books', UserBookViewSet, basename='userbook')
router.register(r'reading-goals', ReadingGoalViewSet, basename='readinggoal')

urlpatterns = [
    path('api/', include(router.urls)),
]