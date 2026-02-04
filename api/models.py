from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import uuid

# Create your models here.
class Person(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Person {self.id}"

class NameRecord(models.Model):
    NAME_TYPES = [
        ("legal", "Legal"),
        ("preferred", "Preferred"),
        ("professional", "Professional"),
    ]

    SENSITIVITY_LEVELS = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="name_records")
    type = models.CharField(max_length=20, choices=NAME_TYPES)
    value = models.CharField(max_length=255)
    sensitivity_level = models.CharField(max_length=20, choices=SENSITIVITY_LEVELS, default="low")

    def __str__(self):
        return f"{self.person.id} - {self.type}: {self.value}"
    
class Requester(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="requester")
    organisation_name = models.CharField(max_length=255)
    role = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.organisation_name} ({self.role})"


class ContextPolicy(models.Model):
    context_name = models.CharField(max_length=100, unique=True)
    allowed_name_types = models.JSONField(default=list)
    required_role = models.CharField(max_length=100)
    additional_rules = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.context_name
    
class AuditLog(models.Model):
    DECISIONS = [
        ("ALLOW", "ALLOW"),
        ("DENY", "DENY"),
    ]

    request_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    requester = models.ForeignKey(Requester, on_delete=models.CASCADE)
    requester_role = models.CharField(max_length=100)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    context_used = models.CharField(max_length=100)
    decision = models.CharField(max_length=10, choices=DECISIONS)
    denied_reason = models.CharField(max_length=255, blank=True, null=True)
    fields_returned = models.JSONField(default=list)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Tamper-evident fields
    prev_signature = models.CharField(max_length=64, blank=True, null=True)
    signature = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return f"Audit {self.id} - requester {self.requester_id} person {self.person_id}"
    
    def save(self, *args, **kwargs):
        # Append only. Block updates
        if self.pk is not None:
            raise ValidationError("Audit logs are append-only and cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Audit logs are append-only and cannot be deleted.")

