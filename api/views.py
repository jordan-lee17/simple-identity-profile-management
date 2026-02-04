from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from .models import *
from .permissions import IsAdminRequester
from .serializers import ContextPolicySerializer, AuditLogSerializer
from .services.abac import evaluate_abac

# Identity retrieval
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
            AuditLog.objects.create(
                requester=requester,
                person=person,
                context_used=context,
                fields_returned=[],
                decision="DENY",
                denied_reason=decision.denied_reason,
            )

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
        
        # Allowed case
        AuditLog.objects.create(
            requester=requester,
            person=person,
            context_used=context,
            fields_returned=fields_returned,
            decision="ALLOW",
            denied_reason=None,
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
    
# Admin context policy management
class AdminContextPolicyListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminRequester]

    def get(self, request):
        policies = ContextPolicy.objects.all().order_by("context_name")
        return Response(ContextPolicySerializer(policies, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ContextPolicySerializer(data=request.data)
        if serializer.is_valid():
            policy = serializer.save()
            return Response(ContextPolicySerializer(policy).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminContextPolicyDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminRequester]

    def get(self, request, pk: int):
        policy = get_object_or_404(ContextPolicy, pk=pk)
        return Response(ContextPolicySerializer(policy).data, status=status.HTTP_200_OK)

    def put(self, request, pk: int):
        policy = get_object_or_404(ContextPolicy, pk=pk)
        serializer = ContextPolicySerializer(policy, data=request.data)
        if serializer.is_valid():
            policy = serializer.save()
            return Response(ContextPolicySerializer(policy).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk: int):
        policy = get_object_or_404(ContextPolicy, pk=pk)
        serializer = ContextPolicySerializer(policy, data=request.data, partial=True)
        if serializer.is_valid():
            policy = serializer.save()
            return Response(ContextPolicySerializer(policy).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk: int):
        policy = get_object_or_404(ContextPolicy, pk=pk)
        policy.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class AdminAuditLogListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminRequester]

    def get(self, request):
        logs = AuditLog.objects.all().order_by("-timestamp")

        # Filters
        requester_id = request.GET.get("requester_id")
        person_id = request.GET.get("person_id")
        context_used = request.GET.get("context")
        decision = request.GET.get("decision")

        if requester_id:
            logs = logs.filter(requester_id=requester_id)
        if person_id:
            logs = logs.filter(person_id=person_id)
        if context_used:
            logs = logs.filter(context_used=context_used.strip().lower())
        if decision:
            logs = logs.filter(decision=decision.strip().upper())

        return Response(AuditLogSerializer(logs, many=True).data, status=status.HTTP_200_OK)
