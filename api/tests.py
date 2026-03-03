from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase
from .models import *
from .model_factories import *
from .services.abac import evaluate_abac
from .services.audit import verify_audit_log_entry
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta

# Create your tests here.

# Test ABAC
class ABACServiceTests(APITestCase):
    def test_abac_denies_when_no_policy(self):
        requester = RequesterFactory(role="teacher")
        person = PersonFactory()
        records = [
            NameRecordFactory(person=person, 
                              type="preferred", 
                              sensitivity_level="low", 
                              value="Kai Yin")
        ]

        decision = evaluate_abac(requester=requester, context="school", name_records=records)
        self.assertEqual(len(decision.allowed), 0)
        self.assertIn("No policy", decision.denied_reason)

    def test_abac_denies_when_role_mismatch(self):
        # Policy requires teacher
        ContextPolicyFactory(context_name="school", 
                             required_role="teacher", 
                             allowed_name_types=["preferred"])

        requester = RequesterFactory(role="employer")
        person = PersonFactory()
        records = [
            NameRecordFactory(person=person, 
                              type="preferred", 
                              sensitivity_level="low", 
                              value="Kai Yin")
        ]

        decision = evaluate_abac(requester=requester, context="school", name_records=records)
        self.assertEqual(len(decision.allowed), 0)
        self.assertIn("role not permitted", decision.denied_reason)

    def test_abac_allows_only_types_in_policy(self):
        ContextPolicyFactory(context_name="job", 
                             required_role="employer", 
                             allowed_name_types=["legal", "professional"])

        requester = RequesterFactory(role="employer")
        person = PersonFactory()

        legal = NameRecordFactory(person=person, 
                                  type="legal", 
                                  value="Jordan Lee", 
                                  sensitivity_level="low")
        preferred = NameRecordFactory(person=person, 
                                      type="preferred", 
                                      value="Jordan", 
                                      sensitivity_level="low")
        prof = NameRecordFactory(person=person, 
                                 type="professional", 
                                 value="Mr Jordan Lee", 
                                 sensitivity_level="low")

        decision = evaluate_abac(requester=requester, context="job", name_records=[legal, preferred, prof])
        allowed_types = [r.type for r in decision.allowed]

        self.assertIn("legal", allowed_types)
        self.assertIn("professional", allowed_types)
        self.assertNotIn("preferred", allowed_types)

    def test_abac_blocks_high_sensitivity_unless_admin(self):
        ContextPolicyFactory(context_name="school", 
                             required_role="teacher", 
                             allowed_name_types=["preferred"])

        teacher_req = RequesterFactory(role="teacher")
        admin_req = RequesterFactory(role="admin")
        person = PersonFactory()

        high_pref = NameRecordFactory(person=person, 
                                      type="preferred", 
                                      value="Sensitive Name", 
                                      sensitivity_level="high")

        decision_teacher = evaluate_abac(requester=teacher_req, context="school", name_records=[high_pref])
        self.assertEqual(len(decision_teacher.allowed), 0)

        decision_admin = evaluate_abac(requester=admin_req, context="school", name_records=[high_pref])
        self.assertEqual(len(decision_admin.allowed), 1)

    def test_abac_blocks_high_sensitivity_unless_policy_allows(self):
        # Policy does not allow high
        ContextPolicyFactory(context_name="school",
                             required_role="teacher",
                             allowed_name_types=["preferred"],
                             additional_rules={"allow_high": False},)

        teacher_req = RequesterFactory(role="teacher")
        person = PersonFactory()

        high_pref = NameRecordFactory(person=person,
                                      type="preferred",
                                      value="Sensitive Name",
                                      sensitivity_level="high")

        decision_teacher = evaluate_abac(requester=teacher_req, context="school", name_records=[high_pref])
        self.assertEqual(len(decision_teacher.allowed), 0)

        # Update policy to allow high sensitivity
        ContextPolicy.objects.filter(context_name="school").update(additional_rules={"allow_high": True})

        decision_teacher2 = evaluate_abac(requester=teacher_req, context="school", name_records=[high_pref])
        self.assertEqual(len(decision_teacher2.allowed), 1)

    def test_abac_healthcare_context_allows_legal_and_preferred(self):
        ContextPolicyFactory(context_name="healthcare", 
                             required_role="doctor", 
                             allowed_name_types=["legal", "preferred"])

        requester = RequesterFactory(role="doctor")
        person = PersonFactory()

        legal = NameRecordFactory(person=person, 
                                  type="legal", 
                                  value="Jordan Lee", 
                                  sensitivity_level="low")
        preferred = NameRecordFactory(person=person, 
                                      type="preferred", 
                                      value="Jordan", 
                                      sensitivity_level="low")
        prof = NameRecordFactory(person=person, 
                                 type="professional", 
                                 value="Mr Jordan Lee", 
                                 sensitivity_level="low")

        decision = evaluate_abac(requester=requester, context="healthcare", name_records=[legal, preferred, prof])
        allowed_types = [r.type for r in decision.allowed]

        self.assertIn("legal", allowed_types)
        self.assertIn("preferred", allowed_types)
        self.assertNotIn("professional", allowed_types)

    def test_abac_banking_context_allows_legal_only(self):
        ContextPolicyFactory(context_name="banking",
                             required_role="bank_staff",
                             allowed_name_types=["legal"])

        requester = RequesterFactory(role="bank_staff")
        person = PersonFactory()

        legal = NameRecordFactory(person=person, 
                                  type="legal", 
                                  value="Jordan Lee", 
                                  sensitivity_level="low")
        preferred = NameRecordFactory(person=person, 
                                      type="preferred", 
                                      value="Jordan", 
                                      sensitivity_level="low")

        decision = evaluate_abac(requester=requester, context="banking", name_records=[legal, preferred])
        allowed_types = [r.type for r in decision.allowed]

        self.assertEqual(allowed_types, ["legal"])

# Test admin policies api
class AdminContextPolicyAPITests(APITestCase):
    def setUp(self):
        self.url_list = reverse("admin-policy-list")

        self.admin_user = UserFactory(username="admin1")
        RequesterFactory(user=self.admin_user, role="admin", organisation_name="GovTech")

        self.non_admin_user = UserFactory(username="teacher1")
        RequesterFactory(user=self.non_admin_user, role="teacher", organisation_name="School A")

    def test_admin_policy_list_requires_auth(self):
        res = self.client.get(self.url_list)
        self.assertIn(res.status_code, [401, 403])

    def test_non_admin_cannot_list_policies(self):
        self.client.force_authenticate(user=self.non_admin_user)
        res = self.client.get(self.url_list)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_policies(self):
        ContextPolicyFactory(context_name="school")
        ContextPolicyFactory(context_name="job")

        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(self.url_list)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 2)

    def test_admin_can_create_policy(self):
        self.client.force_authenticate(user=self.admin_user)

        payload = {
            "context_name": "hospital",
            "allowed_name_types": ["legal"],
            "required_role": "doctor",
            "additional_rules": {"allow_high": False},
        }

        res = self.client.post(self.url_list, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["context_name"], "hospital")

    def test_admin_create_policy_invalid_payload(self):
        self.client.force_authenticate(user=self.admin_user)

        # Missing required fields
        payload = {"context_name": "invalid_only_name"}
        res = self.client.post(self.url_list, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_update_policy_put(self):
        self.client.force_authenticate(user=self.admin_user)

        policy = ContextPolicyFactory(
            context_name="school",
            allowed_name_types=["preferred"],
            required_role="teacher",
            additional_rules={"allow_high": False},
        )

        url_detail = reverse("admin-policy-detail", kwargs={"pk": policy.id})
        payload = {
            "context_name": "school",
            "allowed_name_types": ["preferred", "legal"],
            "required_role": "teacher",
            "additional_rules": {"allow_high": True},
        }

        res = self.client.put(url_detail, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("legal", res.data["allowed_name_types"])
        self.assertTrue(res.data["additional_rules"]["allow_high"])

    def test_admin_can_patch_policy(self):
        self.client.force_authenticate(user=self.admin_user)

        policy = ContextPolicyFactory(
            context_name="job",
            allowed_name_types=["legal"],
            required_role="employer",
            additional_rules={"allow_high": False},
        )

        url_detail = reverse("admin-policy-detail", kwargs={"pk": policy.id})
        res = self.client.patch(url_detail, {"additional_rules": {"allow_high": True}}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["additional_rules"]["allow_high"])

    def test_admin_can_delete_policy(self):
        self.client.force_authenticate(user=self.admin_user)

        policy = ContextPolicyFactory(context_name="temp_context")
        url_detail = reverse("admin-policy-detail", kwargs={"pk": policy.id})

        res = self.client.delete(url_detail)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        # Verify it is gone
        res2 = self.client.get(url_detail)
        self.assertEqual(res2.status_code, status.HTTP_404_NOT_FOUND)

# Test admin audit log API
class AdminAuditLogAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("admin-auditlog-list")

        self.admin_user = UserFactory(username="admin1")
        RequesterFactory(user=self.admin_user, role="admin", organisation_name="GovTech")

        self.non_admin_user = UserFactory(username="teacher1")
        RequesterFactory(user=self.non_admin_user, role="teacher", organisation_name="School A")

        # Make 1 sample log
        person = PersonFactory()
        requester = RequesterFactory(role="admin")
        AuditLog.objects.create(
            requester=requester,
            person=person,
            context_used="school",
            fields_returned=["preferred"],
            decision="ALLOW",
            denied_reason=None,
        )

    def test_admin_audit_logs_requires_auth(self):
        res = self.client.get(self.url)
        self.assertIn(res.status_code, [401, 403])

    def test_non_admin_cannot_list_audit_logs(self):
        self.client.force_authenticate(user=self.non_admin_user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_audit_logs(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 1)

# Test audit logging security
class AuditLogSecurityTests(APITestCase):
    def setUp(self):
        self.admin_user = UserFactory(username="admin_audit")
        self.admin_req = RequesterFactory(user=self.admin_user, role="admin", organisation_name="GovTech")

        self.person = PersonFactory()

    def test_audit_log_cannot_be_updated_via_model_save(self):
        log = AuditLog.objects.create(
            requester=self.admin_req,
            person=self.person,
            context_used="school",
            fields_returned=["preferred"],
            decision="ALLOW",
            denied_reason=None,
        )

        with self.assertRaises(ValidationError):
            log.context_used = "job"
            log.save()

    def test_audit_log_cannot_be_deleted(self):
        log = AuditLog.objects.create(
            requester=self.admin_req,
            person=self.person,
            context_used="school",
            fields_returned=[],
            decision="DENY",
            denied_reason="test",
        )

        with self.assertRaises(ValidationError):
            log.delete()
    
    def test_audit_log_signature_detects_tampering(self):
        log = AuditLog.objects.create(
            requester=self.admin_req,
            person=self.person,
            context_used="school",
            fields_returned=["preferred"],
            decision="ALLOW",
            denied_reason=None,
            prev_signature=None,
        )

        # Set a correct signature for baseline
        from .services.audit import compute_audit_signature, build_audit_payload
        payload = build_audit_payload(
            requester_id=log.requester_id,
            person_id=log.person_id,
            context_used=log.context_used,
            fields_returned=log.fields_returned,
            decision=log.decision,
            denied_reason=log.denied_reason,
            timestamp_iso=log.timestamp.isoformat(),
        )
        sig = compute_audit_signature(payload=payload, prev_signature=None)
        AuditLog.objects.filter(pk=log.pk).update(signature=sig)

        log.refresh_from_db()
        self.assertTrue(verify_audit_log_entry(log))

        # Tamper in DB
        AuditLog.objects.filter(pk=log.pk).update(context_used="job")
        log.refresh_from_db()

        self.assertFalse(verify_audit_log_entry(log))

# Test audit log
class IdentityAuditLogTests(APITestCase):
    def setUp(self):
        # Policies
        ContextPolicyFactory(context_name="school", required_role="teacher", allowed_name_types=["preferred"])
        ContextPolicyFactory(context_name="job", required_role="employer", allowed_name_types=["legal", "professional"])

        # Name records
        self.person = PersonFactory()
        NameRecordFactory(person=self.person, type="legal", value="Jordan Lee", sensitivity_level="low")
        NameRecordFactory(person=self.person, type="preferred", value="Jordan", sensitivity_level="low")
        NameRecordFactory(person=self.person, type="professional", value="Jordan Lee (Intern)", sensitivity_level="low")

        # Users + Requesters
        self.teacher_user = UserFactory(username="teacher1")
        RequesterFactory(user=self.teacher_user, role="teacher", organisation_name="School A")

        self.employer_user = UserFactory(username="employer1")
        RequesterFactory(user=self.employer_user, role="employer", organisation_name="Company B")

        self.url = reverse("identity", kwargs={"person_id": self.person.id})

    def test_allow_creates_audit_log(self):
        self.client.force_authenticate(user=self.teacher_user)

        res = self.client.get(self.url + "?context=school")
        self.assertEqual(res.status_code, 200)

        self.assertEqual(AuditLog.objects.count(), 1)
        log = AuditLog.objects.first()
        self.assertEqual(log.person_id, self.person.id)
        self.assertEqual(log.context_used, "school")
        self.assertEqual(log.decision, "ALLOW")
        self.assertIn("preferred", log.fields_returned)

    def test_deny_creates_audit_log(self):
        self.client.force_authenticate(user=self.employer_user)

        res = self.client.get(self.url + "?context=school")
        self.assertEqual(res.status_code, 403)

        self.assertEqual(AuditLog.objects.count(), 1)
        log = AuditLog.objects.first()
        self.assertEqual(log.decision, "DENY")
        self.assertEqual(log.fields_returned, [])
        self.assertTrue(log.denied_reason)

# Test IdentityView end to end
class IdentityAPITests(APITestCase):
    def setUp(self):
        # Policies
        ContextPolicyFactory(context_name="school", 
                             required_role="teacher", 
                             allowed_name_types=["preferred"])
        ContextPolicyFactory(context_name="job", 
                             required_role="employer", 
                             allowed_name_types=["legal", "professional"])
        ContextPolicyFactory(context_name="healthcare",
                             required_role="doctor",
                             allowed_name_types=["legal", "preferred"])
        ContextPolicyFactory(context_name="banking",
                             required_role="bank_staff",
                             allowed_name_types=["legal"])

        # Name records
        self.person = PersonFactory()
        NameRecordFactory(person=self.person, 
                          type="legal", 
                          value="Jordan Lee", 
                          sensitivity_level="low")
        NameRecordFactory(person=self.person, 
                          type="preferred", 
                          value="Jordan", 
                          sensitivity_level="low")
        NameRecordFactory(person=self.person, 
                          type="professional", 
                          value="Jordan Lee (Intern)", 
                          sensitivity_level="low")

        # Users + Requesters
        self.teacher_user = UserFactory(username="teacher1")
        self.teacher_requester = RequesterFactory(user=self.teacher_user, role="teacher", organisation_name="School A")

        self.employer_user = UserFactory(username="employer1")
        self.employer_requester = RequesterFactory(user=self.employer_user, role="employer", organisation_name="Company B")

        self.doctor_user = UserFactory(username="doctor1")
        self.doctor_requester = RequesterFactory(user=self.doctor_user, role="doctor", organisation_name="Hospital X")

        self.bank_user = UserFactory(username="bank1")
        self.bank_requester = RequesterFactory(user=self.bank_user, role="bank_staff", organisation_name="Bank Y")


        self.url = reverse("identity", kwargs={"person_id": self.person.id})

    def test_identity_requires_auth(self):
        response = self.client.get(self.url + "?context=school")
        self.assertIn(response.status_code, [401, 403])

    def test_teacher_gets_preferred_in_school_context(self):
        self.client.force_authenticate(user=self.teacher_user)

        response = self.client.get(self.url + "?context=school")
        self.assertEqual(response.status_code, 200)

        self.assertIn("preferred_name", response.data["result"])
        self.assertNotIn("legal_name", response.data["result"])
        self.assertNotIn("professional_name", response.data["result"])

    def test_employer_gets_legal_and_professional_in_job_context(self):
        self.client.force_authenticate(user=self.employer_user)

        response = self.client.get(self.url + "?context=job")
        self.assertEqual(response.status_code, 200)

        self.assertIn("legal_name", response.data["result"])
        self.assertIn("professional_name", response.data["result"])
        self.assertNotIn("preferred_name", response.data["result"])

    def test_doctor_gets_legal_and_preferred_in_healthcare_context(self):
        self.client.force_authenticate(user=self.doctor_user)

        response = self.client.get(self.url + "?context=healthcare")
        self.assertEqual(response.status_code, 200)

        self.assertIn("legal_name", response.data["result"])
        self.assertIn("preferred_name", response.data["result"])
        self.assertNotIn("professional_name", response.data["result"])

    def test_bank_staff_gets_legal_only_in_banking_context(self):
        self.client.force_authenticate(user=self.bank_user)

        response = self.client.get(self.url + "?context=banking")
        self.assertEqual(response.status_code, 200)

        self.assertIn("legal_name", response.data["result"])
        self.assertNotIn("preferred_name", response.data["result"])
        self.assertNotIn("professional_name", response.data["result"])

    def test_role_mismatch_returns_403(self):
        self.client.force_authenticate(user=self.employer_user)

        # Employer requesting "school" context (requires teacher)
        response = self.client.get(self.url + "?context=school")
        self.assertEqual(response.status_code, 403)
        self.assertIn("denied_reason", response.data)

# Test identity validation
class IdentityValidationEdgeTests(APITestCase):
    def setUp(self):
        ContextPolicyFactory(
            context_name="school",
            required_role="teacher",
            allowed_name_types=["preferred"],
        )

        self.person = PersonFactory()
        NameRecordFactory(person=self.person, type="preferred", value="Jordan", sensitivity_level="low")

        self.user = UserFactory(username="teacher_edge")
        RequesterFactory(user=self.user, role="teacher", organisation_name="School A")

        self.url = reverse("identity", kwargs={"person_id": self.person.id})
        self.client.force_authenticate(user=self.user)

    def test_missing_context_defaults_and_denies(self):
        # No ?context= provided -> uses "default" -> no policy -> DENY 403
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data["context_used"], "default")
        self.assertIn("denied_reason", res.data)
        self.assertEqual(res.data["result"], {})

        # audit log created
        self.assertEqual(AuditLog.objects.count(), 1)
        log = AuditLog.objects.first()
        self.assertEqual(log.context_used, "default")
        self.assertEqual(log.decision, "DENY")

    def test_context_is_trimmed_and_lowercased(self):
        res = self.client.get(self.url + "?context=  ScHoOl  ")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["context_used"], "school")

    def test_invalid_person_id_returns_404(self):
        bad_url = reverse("identity", kwargs={"person_id": 999999})
        res = self.client.get(bad_url + "?context=school")
        self.assertEqual(res.status_code, 404)

    def test_user_without_requester_gets_403(self):
        # user has no requester profile
        user2 = UserFactory(username="no_req")
        self.client.force_authenticate(user=user2)

        res = self.client.get(self.url + "?context=school")
        self.assertEqual(res.status_code, 403)
        self.assertIn("Requester profile not found", res.data.get("detail", ""))

# Test profile creation and editing
class ProfileAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse("register-person")
        self.me_profile_url = reverse("my-profile")
        self.admin_create_requester_url = reverse("admin-create-requester")

        # Admin user + requester
        self.admin_user = UserFactory(username="admin_hybrid")
        self.admin_req = RequesterFactory(user=self.admin_user, role="admin", organisation_name="GovTech")

    def test_register_creates_person_profile_and_legal_name(self):
        payload = {
            "username": "person1",
            "password": "pass123456",
            "email": "person1@example.com",
            "legal_name": "Jordan Lee Jun Loong",
            "sensitivity_level": "high",
            "preferred_name": "Jordan",
            "professional_name": "Mr Jordan Lee",
        }

        res = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("person_id", res.data)
        person_id = res.data["person_id"]

        # Person profile created
        user = User.objects.get(username="person1")
        self.assertTrue(hasattr(user, "person_profile"))
        self.assertEqual(user.person_profile.person_id, person_id)

        # Legal NameRecord created
        legal = NameRecord.objects.filter(person_id=person_id, type="legal").first()
        self.assertIsNotNone(legal)
        self.assertEqual(legal.value, "Jordan Lee Jun Loong")
        self.assertEqual(legal.sensitivity_level, "high")

    def test_self_service_can_edit_preferred_and_professional(self):
        # Register a normal user
        res = self.client.post(self.register_url, {
            "username": "person2",
            "password": "pass123456",
            "email": "person2@example.com",
            "legal_name": "Alicia Tan Wei Ling",
            "sensitivity_level": "high",
            "preferred_name": "Ali",
            "professional_name": "Ms Alicia Tan",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="person2")
        self.client.force_authenticate(user=user)

        # Add preferred
        res2 = self.client.patch(self.me_profile_url, {
            "type": "preferred",
            "value": "Alicia",
            "sensitivity_level": "low",
        }, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        # Add professional
        res3 = self.client.patch(self.me_profile_url, {
            "type": "professional",
            "value": "Ms Tan",
            "sensitivity_level": "medium",
        }, format="json")
        self.assertEqual(res3.status_code, status.HTTP_200_OK)

        # Verify stored
        person_id = user.person_profile.person_id
        self.assertTrue(NameRecord.objects.filter(person_id=person_id, type="preferred", value="Alicia").exists())
        self.assertTrue(NameRecord.objects.filter(person_id=person_id, type="professional", value="Ms Tan").exists())

    def test_self_service_cannot_edit_legal_name(self):
        # Register a normal user (creates legal)
        res = self.client.post(self.register_url, {
            "username": "person3",
            "password": "pass123456",
            "email": "person3@example.com",
            "legal_name": "Muhammad Haziq bin Ahmad",
            "sensitivity_level": "high",
            "preferred_name": "Haziq",
            "professional_name": "Muhammad Haziq",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="person3")
        self.client.force_authenticate(user=user)

        # Attempt to edit legal via /api/me/profile/
        res2 = self.client.patch(self.me_profile_url, {
            "type": "legal",
            "value": "Hacked Legal Name",
            "sensitivity_level": "high",
        }, format="json")

        self.assertEqual(res2.status_code, status.HTTP_403_FORBIDDEN)

        # Ensure unchanged
        person_id = user.person_profile.person_id
        legal = NameRecord.objects.get(person_id=person_id, type="legal")
        self.assertEqual(legal.value, "Muhammad Haziq bin Ahmad")

    def test_admin_can_update_legal_name(self):
        # Create a normal user to own a person/profile
        res = self.client.post(self.register_url, {
            "username": "person4",
            "password": "pass123456",
            "email": "person4@example.com",
            "legal_name": "Old Legal",
            "sensitivity_level": "high",
            "preferred_name": "Old",
            "professional_name": "Old Legal",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        person_id = res.data["person_id"]

        # Admin updates legal
        self.client.force_authenticate(user=self.admin_user)
        admin_edit_legal_url = reverse("admin-person-names", kwargs={"person_id": person_id})
        res2 = self.client.put(admin_edit_legal_url, {
            "person_id": person_id,
            "type": "legal",
            "value": "New Legal Name",
            "sensitivity_level": "high",
        }, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        legal = NameRecord.objects.get(person_id=person_id, type="legal")
        self.assertEqual(legal.value, "New Legal Name")

    def test_non_admin_cannot_update_legal_name(self):
        # Create a normal user
        res = self.client.post(self.register_url, {
            "username": "person5",
            "password": "pass123456",
            "email": "person5@example.com",
            "legal_name": "Legal X",
            "sensitivity_level": "high",
            "preferred_name": "Legal",
            "professional_name": "Legal X",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        person_id = res.data["person_id"]

        # Non-admin requester
        non_admin_user = UserFactory(username="not_admin")
        RequesterFactory(user=non_admin_user, role="teacher", organisation_name="School A")

        self.client.force_authenticate(user=non_admin_user)
        admin_edit_legal_url = reverse("admin-person-names", kwargs={"person_id": person_id})
        res2 = self.client.put(admin_edit_legal_url, {
            "person_id": person_id,
            "type": "legal",
            "value": "Should Fail",
            "sensitivity_level": "high",
        }, format="json")
        self.assertEqual(res2.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_requester_account(self):
        self.client.force_authenticate(user=self.admin_user)

        payload = {
            "username": "req_teacher_1",
            "password": "pass123456",
            "email": "req_teacher_1@example.com",
            "organisation_name": "School A",
            "role": "teacher",
        }

        res = self.client.post(self.admin_create_requester_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Verify User + Requester created
        u = User.objects.get(username="req_teacher_1")
        self.assertTrue(hasattr(u, "requester"))
        self.assertEqual(u.requester.role, "teacher")
        self.assertEqual(u.requester.organisation_name, "School A")

    def test_non_admin_cannot_create_requester_account(self):
        non_admin_user = UserFactory(username="teacher_non_admin")
        RequesterFactory(user=non_admin_user, role="teacher", organisation_name="School A")

        self.client.force_authenticate(user=non_admin_user)

        payload = {
            "username": "req_fail",
            "password": "pass123456",
            "email": "req_fail@example.com",
            "organisation_name": "Company B",
            "role": "employer",
        }

        res = self.client.post(self.admin_create_requester_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

class MeViewTests(APITestCase):
    def setUp(self):
        self.me_url = reverse("me")

    def test_me_requires_auth(self):
        res = self.client.get(self.me_url)
        self.assertIn(res.status_code, [401, 403])

    def test_me_returns_person_account_type(self):
        user = UserFactory(username="person_me")
        person = PersonFactory()
        PersonProfileFactory(user=user, person=person)

        self.client.force_authenticate(user=user)
        res = self.client.get(self.me_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["account_type"], "person")
        self.assertIsNotNone(res.data["person_profile"])
        self.assertEqual(res.data["person_profile"]["person_id"], person.id)
        self.assertIsNone(res.data["requester"])

    def test_me_returns_requester_account_type(self):
        user = UserFactory(username="req_me")
        RequesterFactory(user=user, role="teacher", organisation_name="School A")

        self.client.force_authenticate(user=user)
        res = self.client.get(self.me_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["account_type"], "requester")
        self.assertIsNotNone(res.data["requester"])
        self.assertEqual(res.data["requester"]["role"], "teacher")
        self.assertEqual(res.data["requester"]["organisation_name"], "School A")
        self.assertIsNone(res.data["person_profile"])

    def test_me_returns_admin_account_type(self):
        user = UserFactory(username="admin_me")
        RequesterFactory(user=user, role="admin", organisation_name="GovTech")

        self.client.force_authenticate(user=user)
        res = self.client.get(self.me_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["account_type"], "admin")
        self.assertIsNotNone(res.data["requester"])
        self.assertEqual(res.data["requester"]["role"], "admin")

class MyProfileEdgeCaseTests(APITestCase):
    def setUp(self):
        self.url = reverse("my-profile")

    def test_requester_cannot_access_my_profile(self):
        user = UserFactory(username="req_no_profile")
        RequesterFactory(user=user, role="teacher", organisation_name="School A")

        self.client.force_authenticate(user=user)
        res = self.client.get(self.url)

        self.assertIn(res.status_code, [403, 404])

class AdminRequesterListTests(APITestCase):
    def setUp(self):
        self.url = reverse("admin-requester-list")

        self.admin_user = UserFactory(username="admin_req_list")
        RequesterFactory(user=self.admin_user, role="admin", organisation_name="GovTech")

        self.teacher_user = UserFactory(username="teacher_req_list")
        RequesterFactory(user=self.teacher_user, role="teacher", organisation_name="School A")

        # Seed requesters
        u1 = UserFactory(username="alice")
        RequesterFactory(user=u1, role="teacher", organisation_name="School Alpha")

        u2 = UserFactory(username="bob")
        RequesterFactory(user=u2, role="employer", organisation_name="Company B")

        u3 = UserFactory(username="charlie")
        RequesterFactory(user=u3, role="doctor", organisation_name="Hospital X")

    def test_requires_auth(self):
        res = self.client.get(self.url)
        self.assertIn(res.status_code, [401, 403])

    def test_non_admin_forbidden(self):
        self.client.force_authenticate(user=self.teacher_user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("results", res.data)
        self.assertGreaterEqual(res.data["count"], 3)

    def test_admin_search_by_username(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(self.url, {"q": "alice"})
        self.assertEqual(res.status_code, 200)
        usernames = [x.get("username") for x in res.data["results"]]
        self.assertIn("alice", usernames)

    def test_admin_search_by_org(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(self.url, {"q": "Hospital"})
        self.assertEqual(res.status_code, 200)
        orgs = [x.get("organisation_name") for x in res.data["results"]]
        self.assertTrue(any("Hospital" in (o or "") for o in orgs))

    def test_admin_search_by_role(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(self.url, {"q": "doctor"})
        self.assertEqual(res.status_code, 200)
        roles = [x.get("role") for x in res.data["results"]]
        self.assertIn("doctor", roles)

    def test_pagination(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(self.url, {"page": 1, "page_size": 2})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["page"], 1)
        self.assertEqual(res.data["page_size"], 2)
        self.assertLessEqual(len(res.data["results"]), 2)

# Test JWT authentication
class IdentityJWTTests(APITestCase):
    def setUp(self):
        # Policy
        ContextPolicyFactory(
            context_name="school",
            required_role="teacher",
            allowed_name_types=["preferred"],
        )

        # Person + records
        self.person = PersonFactory()
        NameRecordFactory(person=self.person, type="preferred", value="Jordan", sensitivity_level="low")

        # User + requester
        self.user = UserFactory(username="jwt_teacher")
        RequesterFactory(user=self.user, role="teacher", organisation_name="School A")

        self.url = reverse("identity", kwargs={"person_id": self.person.id})

    def set_bearer(self, token: str):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def make_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token), str(refresh)

    def test_identity_works_with_valid_access_token(self):
        access, _ = self.make_tokens(self.user)
        self.set_bearer(access)

        res = self.client.get(self.url + "?context=school")
        self.assertEqual(res.status_code, 200)
        self.assertIn("preferred_name", res.data["result"])

    def test_identity_rejects_missing_token(self):
        res = self.client.get(self.url + "?context=school")
        self.assertIn(res.status_code, [401, 403])

    def test_identity_rejects_expired_access_token(self):
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token

        # Force token to be expired
        access.set_exp(lifetime=timedelta(seconds=-1))

        self.set_bearer(str(access))
        res = self.client.get(self.url + "?context=school")

        self.assertEqual(res.status_code, 401)

# Test refresh token
class JWTRefreshTests(APITestCase):
    def setUp(self):
        self.user = UserFactory(username="refresh_user")

    def test_refresh_returns_new_access_token(self):
        refresh = RefreshToken.for_user(self.user)

        url = reverse("token_refresh")
        res = self.client.post(url, {"refresh": str(refresh)}, format="json")

        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.data)
        self.assertTrue(isinstance(res.data["access"], str))

    def test_refresh_with_invalid_token_returns_401(self):
        url = reverse("token_refresh")
        res = self.client.post(url, {"refresh": "not-a-real-token"}, format="json")

        self.assertEqual(res.status_code, 401)