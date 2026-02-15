from django.urls import path
from .views import *

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

urlpatterns = [
    # Token
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Profile
    path("api/register/", RegisterPersonView.as_view(), name="register-person"),
    path("api/me/profile/", MyProfileView.as_view(), name="my-profile"),
    # Identity view
    path("identity/<int:person_id>/", IdentityView.as_view(), name="identity"),
    # Admin policy endpoints
    path("api/admin/policies/", AdminContextPolicyListCreateView.as_view(), name="admin-policy-list"),
    path("api/admin/policies/<int:pk>/", AdminContextPolicyDetailView.as_view(), name="admin-policy-detail"),
    # Admin audit log endpoint
    path("api/admin/audit-logs/", AdminAuditLogListView.as_view(), name="admin-auditlog-list"),
    # Admin person list endpoint
    path("api/admin/persons/", AdminPersonListView.as_view(), name="admin-person-list"),
    # Admin operations
    path("api/admin/legal-name/", AdminLegalNameView.as_view(), name="admin-legal-name"),
    path("api/admin/requesters/", AdminCreateRequesterView.as_view(), name="admin-create-requester")
]
