from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from .models import Person, Requester

class IdentityView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, person_id):
        context = request.GET.get("context", "default")
        person = get_object_or_404(Person, id=person_id)

        requester = get_object_or_404(Requester, user=request.user)
        role = requester.role  # <- comes from DB, not ?role=

        return Response({
            "person_id": person_id,
            "context_used": context,
            "requester": request.user.username,
            "requester_role": role,
            "result": {"name": f"Person {person_id}"}
        })


# class IdentityView(APIView):

#     def get(self, request, person_id):

#         requester = request.GET.get("role", "default")
#         context = request.GET.get("context", "default")

#         person = get_object_or_404(Person, id=person_id)

#         # SIMPLE ABAC PROTOTYPE LOGIC
#         data = {}

#         if requester.lower() == "teacher":
#             data["name"] = person.preferred_name

#         elif requester.lower() == "employer":
#             data["name"] = person.legal_name
#             data["title"] = person.professional_title

#         else:
#             data["name"] = person.legal_name

#         return Response({
#             "person_id": person_id,
#             "context_used": context,
#             "role": requester,
#             "result": data
#         })
