from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Person

class IdentityView(APIView):

    def get(self, request, person_id):

        requester = request.GET.get("role", "default")
        context = request.GET.get("context", "default")

        person = get_object_or_404(Person, id=person_id)

        # SIMPLE ABAC PROTOTYPE LOGIC
        data = {}

        if requester.lower() == "teacher":
            data["name"] = person.preferred_name

        elif requester.lower() == "employer":
            data["name"] = person.legal_name
            data["title"] = person.professional_title

        else:
            data["name"] = person.legal_name

        return Response({
            "person_id": person_id,
            "context_used": context,
            "role": requester,
            "result": data
        })
