from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import *
from .permissions import IsAdminRequester
from .serializers import ContextPolicySerializer, AuditLogSerializer, PersonSerializer
from .services.abac import evaluate_abac
from .services.audit import compute_audit_signature, build_audit_payload

# Person list retrieval
class AdminPersonListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminRequester]

    def get(self, request):
        # Query params
        q = (request.GET.get("q") or "").strip()
        page = int(request.GET.get("page") or 1)
        page_size = int(request.GET.get("page_size") or 20)
        page_size = max(1, min(page_size, 100))

        qs = Person.objects.prefetch_related("name_records").order_by("id")

        # Match NameRecord value
        if q:
            qs = qs.filter(
                Q(name_records__value__icontains=q)
            ).distinct()

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size
        items = qs[start:end]

        data = PersonSerializer(items, many=True).data

        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": data,
            },
            status=status.HTTP_200_OK,
        )

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
            # Create audit log
            last = AuditLog.objects.order_by("-timestamp").first()
            
            # Change prev_sig to last one or None if there isn't any
            prev_sig = last.signature if last else None

            log = AuditLog.objects.create(
                requester=requester,
                person=person,
                context_used=context,
                fields_returned=[],
                decision="DENY",
                denied_reason=decision.denied_reason,
                prev_signature=prev_sig,
            )

            payload = build_audit_payload(
                requester_id=log.requester_id,
                person_id=log.person_id,
                context_used=log.context_used,
                fields_returned=log.fields_returned,
                decision=log.decision,
                denied_reason=log.denied_reason,
                timestamp_iso=log.timestamp.isoformat(),
            )
            
            # Do a one time update to set signature
            AuditLog.objects.filter(pk=log.pk).update(
                signature=compute_audit_signature(payload=payload, prev_signature=prev_sig)
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
        last = AuditLog.objects.order_by("-timestamp").first()

        # Change prev_sig to last one or None if there isn't any
        prev_sig = last.signature if last else None

        log = AuditLog.objects.create(
            requester=requester,
            person=person,
            context_used=context,
            fields_returned=fields_returned,
            decision="ALLOW",
            denied_reason=None,
            prev_signature=prev_sig,
        )

        payload = build_audit_payload(
            requester_id=log.requester_id,
            person_id=log.person_id,
            context_used=log.context_used,
            fields_returned=log.fields_returned,
            decision=log.decision,
            denied_reason=log.denied_reason,
            timestamp_iso=log.timestamp.isoformat(),
        )

        # Do a one time update to set signature
        AuditLog.objects.filter(pk=log.pk).update(
            signature=compute_audit_signature(payload=payload, prev_signature=prev_sig)
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
        decision = request.GET.get("decision")
        context = request.GET.get("context")
        q = request.GET.get("q")

        page = int(request.GET.get("page") or 1)
        page_size = int(request.GET.get("page_size") or 20)
        page_size = max(1, min(page_size, 100))

        qs = AuditLog.objects.select_related(
            "requester__user", "person"
        ).order_by("-timestamp")

        if decision:
            qs = qs.filter(decision=decision.upper())

        if context:
            qs = qs.filter(context_used__icontains=context)

        if q:
            qs = qs.filter(
                Q(requester__user__username__icontains=q)
                | Q(person__id__icontains=q)
            )

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        logs = qs[start:end]

        serializer = AuditLogSerializer(logs, many=True)
        print(serializer.data)
        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )