from rest_framework.permissions import BasePermission

# Allow access to users with role of admin
class IsAdminRequester(BasePermission):
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            return request.user.requester.role.lower() == "admin"
        except:
            return False
