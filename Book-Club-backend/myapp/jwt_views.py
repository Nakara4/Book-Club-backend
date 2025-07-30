from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token view that includes is_staff in the token payload
    """
    serializer_class = CustomTokenObtainPairSerializer
