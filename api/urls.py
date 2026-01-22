from django.urls import path
from .views import *

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

urlpatterns = [
    path("identity/<int:person_id>/", IdentityView.as_view(), name="identity"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Admin policy endpoints
    path("api/admin/policies/", AdminContextPolicyListCreateView.as_view(), name="admin-policy-list"),
    path("api/admin/policies/<int:pk>/", AdminContextPolicyDetailView.as_view(), name="admin-policy-detail"),
]
