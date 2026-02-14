from rest_framework import serializers
from .models import *
from .services.labels import build_safe_person_label

class PersonSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = "__all__"

    def get_label(self, obj):
        return build_safe_person_label(obj)

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
    requester_username = serializers.CharField(source="requester.user.username")
    
    class Meta:
        model = AuditLog
        fields = "__all__"