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
    # Register new user
    path("api/register/", RegisterView.as_view(), name="register-person"),
    # Profile for admin/requester
    path("api/me/", MeView.as_view(), name="me"),
    # Profile for user
    path("api/me/profile/", MyProfileView.as_view(), name="my-profile"),
    # Identity view
    path("identity/<int:person_id>/", IdentityView.as_view(), name="identity"),
    # Admin requester list endpoint
    path("api/admin/requesters/", AdminRequesterListView.as_view(), name="admin-requester-list"),
    # Admin register requester
    path("api/admin/new-requesters/", AdminCreateRequesterView.as_view(), name="admin-create-requester"),
    # Admin policy endpoints
    path("api/admin/policies/", AdminContextPolicyListCreateView.as_view(), name="admin-policy-list"),
    path("api/admin/policies/<int:pk>/", AdminContextPolicyDetailView.as_view(), name="admin-policy-detail"),
    # Admin audit log endpoint
    path("api/admin/audit-logs/", AdminAuditLogListView.as_view(), name="admin-auditlog-list"),
    # Admin person list endpoint
    path("api/admin/persons/", AdminPersonListView.as_view(), name="admin-person-list"),
    # Admin Profile View
    path("api/admin/persons/<int:person_id>/names/", AdminPersonNameRecordsView.as_view(), name="admin-person-names"),
    # Admin operations
    path("api/admin/legal-name/", AdminLegalNameView.as_view(), name="admin-legal-name"),
    path("api/admin/requesters/", AdminCreateRequesterView.as_view(), name="admin-create-requester")
]
