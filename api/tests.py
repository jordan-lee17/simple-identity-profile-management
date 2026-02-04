from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import *
from .model_factories import *
from .services.abac import evaluate_abac

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
