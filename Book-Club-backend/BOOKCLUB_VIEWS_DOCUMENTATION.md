# Django Book Club Views Documentation

This document provides comprehensive documentation for the Django views created for book club creation and listing functionality.

## 🏗️ **Architecture Overview**

The book club views are built using Django REST Framework and follow these patterns:
- **ViewSets** for full CRUD operations
- **Generic Views** for specialized endpoints
- **Function-based Views** for simple utilities
- **Proper authentication** and permissions handling
- **Smart filtering** and search capabilities

---

## 📋 **Main ViewSet: BookClubViewSet**

### **Purpose**
A comprehensive ViewSet that handles all book club operations using Django REST Framework's ModelViewSet.

### **Base Configuration**
```python
class BookClubViewSet(ModelViewSet):
    queryset = BookClub.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_private', 'creator']
    search_fields = ['name', 'description', 'location']
    ordering_fields = ['created_at', 'name', 'member_count']
    ordering = ['-created_at']
```

### **Endpoints Provided**

#### **1. List Book Clubs**
- **URL**: `GET /api/book-clubs/`
- **Purpose**: List all book clubs visible to the current user
- **Authentication**: Required
- **Serializer**: `BookClubListSerializer`
- **Features**:
  - Pagination (20 items per page)
  - Search by name, description, location
  - Filter by privacy status and creator
  - Order by creation date, name, or member count

**Query Parameters**:
```
?search=mystery          # Search in name, description, location
?is_private=false        # Filter by privacy status
?creator=1               # Filter by creator ID
?ordering=-created_at    # Order by creation date (newest first)
```

**Response Example**:
```json
{
  "count": 15,
  "next": "http://localhost:8000/api/book-clubs/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Mystery Lovers Club",
      "description": "A club for mystery novel enthusiasts",
      "creator": {
        "id": 1,
        "username": "bookworm",
        "email": "bookworm@example.com"
      },
      "is_private": false,
      "member_count": 8,
      "current_book": {
        "id": 1,
        "title": "Murder on the Orient Express",
        "authors": [...]
      },
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

#### **2. Create Book Club**
- **URL**: `POST /api/book-clubs/`
- **Purpose**: Create a new book club
- **Authentication**: Required
- **Serializer**: `BookClubCreateUpdateSerializer`

**Request Body**:
```json
{
  "name": "Science Fiction Enthusiasts",
  "description": "A club dedicated to exploring sci-fi literature",
  "is_private": false,
  "max_members": 25,
  "location": "Central Library",
  "meeting_frequency": "Bi-weekly"
}
```

**Features**:
- ✅ **Auto-creator assignment**: Creator set to current user
- ✅ **Auto-membership creation**: Creator becomes admin member
- ✅ **Name validation**: Unique names per user
- ✅ **Member limit validation**: Between 2-1000 members

#### **3. Retrieve Book Club Details**
- **URL**: `GET /api/book-clubs/{id}/`
- **Purpose**: Get detailed information about a specific book club
- **Authentication**: Required
- **Serializer**: `BookClubDetailSerializer`

**Response includes**:
- Complete club information
- Full member list with roles
- Current reading book details
- Creation and update timestamps

#### **4. Update Book Club**
- **URL**: `PUT/PATCH /api/book-clubs/{id}/`
- **Purpose**: Update book club information
- **Authentication**: Required (creator only)
- **Serializer**: `BookClubCreateUpdateSerializer`

#### **5. Delete Book Club**
- **URL**: `DELETE /api/book-clubs/{id}/`
- **Purpose**: Delete a book club
- **Authentication**: Required (creator only)
- **Security**: Only creators can delete their clubs

---

## 🎯 **Custom Actions**

### **1. My Clubs**
- **URL**: `GET /api/book-clubs/my-clubs/`
- **Purpose**: Get all clubs for the current user (created + member of)
- **Authentication**: Required

**Response**:
```json
{
  "created_count": 3,
  "member_count": 5,
  "total_count": 8,
  "clubs": [...]
}
```

### **2. Join Club**
- **URL**: `POST /api/book-clubs/{id}/join/`
- **Purpose**: Join a book club
- **Authentication**: Required
- **Validation**:
  - ✅ User not already a member
  - ✅ Club not at capacity
  - ✅ Public club or user has invitation

**Response**:
```json
{
  "message": "Successfully joined Mystery Lovers Club!",
  "membership": {
    "id": 15,
    "user": {...},
    "role": "member",
    "joined_at": "2025-01-15T14:30:00Z"
  }
}
```

### **3. Leave Club**
- **URL**: `POST /api/book-clubs/{id}/leave/`
- **Purpose**: Leave a book club
- **Authentication**: Required
- **Restriction**: Creators cannot leave their own clubs

### **4. Club Statistics**
- **URL**: `GET /api/book-clubs/{id}/stats/`
- **Purpose**: Get detailed statistics for a club
- **Authentication**: Required (members only for private clubs)
- **Serializer**: `BookClubStatsSerializer`

**Response**:
```json
{
  "id": 1,
  "name": "Mystery Lovers Club",
  "member_count": 8,
  "total_books_read": 12,
  "active_discussions": 3,
  "recent_activity": {
    "new_discussions": 2,
    "new_reviews": 7,
    "period": "last_7_days"
  }
}
```

### **5. Invite Users**
- **URL**: `POST /api/book-clubs/{id}/invite/`
- **Purpose**: Invite users to join the club
- **Authentication**: Required (admins/moderators only)
- **Permissions**: Creator or admin/moderator role required

**Request**:
```json
{
  "email": "newmember@example.com",
  "message": "Join our amazing book club!"
}
```

---

## 🔍 **Search and Discovery Views**

### **BookClubSearchView**
- **URL**: `GET /api/book-clubs/search/`
- **Purpose**: Advanced search with user context
- **Authentication**: Optional (anonymous users see public clubs only)
- **Serializer**: `BookClubSearchSerializer`

**Features**:
- Search across name, description, location, creator username
- Filter by privacy status
- User-specific fields (`is_member`, `can_join`)
- Handles anonymous users gracefully

**Query Parameters**:
```
?search=mystery&is_private=false&ordering=name
```

**Response includes user context**:
```json
{
  "results": [
    {
      "id": 1,
      "name": "Mystery Club",
      "is_member": false,
      "can_join": true,
      "member_count": 8,
      "max_members": 25
    }
  ]
}
```

### **Book Club Discovery**
- **URL**: `GET /api/book-clubs/discover/`
- **Purpose**: Discover featured, popular, and recent clubs
- **Authentication**: None required
- **Function**: `book_club_discovery`

**Response**:
```json
{
  "featured": [...],     // Most members
  "recent": [...],       // Newest clubs
  "popular": [...],      // Most discussions
  "total_public_clubs": 45
}
```

---

## 👥 **Additional Utility Views**

### **My Memberships**
- **URL**: `GET /api/my-memberships/`
- **Purpose**: Get all memberships with role information
- **Authentication**: Required
- **Function**: `my_club_memberships`

**Response**:
```json
{
  "count": 5,
  "memberships": [
    {
      "id": 1,
      "user": {...},
      "book_club": {...},
      "role": "admin",
      "joined_at": "2025-01-10T12:00:00Z",
      "is_active": true
    }
  ]
}
```

---

## 🔒 **Security and Permissions**

### **Privacy Handling**
```python
def get_queryset(self):
    """Smart filtering based on user permissions"""
    if not self.request.user.is_authenticated:
        return queryset.filter(is_private=False)
    
    user = self.request.user
    user_memberships = Membership.objects.filter(user=user, is_active=True)
    
    return queryset.filter(
        Q(is_private=False) |      # Public clubs
        Q(creator=user) |          # User's own clubs  
        Q(id__in=user_memberships) # Member clubs
    ).distinct()
```

### **Permission Checks**
- **Create**: Authenticated users only
- **Update/Delete**: Creators only
- **Join**: Public clubs or invited users
- **View Stats**: Members only for private clubs
- **Invite**: Admins/moderators only

### **Validation Rules**
- Club names must be unique per user
- Member limits: 2-1000 members
- Creators cannot leave their own clubs
- Cannot join clubs at capacity
- Cannot join private clubs without invitation

---

## 📊 **Performance Optimizations**

### **Database Optimizations**
```python
queryset = BookClub.objects.select_related('creator').prefetch_related(
    'members', 'reading_sessions__book'
)
```

### **Efficient Queries**
- `select_related()` for foreign keys
- `prefetch_related()` for many-to-many relationships
- Indexed fields for common filters
- Pagination to limit result sets

---

## 🧪 **Testing**

### **API Testing Script**
Run the comprehensive test:
```bash
python test_api_endpoints.py
```

**Tests Include**:
- ✅ User registration and authentication
- ✅ Book club creation with validation
- ✅ Book club listing with pagination
- ✅ Search functionality
- ✅ Discovery endpoints
- ✅ Joining and leaving clubs
- ✅ My clubs and memberships

### **Model Testing Script**
Run the model tests:
```bash
python test_bookclub_views.py
```

---

## 🚀 **Usage Examples**

### **Creating a Book Club**
```bash
curl -X POST http://localhost:8000/api/book-clubs/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sci-Fi Book Club",
    "description": "For science fiction enthusiasts",
    "is_private": false,
    "max_members": 20,
    "location": "Virtual",
    "meeting_frequency": "Monthly"
  }'
```

### **Searching Book Clubs**
```bash
curl "http://localhost:8000/api/book-clubs/search/?search=mystery&is_private=false"
```

### **Joining a Club**
```bash
curl -X POST http://localhost:8000/api/book-clubs/1/join/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎯 **Key Features Summary**

✅ **Complete CRUD Operations**: Create, read, update, delete book clubs
✅ **Smart Permissions**: Privacy-aware filtering and access control  
✅ **Advanced Search**: Full-text search with filters and ordering
✅ **User Context**: Shows membership status and join eligibility
✅ **Statistics**: Club analytics and activity summaries
✅ **Discovery**: Featured, popular, and recent club recommendations
✅ **Membership Management**: Join, leave, invite functionality
✅ **Validation**: Comprehensive input validation and business rules
✅ **Performance**: Optimized queries with proper indexing
✅ **Testing**: Complete test coverage for all endpoints

This comprehensive view system provides a solid foundation for a full-featured book club application with proper security, performance, and user experience considerations.
