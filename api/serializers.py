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

class AdminNameRecordUpsertSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["legal", "preferred", "professional"])
    value = serializers.CharField(max_length=255)
    sensitivity_level = serializers.ChoiceField(choices=["low", "medium", "high"])

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    legal_name = serializers.CharField()
    preferred_name = serializers.CharField()
    professional_name = serializers.CharField()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def create(self, validated_data):
        username = validated_data["username"]
        email = validated_data["email"]
        password = validated_data["password"]

        legal_name = validated_data["legal_name"]
        preferred_name = validated_data.get("preferred_name")
        professional_name = validated_data.get("professional_name")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        person = Person.objects.create()
        PersonProfile.objects.create(user=user, person=person)

        NameRecord.objects.create(
            person=person,
            type="legal",
            value=legal_name,
            sensitivity_level="high",
        )

        NameRecord.objects.create(
            person=person,
            type="preferred",
            value=preferred_name,
            sensitivity_level="low",
        )

        NameRecord.objects.create(
            person=person,
            type="professional",
            value=professional_name,
            sensitivity_level="low",
        )

        return user

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

    def validate_role(self, v):
        v = v.strip()
        if not v:
            raise serializers.ValidationError("Role is required.")
        return v

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

class MeSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField(allow_blank=True, required=False)
    account_type = serializers.ChoiceField(choices=["person", "requester", "admin"])

    requester = serializers.DictField(required=False, allow_null=True)
    person_profile = serializers.DictField(required=False, allow_null=True)