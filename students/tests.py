from datetime import date
import json
import os
import unittest

from django.core.cache import cache
from django.urls import reverse
from django_tenants.test.cases import TenantTestCase
from django.db import connection

from accounts.models import User
from academics.arena_models import StudyGroupRoom
from academics.gamification_models import StudentXP
from academics.models import AcademicYear, Class
from academics.pulse_models import PulseSession
from academics.tutor_models import TutorSession
from students.models import Student
from students.views_ai import _build_voice_xp_token, _voice_active_session_cache_key
from teachers.models import Teacher


@unittest.skipUnless(
	os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1',
	'Tenant integration tests are opt-in; set RUN_TENANT_INTEGRATION_TESTS=1 to execute.',
)
class AuraStudentSecurityTests(TenantTestCase):
	@classmethod
	def setup_tenant(cls, tenant):
		tenant.name = 'Test School'
		tenant.school_type = 'basic'
		return tenant

	def setUp(self):
		connection.set_tenant(self.tenant)
		cache.clear()
		self.year = AcademicYear.objects.create(
			name='2025/2026',
			start_date=date(2025, 9, 1),
			end_date=date(2026, 7, 31),
			is_current=True,
		)

		self.class_a = Class.objects.create(name='Basic 8A', academic_year=self.year)
		self.class_b = Class.objects.create(name='Basic 8B', academic_year=self.year)

		self.teacher_user = User.objects.create_user(
			username='teacher1',
			password='pass1234',
			user_type='teacher',
			first_name='Teach',
			last_name='One',
		)
		self.teacher = Teacher.objects.create(
			user=self.teacher_user,
			employee_id='TCHR1001',
			date_of_birth=date(1990, 1, 1),
			date_of_joining=date(2020, 1, 1),
			qualification='B.Ed',
		)

		self.student_user = User.objects.create_user(
			username='student1',
			password='pass1234',
			user_type='student',
			first_name='Stu',
			last_name='Dent',
		)
		self.student = Student.objects.create(
			user=self.student_user,
			admission_number='ADM1001',
			date_of_birth=date(2012, 1, 1),
			date_of_admission=date(2024, 9, 1),
			current_class=self.class_a,
			emergency_contact='0200000000',
		)

	def turl(self, name, *args):
		return f"/{self.tenant.schema_name}{reverse(name, args=args)}"

	def test_pulse_submit_blocks_cross_class_session(self):
		pulse = PulseSession.objects.create(
			teacher=self.teacher,
			target_class=self.class_b,
			status='active',
			q1_text='Q1',
			q2_text='Q2',
			q3_text='Q3',
			q3_chips=['A', 'B', 'C'],
		)

		self.client.force_login(self.student_user)
		response = self.client.post(
			self.turl('students:pulse_submit', pulse.id),
			data='{"q1": true, "q2": false, "q3": "A"}',
			content_type='application/json',
		)
		self.assertEqual(response.status_code, 403)

	def test_aura_arena_get_handles_invalid_last_id(self):
		StudyGroupRoom.objects.create(name='Arena A', student_class=self.class_a)

		self.client.force_login(self.student_user)
		response = self.client.get(self.turl('students:aura_arena_api') + '?last_id=bad-value')
		self.assertEqual(response.status_code, 200)
		self.assertIn('messages', response.json())

	def test_aura_arena_post_rejects_invalid_json(self):
		StudyGroupRoom.objects.create(name='Arena A', student_class=self.class_a)

		self.client.force_login(self.student_user)
		response = self.client.post(
			self.turl('students:aura_arena_api'),
			data='{not-valid-json',
			content_type='application/json',
		)
		self.assertEqual(response.status_code, 400)

	def _prepare_voice_session(self):
		tutor_session = TutorSession.objects.create(student=self.student, title='Voice Session')
		cache.set(_voice_active_session_cache_key(self.student_user.id), str(tutor_session.id), timeout=3600)
		token = _build_voice_xp_token(self.student_user.id, tutor_session.id)
		return tutor_session, token

	def test_voice_award_xp_requires_valid_token(self):
		tutor_session, _token = self._prepare_voice_session()
		self.client.force_login(self.student_user)

		response = self.client.post(
			self.turl('students:voice_award_xp'),
			data=json.dumps({
				'amount': 10,
				'session_id': str(tutor_session.id),
				'voice_xp_token': 'invalid-token',
			}),
			content_type='application/json',
		)
		self.assertEqual(response.status_code, 403)

	def test_voice_award_xp_success_updates_profile(self):
		tutor_session, token = self._prepare_voice_session()
		self.client.force_login(self.student_user)

		response = self.client.post(
			self.turl('students:voice_award_xp'),
			data=json.dumps({
				'amount': 10,
				'session_id': str(tutor_session.id),
				'voice_xp_token': token,
			}),
			content_type='application/json',
		)
		self.assertEqual(response.status_code, 200)

		xp = StudentXP.objects.get(student=self.student)
		self.assertEqual(xp.total_xp, 10)

	def test_voice_end_session_blocks_future_awards(self):
		tutor_session, token = self._prepare_voice_session()
		self.client.force_login(self.student_user)

		end_resp = self.client.post(
			self.turl('students:voice_end_session'),
			data=json.dumps({
				'session_id': str(tutor_session.id),
				'voice_xp_token': token,
			}),
			content_type='application/json',
		)
		self.assertEqual(end_resp.status_code, 200)

		award_resp = self.client.post(
			self.turl('students:voice_award_xp'),
			data=json.dumps({
				'amount': 10,
				'session_id': str(tutor_session.id),
				'voice_xp_token': token,
			}),
			content_type='application/json',
		)
		self.assertEqual(award_resp.status_code, 403)
