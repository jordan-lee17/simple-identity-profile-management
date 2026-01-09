import factory
from django.contrib.auth.models import User
from django.utils import timezone
from .models import *

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")

    password = factory.PostGenerationMethodCall("set_password", "testpass123")

class RequesterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Requester

    user = factory.SubFactory(UserFactory)
    organisation_name = factory.Sequence(lambda n: f"Organisation {n}")
    role = factory.Iterator(["teacher", "employer", "admin"])

class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Person

class NameRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NameRecord

    person = factory.SubFactory(PersonFactory)
    type = factory.Iterator(["legal", "preferred", "professional"])
    value = factory.Faker("name")
    sensitivity_level = factory.Iterator(["low", "medium", "high"])

class ContextPolicyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContextPolicy

    context_name = factory.Sequence(lambda n: f"context{n}")
    allowed_name_types = ["preferred"]
    required_role = "teacher"
    additional_rules = None

class AuditLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuditLog

    requester = factory.SubFactory(RequesterFactory)
    person = factory.SubFactory(PersonFactory)
    context_used = "default"
    fields_returned = ["preferred"]
    timestamp = factory.LazyFunction(timezone.now)