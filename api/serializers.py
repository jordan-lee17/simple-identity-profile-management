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

class MyNameRecordUpsertSerializer(serializers.Serializer):
    type = serializers.CharField()
    value = serializers.CharField(max_length=255)
    sensitivity_level = serializers.ChoiceField(choices=["low", "medium", "high"], default="low")

class RegisterPersonSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    legal_name = serializers.CharField()
    legal_sensitivity_level = serializers.ChoiceField(
        choices=["low", "medium", "high"],
        default="high"
    )

class AdminLegalNameUpsertSerializer(serializers.Serializer):
    person_id = serializers.IntegerField()
    value = serializers.CharField(max_length=255)
    sensitivity_level = serializers.ChoiceField(choices=["low", "medium", "high"], default="high")

class AdminCreateRequesterSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    organisation_name = serializers.CharField()
    role = serializers.CharField()

class NameRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NameRecord
        fields = ["id", "person", "type", "value", "sensitivity_level"]
        read_only_fields = ["id", "person"]

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