from django.urls import path
from .views import IdentityView

urlpatterns = [
    path("identity/<int:person_id>/", IdentityView.as_view(), name="identity"),
]
