from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'book-clubs', views.BookClubViewSet, basename='bookclub')

urlpatterns = [
    path('', views.home, name='home'),
    
    # Authentication endpoints
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/profile/', views.profile, name='profile'),
    
    # Book Club endpoints - Include router URLs
    path('api/', include(router.urls)),
    
    # Additional Book Club endpoints (must come after router to avoid conflicts)
    path('api/book-clubs/search/', views.BookClubSearchView.as_view(), name='bookclub-search'),
    path('api/book-clubs/discover/', views.book_club_discovery, name='bookclub-discovery'),
    path('api/my-memberships/', views.my_club_memberships, name='my-memberships'),
]
