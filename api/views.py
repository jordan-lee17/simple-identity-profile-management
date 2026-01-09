from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from .models import *
from .services.abac import evaluate_abac

class IdentityView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, person_id):
        context = request.GET.get("context", "default").strip().lower()

        person = get_object_or_404(Person, id=person_id)

        # Get the Requester linked to the authenticated user
        try:
            requester = request.user.requester
        except Requester.DoesNotExist:
            return Response({
                "detail": "Requester profile not found for this user."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        name_records = list(person.name_records.all())

        decision = evaluate_abac(
            requester=requester,
            context=context,
            name_records=name_records,
        )

        # Build response fields
        result = {}
        fields_returned = []

        for record in decision.allowed:
            key = f"{record.type}_name"
            result[key] = record.value
            fields_returned.append(record.type)

        # Return 403 if nothing allowed
        if not result:
            return Response(
                {
                    "person_id": person_id,
                    "context_used": context,
                    "requester": request.user.username,
                    "requester_role": requester.role,
                    "result": {},
                    "denied_reason": decision.denied_reason,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "person_id": person_id,
                "context_used": context,
                "requester": request.user.username,
                "requester_role": requester.role,
                "result": result,
                "fields_returned": fields_returned,
            },
            status=status.HTTP_200_OK,
        )