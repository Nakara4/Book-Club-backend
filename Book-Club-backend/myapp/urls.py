from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import analytics_views

router = DefaultRouter()
router.register(r'bookclubs', views.BookClubViewSet, basename='bookclub')

urlpatterns = [
    path('', views.home, name='home'),
    
    # Authentication endpoints
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/profile/', views.profile, name='profile'),
    
    # Book Club endpoints - Include router URLs (mounted at root since project URLs already include 'api/')
    path('', include(router.urls)),
    
    # Additional Book Club endpoints (must come after router to avoid conflicts)
    path('book-clubs/search/', views.BookClubSearchView.as_view(), name='bookclub-search'),
    path('book-clubs/discover/', views.book_club_discovery, name='bookclub-discovery'),
    path('my-memberships/', views.my_club_memberships, name='my-memberships'),
    
    # Admin Analytics endpoints
    path('admin/stats/', analytics_views.AdminStatsView.as_view(), name='admin-stats'),
    path('admin/analytics/books/', analytics_views.BooksPerClubView.as_view(), name='analytics-books-per-club'),
    path('admin/analytics/summaries/', analytics_views.SummariesPerBookView.as_view(), name='analytics-summaries-per-book'),
    path('admin/analytics/active-clubs/', analytics_views.ActiveClubsView.as_view(), name='analytics-active-clubs'),
    path('admin/users/', views.AdminUserView.as_view(), name='admin-user-list'),
    path('admin/users/<int:user_id>/', views.AdminUserView.as_view(), name='admin-user-detail'),
]
