from rest_framework import serializers
from .models import *

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = "__all__"

class NameRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NameRecord
        fields = "__all__"

class RequesterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Requester
        fields = "__all__"

class ContextPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContextPolicy
        fields = "__all__"

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"