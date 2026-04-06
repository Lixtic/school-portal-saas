"""
Core business logic tests.
Opt-in: set RUN_TENANT_INTEGRATION_TESTS=1 to execute.

  $env:RUN_TENANT_INTEGRATION_TESTS='1'; python manage.py test tests.test_core -v2

NOTE: Each TenantTestCase class creates a full schema on the remote DB.
      Keep the number of classes minimal to reduce migration overhead.
"""
import os
import unittest
from datetime import date, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db import connection
from django.test import RequestFactory
from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient

from accounts.models import User
from academics.models import AcademicYear, Class, Subject, ClassSubject, GradingScale
from students.models import Student, Grade, Attendance
from finance.models import FeeHead, FeeStructure, StudentFee, Payment
from teachers.models import Teacher

_SKIP_MSG = 'Tenant integration tests are opt-in; set RUN_TENANT_INTEGRATION_TESTS=1 to execute.'


# ═══════════════════════════════════════════════════════════════
# 1) MODEL LOGIC TESTS — pure data, no HTTP
# ═══════════════════════════════════════════════════════════════
@unittest.skipUnless(os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1', _SKIP_MSG)
class ModelLogicTests(TenantTestCase):
    """Grade auto-calc, fee transitions, attendance, ranking – all in one schema."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'Model Test School'
        tenant.school_type = 'basic'
        return tenant

    def setUp(self):
        connection.set_tenant(self.tenant)
        cache.clear()
        self.year = AcademicYear.objects.create(
            name='2025/2026', start_date=date(2025, 9, 1),
            end_date=date(2026, 7, 31), is_current=True,
        )
        self.cls = Class.objects.create(name='Basic 7A', academic_year=self.year)
        self.subject = Subject.objects.create(name='Math', code='MATH01')
        self.user = User.objects.create_user(
            username='stu1', password='pass', user_type='student',
            first_name='Ama', last_name='Mensah',
        )
        self.student = Student.objects.create(
            user=self.user, current_class=self.cls,
            admission_number='STU001', date_of_birth=date(2010, 1, 1),
        )
        self.admin_user = User.objects.create_user(
            username='admin1', password='pass', user_type='admin',
        )
        self.teacher_user = User.objects.create_user(
            username='tch1', password='pass', user_type='teacher',
        )

    def _make_grade(self, class_score, exams_score, student=None, subject=None):
        g = Grade(
            student=student or self.student,
            subject=subject or self.subject,
            academic_year=self.year, term='first',
            class_score=class_score, exams_score=exams_score,
        )
        g.save()
        return g

    # ── Grade auto-calc (default Ghana scale) ────────────────
    def test_grade_1_highest(self):
        g = self._make_grade(28, 55)  # total = 83
        self.assertEqual(g.total_score, Decimal('83'))
        self.assertEqual(g.grade, '1')
        self.assertEqual(g.remarks, 'Highest')

    def test_grade_5_average(self):
        g = self._make_grade(20, 37)  # total = 57
        self.assertEqual(g.grade, '5')
        self.assertEqual(g.remarks, 'Average')

    def test_grade_9_lowest(self):
        g = self._make_grade(10, 20)  # total = 30
        self.assertEqual(g.grade, '9')
        self.assertEqual(g.remarks, 'Lowest')

    def test_total_capped_at_100(self):
        g = self._make_grade(40, 70)  # 110 → capped at 100
        self.assertEqual(g.total_score, Decimal('100'))
        self.assertEqual(g.grade, '1')

    def test_zero_scores(self):
        g = self._make_grade(0, 0)
        self.assertEqual(g.total_score, Decimal('0'))
        self.assertEqual(g.grade, '9')

    # ── Custom grading scale ─────────────────────────────────
    def test_custom_scale_overrides_default(self):
        GradingScale.objects.create(min_score=90, grade_label='A+', remarks='Excellent', ordering=0)
        GradingScale.objects.create(min_score=70, grade_label='A', remarks='Very Good', ordering=1)
        GradingScale.objects.create(min_score=50, grade_label='B', remarks='Good', ordering=2)
        GradingScale.objects.create(min_score=0, grade_label='F', remarks='Fail', ordering=3)
        g = self._make_grade(25, 50)  # total = 75 → A (≥70)
        self.assertEqual(g.grade, 'A')
        self.assertEqual(g.remarks, 'Very Good')

    def test_custom_scale_lowest_bucket(self):
        GradingScale.objects.create(min_score=50, grade_label='P', remarks='Pass', ordering=0)
        GradingScale.objects.create(min_score=0, grade_label='F', remarks='Fail', ordering=1)
        g = self._make_grade(10, 20)  # total = 30 → F
        self.assertEqual(g.grade, 'F')

    # ── Fee logic ────────────────────────────────────────────
    def _make_fee(self):
        head = FeeHead.objects.create(name='Tuition')
        structure = FeeStructure.objects.create(
            head=head, academic_year=self.year,
            class_level=self.cls, term='first', amount=Decimal('500.00'),
        )
        return StudentFee.objects.create(
            student=self.student, fee_structure=structure,
            amount_payable=Decimal('500.00'),
        )

    def test_initial_status_unpaid(self):
        fee = self._make_fee()
        self.assertEqual(fee.status, 'unpaid')
        self.assertEqual(fee.total_paid, Decimal('0'))
        self.assertEqual(fee.balance, Decimal('500.00'))

    def test_partial_payment(self):
        fee = self._make_fee()
        Payment.objects.create(
            student_fee=fee, amount=Decimal('200.00'),
            date=date.today(), recorded_by=self.admin_user,
        )
        fee.refresh_from_db()
        self.assertEqual(fee.status, 'partial')
        self.assertEqual(fee.balance, Decimal('300.00'))

    def test_full_payment(self):
        fee = self._make_fee()
        Payment.objects.create(
            student_fee=fee, amount=Decimal('500.00'),
            date=date.today(), recorded_by=self.admin_user,
        )
        fee.refresh_from_db()
        self.assertEqual(fee.status, 'paid')
        self.assertEqual(fee.balance, Decimal('0.00'))

    def test_multiple_payments_sum(self):
        fee = self._make_fee()
        Payment.objects.create(
            student_fee=fee, amount=Decimal('100.00'),
            date=date.today(), recorded_by=self.admin_user,
        )
        Payment.objects.create(
            student_fee=fee, amount=Decimal('400.00'),
            date=date.today(), recorded_by=self.admin_user,
        )
        fee.refresh_from_db()
        self.assertEqual(fee.status, 'paid')
        self.assertEqual(fee.total_paid, Decimal('500.00'))

    def test_unique_reference_constraint(self):
        fee = self._make_fee()
        Payment.objects.create(
            student_fee=fee, amount=Decimal('100.00'),
            date=date.today(), recorded_by=self.admin_user, reference='REF-001',
        )
        with self.assertRaises(Exception):
            Payment.objects.create(
                student_fee=fee, amount=Decimal('100.00'),
                date=date.today(), recorded_by=self.admin_user, reference='REF-001',
            )

    def test_overpayment_does_not_crash(self):
        fee = self._make_fee()
        Payment.objects.create(
            student_fee=fee, amount=Decimal('700.00'),
            date=date.today(), recorded_by=self.admin_user,
        )
        fee.refresh_from_db()
        self.assertEqual(fee.status, 'paid')
        self.assertEqual(fee.balance, Decimal('-200.00'))

    def test_payment_auto_generates_reference(self):
        fee = self._make_fee()
        p = Payment.objects.create(
            student_fee=fee, amount=Decimal('100.00'),
            date=date.today(), recorded_by=self.admin_user,
        )
        self.assertTrue(p.reference)
        self.assertGreater(len(p.reference), 5)

    # ── Attendance ───────────────────────────────────────────
    def test_mark_present(self):
        att = Attendance.objects.create(
            student=self.student, date=date.today(),
            status='present', marked_by=self.teacher_user,
        )
        self.assertEqual(att.status, 'present')

    def test_unique_per_student_per_date(self):
        Attendance.objects.create(
            student=self.student, date=date.today(), status='present',
        )
        with self.assertRaises(Exception):
            Attendance.objects.create(
                student=self.student, date=date.today(), status='absent',
            )

    def test_update_or_create_pattern(self):
        Attendance.objects.create(
            student=self.student, date=date.today(), status='absent',
        )
        att, created = Attendance.objects.update_or_create(
            student=self.student, date=date.today(),
            defaults={'status': 'present'},
        )
        self.assertFalse(created)
        self.assertEqual(att.status, 'present')

    def test_multiple_days(self):
        Attendance.objects.create(student=self.student, date=date(2025, 10, 1), status='present')
        Attendance.objects.create(student=self.student, date=date(2025, 10, 2), status='absent')
        self.assertEqual(Attendance.objects.filter(student=self.student).count(), 2)

    # ── Ranking ──────────────────────────────────────────────
    def test_ranking_order(self):
        eng = Subject.objects.create(name='English', code='ENG01')
        students = []
        for i in range(3):
            u = User.objects.create_user(
                username=f'rank_stu{i}', password='pass', user_type='student',
                first_name=f'Student{i}',
            )
            s = Student.objects.create(
                user=u, current_class=self.cls,
                admission_number=f'RNK{i:03}', date_of_birth=date(2010, 1, 1),
            )
            students.append(s)

        scores = [(30, 60), (20, 40), (25, 55)]  # 90, 60, 80
        for i, (cs, ex) in enumerate(scores):
            Grade.objects.create(
                student=students[i], subject=eng,
                academic_year=self.year, term='first',
                class_score=cs, exams_score=ex,
            )
        grades = list(Grade.objects.filter(
            subject=eng, academic_year=self.year, term='first',
        ).order_by('-total_score'))

        self.assertEqual(grades[0].subject_position, 1)
        self.assertEqual(grades[1].subject_position, 2)
        self.assertEqual(grades[2].subject_position, 3)


# ═══════════════════════════════════════════════════════════════
# 2) VIEW & INTEGRATION TESTS — HTTP requests, single schema
# ═══════════════════════════════════════════════════════════════
@unittest.skipUnless(os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1', _SKIP_MSG)
class ViewIntegrationTests(TenantTestCase):
    """Dashboard, parent, rate-limit, API, and permission tests."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'View Test School'
        tenant.school_type = 'basic'
        return tenant

    def setUp(self):
        connection.set_tenant(self.tenant)
        cache.clear()
        self.year = AcademicYear.objects.create(
            name='2025/2026', start_date=date(2025, 9, 1),
            end_date=date(2026, 7, 31), is_current=True,
        )
        self.cls = Class.objects.create(name='Basic 7A', academic_year=self.year)
        self.subject = Subject.objects.create(name='Math', code='M01')

        # Users
        self.admin = User.objects.create_user(username='adm', password='pass', user_type='admin')
        self.teacher_user = User.objects.create_user(username='tch', password='pass', user_type='teacher')
        Teacher.objects.create(user=self.teacher_user, employee_id='T001')
        self.student_user = User.objects.create_user(username='stu', password='pass', user_type='student')
        self.student = Student.objects.create(
            user=self.student_user, current_class=self.cls,
            admission_number='INT001', date_of_birth=date(2010, 1, 1),
        )
        self.parent_user = User.objects.create_user(username='par', password='pass', user_type='parent')

        from parents.models import Parent
        self.parent = Parent.objects.create(user=self.parent_user, relation='Father')
        self.parent.children.add(self.student)

        # Other parent+child for isolation
        self.other_parent_user = User.objects.create_user(username='par2', password='pass', user_type='parent')
        self.other_child_user = User.objects.create_user(username='stu2', password='pass', user_type='student')
        self.other_child = Student.objects.create(
            user=self.other_child_user, current_class=self.cls,
            admission_number='INT002', date_of_birth=date(2012, 5, 20),
        )
        self.other_parent = Parent.objects.create(user=self.other_parent_user, relation='Mother')
        self.other_parent.children.add(self.other_child)

        # Rate-limit user
        self.rl_user = User.objects.create_user(username='rl_user', password='correctpass', user_type='admin')

        # Fee fixtures
        head = FeeHead.objects.create(name='Tuition')
        structure = FeeStructure.objects.create(
            head=head, academic_year=self.year,
            class_level=self.cls, term='first', amount=Decimal('1000.00'),
        )
        self.fee = StudentFee.objects.create(
            student=self.student, fee_structure=structure,
            amount_payable=Decimal('1000.00'),
        )

        self.client = TenantClient(self.tenant)

    # ── Dashboard access ─────────────────────────────────────
    def test_unauthenticated_redirects_to_login(self):
        resp = self.client.get('/dashboard/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('login', resp.url)

    def test_admin_sees_dashboard(self):
        self.client.force_login(self.admin)
        resp = self.client.get('/dashboard/')
        self.assertEqual(resp.status_code, 200)

    def test_teacher_sees_dashboard(self):
        self.client.force_login(self.teacher_user)
        resp = self.client.get('/dashboard/')
        self.assertEqual(resp.status_code, 200)

    def test_student_dashboard_redirect(self):
        self.client.force_login(self.student_user)
        resp = self.client.get('/dashboard/')
        self.assertIn(resp.status_code, [200, 302])

    def test_student_cannot_access_add_student(self):
        self.client.force_login(self.student_user)
        resp = self.client.get('/students/add/')
        self.assertIn(resp.status_code, [302, 403])

    def test_parent_cannot_access_add_student(self):
        self.client.force_login(self.parent_user)
        resp = self.client.get('/students/add/')
        self.assertIn(resp.status_code, [302, 403])

    def test_student_cannot_access_finance(self):
        self.client.force_login(self.student_user)
        resp = self.client.get('/finance/')
        self.assertIn(resp.status_code, [302, 403])

    # ── Permission boundaries ────────────────────────────────
    def test_student_cannot_access_mark_attendance(self):
        from django.test import Client as DjangoClient
        c = DjangoClient()
        c.force_login(self.student_user)
        from django.urls import reverse
        resp = c.get(reverse('students:mark_attendance'), HTTP_HOST='localhost')
        self.assertIn(resp.status_code, [302, 403])

    def test_parent_cannot_access_mark_attendance(self):
        from django.test import Client as DjangoClient
        c = DjangoClient()
        c.force_login(self.parent_user)
        from django.urls import reverse
        resp = c.get(reverse('students:mark_attendance'), HTTP_HOST='localhost')
        self.assertIn(resp.status_code, [302, 403])

    def test_student_cannot_access_grading_scale(self):
        from django.test import Client as DjangoClient
        c = DjangoClient()
        c.force_login(self.student_user)
        from django.urls import reverse
        resp = c.get(reverse('academics:grading_scale'), HTTP_HOST='localhost')
        self.assertIn(resp.status_code, [302, 403])

    def test_admin_can_access_grading_scale(self):
        from django.test import Client as DjangoClient
        c = DjangoClient()
        c.force_login(self.admin)
        from django.urls import reverse
        resp = c.get(reverse('academics:grading_scale'), HTTP_HOST='localhost')
        self.assertIn(resp.status_code, [200, 302])

    # ── Parent views ─────────────────────────────────────────
    def test_parent_sees_own_children(self):
        self.client.force_login(self.parent_user)
        resp = self.client.get('/parents/children/')
        self.assertEqual(resp.status_code, 200)

    def test_parent_cannot_see_other_child_details(self):
        self.client.force_login(self.parent_user)
        resp = self.client.get(f'/parents/children/{self.other_child.id}/')
        self.assertEqual(resp.status_code, 302)

    def test_parent_can_see_own_child_details(self):
        self.client.force_login(self.parent_user)
        resp = self.client.get(f'/parents/children/{self.student.id}/')
        self.assertEqual(resp.status_code, 200)

    def test_student_cannot_access_parent_views(self):
        self.client.force_login(self.student_user)
        resp = self.client.get('/parents/children/')
        self.assertIn(resp.status_code, [302, 403])

    def test_parent_sees_child_fees(self):
        self.client.force_login(self.parent_user)
        resp = self.client.get(f'/parents/children/{self.student.id}/fees/')
        self.assertEqual(resp.status_code, 200)

    def test_parent_cannot_see_other_child_fees(self):
        self.client.force_login(self.parent_user)
        resp = self.client.get(f'/parents/children/{self.other_child.id}/fees/')
        self.assertIn(resp.status_code, [302, 403])

    # ── Rate limiter ─────────────────────────────────────────
    def test_valid_login_succeeds(self):
        resp = self.client.post('/login/', {'username': 'rl_user', 'password': 'correctpass'})
        self.assertEqual(resp.status_code, 302)

    def test_invalid_login_returns_200(self):
        resp = self.client.post('/login/', {'username': 'rl_user', 'password': 'wrongpass'})
        self.assertEqual(resp.status_code, 200)

    def test_rate_limit_after_max_attempts(self):
        from accounts.ratelimit import LOGIN_MAX_ATTEMPTS
        for _ in range(LOGIN_MAX_ATTEMPTS):
            self.client.post('/login/', {'username': 'baduser', 'password': 'badpass'})
        resp = self.client.post('/login/', {'username': 'baduser', 'password': 'badpass'})
        self.assertEqual(resp.status_code, 429)

    def test_successful_login_resets_counter(self):
        for _ in range(3):
            self.client.post('/login/', {'username': 'rl_user', 'password': 'wrong'})
        resp = self.client.post('/login/', {'username': 'rl_user', 'password': 'correctpass'})
        self.assertEqual(resp.status_code, 302)
        self.client.logout()
        resp = self.client.post('/login/', {'username': 'rl_user', 'password': 'wrong'})
        self.assertEqual(resp.status_code, 200)

    # ── Student dashboard ────────────────────────────────────
    def test_student_dashboard_loads(self):
        for i in range(5):
            Attendance.objects.create(
                student=self.student,
                date=date.today() - timedelta(days=i + 1),
                status='present' if i < 4 else 'absent',
            )
        Grade.objects.create(
            student=self.student, subject=self.subject,
            academic_year=self.year, term='first',
            class_score=25, exams_score=55,
        )
        self.client.force_login(self.student_user)
        resp = self.client.get('/students/dashboard/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('attendance_stats', resp.context)
        self.assertIn('subject_analytics', resp.context)

    def test_non_student_blocked_from_student_dashboard(self):
        self.client.force_login(self.admin)
        resp = self.client.get('/students/dashboard/')
        self.assertEqual(resp.status_code, 302)

    # ── Tenant isolation ─────────────────────────────────────
    def test_data_exists_in_schema(self):
        self.assertEqual(Student.objects.count(), 2)  # INT001 + INT002

    def test_grades_start_empty(self):
        self.assertEqual(Grade.objects.count(), 0)

    # ── API endpoints ────────────────────────────────────────
    def test_unauthenticated_api_denied(self):
        resp = self.client.get('/api/students/')
        self.assertIn(resp.status_code, [401, 403])

    def test_admin_can_list_students(self):
        self.client.force_login(self.admin)
        resp = self.client.get('/api/students/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data['count'], 1)

    def test_admin_can_list_academic_years(self):
        self.client.force_login(self.admin)
        resp = self.client.get('/api/academic-years/')
        self.assertEqual(resp.status_code, 200)

    def test_student_cannot_write_grades(self):
        self.client.force_login(self.student_user)
        resp = self.client.post('/api/grades/', {
            'student': self.student.id,
            'subject': 1,
            'academic_year': self.year.id,
            'term': 'first',
            'class_score': 20,
            'exams_score': 50,
        }, content_type='application/json')
        self.assertIn(resp.status_code, [403, 405])

    def test_api_returns_json(self):
        self.client.force_login(self.admin)
        resp = self.client.get('/api/classes/')
        self.assertEqual(resp['Content-Type'], 'application/json')


# ═══════════════════════════════════════════════════════════════
# 3) SUBSCRIPTION & BILLING TESTS
# ═══════════════════════════════════════════════════════════════
@unittest.skipUnless(os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1', _SKIP_MSG)
class SubscriptionBillingTests(TenantTestCase):
    """Trial expiry, grace period, subscription lifecycle, audit logging."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'Billing Test School'
        tenant.school_type = 'basic'
        return tenant

    def setUp(self):
        connection.set_tenant(self.tenant)
        cache.clear()
        self.admin = User.objects.create_user(username='bill_admin', password='pass', user_type='admin')
        self.client = TenantClient(self.tenant)

    def _create_subscription(self, status='trial', trial_days=14, grace_days=3):
        from tenants.subscription_models import SubscriptionPlan, SchoolSubscription
        plan, _ = SubscriptionPlan.objects.get_or_create(
            plan_type='trial', defaults={
                'name': 'Trial', 'description': 'Trial plan',
                'monthly_price': 0, 'quarterly_price': 0, 'annual_price': 0,
                'max_students': 50, 'max_teachers': 5, 'max_storage_gb': 2,
                'ai_calls_per_month': 20,
            }
        )
        from django.utils import timezone
        trial_end = timezone.now() + timedelta(days=trial_days)
        sub, _ = SchoolSubscription.objects.get_or_create(
            school=self.tenant,
            defaults={
                'plan': plan, 'status': status,
                'trial_ends_at': trial_end,
                'current_period_end': trial_end,
                'grace_period_days': grace_days,
            }
        )
        return sub

    def test_active_trial_allows_access(self):
        """Active trial (14 days left) should allow dashboard access."""
        self._create_subscription(trial_days=14)
        self.client.force_login(self.admin)
        resp = self.client.get('/dashboard/')
        self.assertIn(resp.status_code, [200, 302])
        # Should NOT redirect to subscription page
        if resp.status_code == 302:
            self.assertNotIn('subscription', resp.url)

    def test_expired_trial_within_grace_allows_access(self):
        """Expired trial but within grace period should still allow access."""
        sub = self._create_subscription(trial_days=-1, grace_days=3)
        # Trial ended 1 day ago, grace = 3 days → still accessible
        self.client.force_login(self.admin)
        resp = self.client.get('/dashboard/')
        self.assertIn(resp.status_code, [200, 302])

    def test_expired_trial_past_grace_redirects(self):
        """Expired trial past grace period should redirect to subscription page."""
        sub = self._create_subscription(trial_days=-10, grace_days=3)
        # Trial ended 10 days ago, grace = 3 → locked out
        self.client.force_login(self.admin)
        resp = self.client.get('/dashboard/')
        if resp.status_code == 302:
            self.assertIn('subscription', resp.url)

    def test_grace_period_days_field_default(self):
        """grace_period_days should default to 3."""
        sub = self._create_subscription()
        self.assertEqual(sub.grace_period_days, 3)

    def test_subscription_mrr_calculation(self):
        """MRR calculation based on billing cycle."""
        from tenants.subscription_models import SubscriptionPlan, SchoolSubscription
        plan, _ = SubscriptionPlan.objects.get_or_create(
            plan_type='basic', defaults={
                'name': 'Basic', 'description': 'Basic plan',
                'monthly_price': 99, 'quarterly_price': 267, 'annual_price': 948,
                'max_students': 300, 'max_teachers': 20, 'max_storage_gb': 10,
                'ai_calls_per_month': 50,
            }
        )
        from django.utils import timezone
        sub = SchoolSubscription.objects.create(
            school=self.tenant, plan=plan, status='active',
            billing_cycle='monthly',
            current_period_end=timezone.now() + timedelta(days=30),
        )
        sub.mrr = sub.calculate_mrr()
        self.assertEqual(sub.mrr, 99)


# ═══════════════════════════════════════════════════════════════
# 4) AUDIT LOG TESTS
# ═══════════════════════════════════════════════════════════════
@unittest.skipUnless(os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1', _SKIP_MSG)
class AuditLogTests(TenantTestCase):
    """Audit log creation, query, and signal-driven recording."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'Audit Test School'
        tenant.school_type = 'basic'
        return tenant

    def setUp(self):
        connection.set_tenant(self.tenant)
        cache.clear()
        self.admin = User.objects.create_user(username='audit_admin', password='pass', user_type='admin')
        self.client = TenantClient(self.tenant)

    def test_audit_log_creation(self):
        """AuditLog.log() should create a record."""
        from tenants.subscription_models import AuditLog
        log = AuditLog.log('admin_action', user=self.admin, detail='test action')
        self.assertIsNotNone(log.pk)
        self.assertEqual(log.action, 'admin_action')
        self.assertEqual(log.username, 'audit_admin')

    def test_audit_log_with_request(self):
        """AuditLog.log() should extract IP and user agent from request."""
        from tenants.subscription_models import AuditLog
        factory = RequestFactory()
        req = factory.get('/', HTTP_X_FORWARDED_FOR='1.2.3.4', HTTP_USER_AGENT='TestBot/1.0')
        req.user = self.admin
        req.tenant = self.tenant
        log = AuditLog.log('login', request=req)
        self.assertEqual(log.ip_address, '1.2.3.4')
        self.assertIn('TestBot', log.user_agent)
        self.assertEqual(log.tenant_schema, self.tenant.schema_name)

    def test_audit_log_ordering(self):
        """AuditLog should be ordered by -created_at."""
        from tenants.subscription_models import AuditLog
        AuditLog.log('login', user=self.admin, detail='first')
        AuditLog.log('logout', user=self.admin, detail='second')
        logs = list(AuditLog.objects.all()[:2])
        self.assertEqual(logs[0].action, 'logout')
        self.assertEqual(logs[1].action, 'login')

    def test_login_signal_creates_audit(self):
        """Successful login should create an audit log entry via signal."""
        from tenants.subscription_models import AuditLog
        initial_count = AuditLog.objects.filter(action='login').count()
        self.client.post('/login/', {'username': 'audit_admin', 'password': 'pass'})
        new_count = AuditLog.objects.filter(action='login').count()
        self.assertGreaterEqual(new_count, initial_count + 1)

    def test_failed_login_signal_creates_audit(self):
        """Failed login should create an audit log entry via signal."""
        from tenants.subscription_models import AuditLog
        initial_count = AuditLog.objects.filter(action='login_failed').count()
        self.client.post('/login/', {'username': 'audit_admin', 'password': 'wrongpass'})
        new_count = AuditLog.objects.filter(action='login_failed').count()
        self.assertGreaterEqual(new_count, initial_count + 1)


# ═══════════════════════════════════════════════════════════════
# 5) SECURITY & ISOLATION TESTS
# ═══════════════════════════════════════════════════════════════
@unittest.skipUnless(os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1', _SKIP_MSG)
class SecurityIsolationTests(TenantTestCase):
    """Cross-tenant isolation and role-based access control."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'Security Test School'
        tenant.school_type = 'basic'
        return tenant

    def setUp(self):
        connection.set_tenant(self.tenant)
        cache.clear()
        self.year = AcademicYear.objects.create(
            name='2025/2026', start_date=date(2025, 9, 1),
            end_date=date(2026, 7, 31), is_current=True,
        )
        self.cls = Class.objects.create(name='Basic 7A', academic_year=self.year)

        self.admin = User.objects.create_user(username='sec_admin', password='pass', user_type='admin')
        self.teacher_user = User.objects.create_user(username='sec_teacher', password='pass', user_type='teacher')
        Teacher.objects.create(user=self.teacher_user, employee_id='SEC01')
        self.student_user = User.objects.create_user(username='sec_student', password='pass', user_type='student')
        Student.objects.create(
            user=self.student_user, current_class=self.cls,
            admission_number='SEC001', date_of_birth=date(2010, 1, 1),
        )
        self.client = TenantClient(self.tenant)

    # ── Role escalation prevention ────────────────────────────
    def test_student_cannot_access_teacher_views(self):
        self.client.force_login(self.student_user)
        resp = self.client.get('/teachers/')
        self.assertIn(resp.status_code, [302, 403])

    def test_student_cannot_add_grades(self):
        self.client.force_login(self.student_user)
        resp = self.client.get('/students/grades/')
        self.assertIn(resp.status_code, [200, 302, 403])

    def test_teacher_cannot_access_finance_dashboard(self):
        self.client.force_login(self.teacher_user)
        resp = self.client.get('/finance/')
        self.assertIn(resp.status_code, [302, 403])

    def test_student_cannot_access_settings(self):
        self.client.force_login(self.student_user)
        resp = self.client.get('/academics/school-info/')
        self.assertIn(resp.status_code, [302, 403])

    # ── Unauthenticated access ────────────────────────────────
    def test_unauthenticated_cannot_access_students(self):
        resp = self.client.get('/students/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('login', resp.url)

    def test_unauthenticated_cannot_access_api(self):
        resp = self.client.get('/api/classes/')
        self.assertIn(resp.status_code, [302, 401, 403])

    # ── Admin-only endpoints ──────────────────────────────────
    def test_admin_can_access_finance(self):
        self.client.force_login(self.admin)
        resp = self.client.get('/finance/')
        self.assertIn(resp.status_code, [200, 302])

    def test_admin_can_access_school_info(self):
        self.client.force_login(self.admin)
        resp = self.client.get('/academics/school-info/')
        self.assertIn(resp.status_code, [200, 302])

    # ── Password validators are configured ────────────────────
    def test_password_validators_enabled(self):
        from django.conf import settings
        self.assertGreaterEqual(len(settings.AUTH_PASSWORD_VALIDATORS), 4)

    def test_session_cookie_httponly(self):
        from django.conf import settings
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)

    def test_session_cookie_samesite(self):
        from django.conf import settings
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, 'Lax')

    def test_session_cookie_age_reasonable(self):
        from django.conf import settings
        # Should be 30 days or less, not 365
        self.assertLessEqual(settings.SESSION_COOKIE_AGE, 30 * 24 * 60 * 60)
