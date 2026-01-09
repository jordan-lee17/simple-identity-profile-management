from rest_framework import serializers
from .models import *

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["id", "created_at", "updated_at"]

class NameRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NameRecord
        fields = ["id", "person", "type", "value", "sensitivity_level"]

class RequesterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Requester
        fields = ["id", "username", "organisation_name", "role"]

class ContextPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContextPolicy
        fields = ["id", "context_name", "allowed_name_types", "required_role", "additional_rules"]

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ["id", "requester", "person", "context_used", "fields_returned", "timestamp"]