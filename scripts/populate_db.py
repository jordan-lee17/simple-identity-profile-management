import os
import sys
import django
import csv
import json

sys.path.append('C:/Users/jorda/Desktop/School/FYP/identity-manager/identity_manager')  
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "identity_manager.settings")
django.setup()

from django.db import connection
from django.contrib.auth.models import User
from api.models import *

requester_file = './requesters.csv'
policy_file = "./context_policies.csv"
person_file = './persons.csv'
name_record_file = "./name_records.csv"

user_rows = []
policy_rows = []
person_keys = []
name_rows = []

# Load requester
with open(requester_file) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    header = csv_reader.__next__()
    for row in csv_reader:
        # Assign each column to their respective headers
        username, password, organisation_name, role, email = row
        
        user_rows.append({
            "username": username,
            "password": password,
            "email": email,
            "organisation_name": organisation_name,
            "role": role,
        })

# Load context policy
with open(policy_file) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    header = csv_reader.__next__()
    for row in csv_reader:
        # Assign each column to their respective headers
        context_name, allowed_name_types, required_role, additional_rules = row

        allowed_list = json.loads(allowed_name_types) if allowed_name_types.strip() else []
        rules_obj = json.loads(additional_rules) if additional_rules.strip() else None

        policy_rows.append({
            "context_name": context_name.strip(),
            "allowed_name_types": allowed_list,
            "required_role": required_role.strip(),
            "additional_rules": rules_obj,
        })

# Load person
with open(person_file) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    header = csv_reader.__next__()
    for row in csv_reader:
        # Assign each column to their respective headers
        person_key = row[0]
        if person_key:
            person_keys.append(person_key)

# Load name record
with open(name_record_file) as csv_file:
    csv_reader = csv.reader(csv_file)
    header = csv_reader.__next__()
    for row in csv_reader:
        # Assign each column to their respective headers
        person_key, rec_type, value, sensitivity_level = row
        name_rows.append({
            "person_key": person_key,
            "type": rec_type,
            "value": value,
            "sensitivity_level": sensitivity_level,
        })


# Clear existing data
# Keep superusers
User.objects.exclude(is_superuser=True).delete()
# AuditLog.objects.all().delete()
# ContextPolicy.objects.all().delete()
# NameRecord.objects.all().delete()
# Person.objects.all().delete()
# Requester.objects.all().delete()
with connection.cursor() as cursor:
    cursor.execute("""
        TRUNCATE TABLE
            api_namerecord,
            api_person,
            api_requester,
            api_contextpolicy
        RESTART IDENTITY CASCADE;
    """)

# Populate Users + Requesters
for r in user_rows:
    user = User.objects.create_user(
        username=r["username"],
        password=r["password"],
        email=r["email"],
    )

    req = Requester.objects.create(
        user=user,
        organisation_name=r["organisation_name"],
        role=r["role"],
    )

# Populate ContextPolicy
for r in policy_rows:
    context = ContextPolicy.objects.create(
        context_name=r["context_name"],
        allowed_name_types=r["allowed_name_types"],
        required_role=r["required_role"],
        additional_rules=r["additional_rules"],
    )

# Populate Persons (key mapping)
person_map = {} 
for key in person_keys:
    person = Person.objects.create()
    person_map[key] = person

# Populate NameRecords
for r in name_rows:
    name_record = NameRecord.objects.create(
        person=person_map[r["person_key"]],
        type=r["type"],
        value=r["value"],
        sensitivity_level=r["sensitivity_level"],
    )