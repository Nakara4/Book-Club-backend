from rest_framework.permissions import BasePermission


class IsStaffMember(BasePermission):
    """
    Allows access only to staff members.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff
