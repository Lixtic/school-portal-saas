"""
Core business logic tests.
Opt-in: set RUN_TENANT_INTEGRATION_TESTS=1 to execute.

  $env:RUN_TENANT_INTEGRATION_TESTS='1'; python manage.py test tests.test_core -v2
"""
import os
import unittest
from datetime import date, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db import connection
from django.test import RequestFactory, Client, override_settings
from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient

from accounts.models import User
from academics.models import AcademicYear, Class, Subject, ClassSubject, GradingScale
from students.models import Student, Grade, Attendance
from finance.models import FeeHead, FeeStructure, StudentFee, Payment
from teachers.models import Teacher


@unittest.skipUnless(
    os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1',
    'Tenant integration tests are opt-in; set RUN_TENANT_INTEGRATION_TESTS=1 to execute.',
)
class GradeAutoCalcTests(TenantTestCase):
    """Grade.save() auto-calculates total_score, grade, and remarks."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'Test School'
        tenant.school_type = 'basic'
        return tenant

    def setUp(self):
        connection.set_tenant(self.tenant)
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

    def _make_grade(self, class_score, exams_score):
        g = Grade(
            student=self.student, subject=self.subject,
            academic_year=self.year, term='first',
            class_score=class_score, exams_score=exams_score,
        )
        g.save()
        return g

    # ── Default Ghana scale ──────────────────────────────────
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
        g = self._make_grade(40, 70)  # total = 110 → capped at 100
        self.assertEqual(g.total_score, Decimal('100'))
        self.assertEqual(g.grade, '1')

    def test_zero_scores(self):
        g = self._make_grade(0, 0)
        self.assertEqual(g.total_score, Decimal('0'))
        self.assertEqual(g.grade, '9')

    # ── Custom grading scale override ────────────────────────
    def test_custom_scale_overrides_default(self):
        GradingScale.objects.create(min_score=90, grade_label='A+', remarks='Excellent', ordering=0)
        GradingScale.objects.create(min_score=70, grade_label='A', remarks='Very Good', ordering=1)
        GradingScale.objects.create(min_score=50, grade_label='B', remarks='Good', ordering=2)
        GradingScale.objects.create(min_score=0, grade_label='F', remarks='Fail', ordering=3)

        g = self._make_grade(25, 50)  # total = 75 → should hit A (≥70)
        self.assertEqual(g.grade, 'A')
        self.assertEqual(g.remarks, 'Very Good')

    def test_custom_scale_lowest_bucket(self):
        GradingScale.objects.create(min_score=50, grade_label='P', remarks='Pass', ordering=0)
        GradingScale.objects.create(min_score=0, grade_label='F', remarks='Fail', ordering=1)

        g = self._make_grade(10, 20)  # total = 30 → F
        self.assertEqual(g.grade, 'F')


@unittest.skipUnless(
    os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1',
    'Tenant integration tests are opt-in; set RUN_TENANT_INTEGRATION_TESTS=1 to execute.',
)
class FeeLogicTests(TenantTestCase):
    """StudentFee status transitions and Payment recording."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'Test School'
        tenant.school_type = 'basic'
        return tenant

    def setUp(self):
        connection.set_tenant(self.tenant)
        self.year = AcademicYear.objects.create(
            name='2025/2026', start_date=date(2025, 9, 1),
            end_date=date(2026, 7, 31), is_current=True,
        )
        self.cls = Class.objects.create(name='Basic 7A', academic_year=self.year)
        self.user = User.objects.create_user(
            username='stu_fee', password='pass', user_type='student',
        )
        self.student = Student.objects.create(
            user=self.user, current_class=self.cls,
            admission_number='FEE001', date_of_birth=date(2010, 1, 1),
        )
        self.admin = User.objects.create_user(
            username='admin1', password='pass', user_type='admin',
        )
        self.head = FeeHead.objects.create(name='Tuition')
        self.structure = FeeStructure.objects.create(
            head=self.head, academic_year=self.year,
            class_level=self.cls, term='first', amount=Decimal('500.00'),
        )
        self.fee = StudentFee.objects.create(
            student=self.student, fee_structure=self.structure,
            amount_payable=Decimal('500.00'),
        )

    def test_initial_status_unpaid(self):
        self.assertEqual(self.fee.status, 'unpaid')
        self.assertEqual(self.fee.total_paid, Decimal('0'))
        self.assertEqual(self.fee.balance, Decimal('500.00'))

    def test_partial_payment(self):
        Payment.objects.create(
            student_fee=self.fee, amount=Decimal('200.00'),
            date=date.today(), recorded_by=self.admin,
        )
        self.fee.refresh_from_db()
        self.assertEqual(self.fee.status, 'partial')
        self.assertEqual(self.fee.balance, Decimal('300.00'))

    def test_full_payment(self):
        Payment.objects.create(
            student_fee=self.fee, amount=Decimal('500.00'),
            date=date.today(), recorded_by=self.admin,
        )
        self.fee.refresh_from_db()
        self.assertEqual(self.fee.status, 'paid')
        self.assertEqual(self.fee.balance, Decimal('0.00'))

    def test_multiple_payments_sum(self):
        Payment.objects.create(
            student_fee=self.fee, amount=Decimal('100.00'),
            date=date.today(), recorded_by=self.admin,
        )
        Payment.objects.create(
            student_fee=self.fee, amount=Decimal('400.00'),
            date=date.today(), recorded_by=self.admin,
        )
        self.fee.refresh_from_db()
        self.assertEqual(self.fee.status, 'paid')
        self.assertEqual(self.fee.total_paid, Decimal('500.00'))

    def test_unique_reference_constraint(self):
        Payment.objects.create(
            student_fee=self.fee, amount=Decimal('100.00'),
            date=date.today(), recorded_by=self.admin, reference='REF-001',
        )
        with self.assertRaises(Exception):
            Payment.objects.create(
                student_fee=self.fee, amount=Decimal('100.00'),
                date=date.today(), recorded_by=self.admin, reference='REF-001',
            )


@unittest.skipUnless(
    os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1',
    'Tenant integration tests are opt-in; set RUN_TENANT_INTEGRATION_TESTS=1 to execute.',
)
class AttendanceTests(TenantTestCase):
    """Attendance marking and uniqueness."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'Test School'
        tenant.school_type = 'basic'
        return tenant

    def setUp(self):
        connection.set_tenant(self.tenant)
        self.year = AcademicYear.objects.create(
            name='2025/2026', start_date=date(2025, 9, 1),
            end_date=date(2026, 7, 31), is_current=True,
        )
        self.cls = Class.objects.create(name='Basic 7A', academic_year=self.year)
        self.user = User.objects.create_user(
            username='att_stu', password='pass', user_type='student',
        )
        self.student = Student.objects.create(
            user=self.user, current_class=self.cls,
            admission_number='ATT001', date_of_birth=date(2010, 1, 1),
        )
        self.teacher_user = User.objects.create_user(
            username='att_teacher', password='pass', user_type='teacher',
        )

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


@unittest.skipUnless(
    os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1',
    'Tenant integration tests are opt-in; set RUN_TENANT_INTEGRATION_TESTS=1 to execute.',
)
class PermissionBoundaryTests(TenantTestCase):
    """Role-based access control for key views."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'Test School'
        tenant.school_type = 'basic'
        return tenant

    def setUp(self):
        connection.set_tenant(self.tenant)
        self.year = AcademicYear.objects.create(
            name='2025/2026', start_date=date(2025, 9, 1),
            end_date=date(2026, 7, 31), is_current=True,
        )
        self.admin_user = User.objects.create_user(
            username='admin_perm', password='pass', user_type='admin',
        )
        self.teacher_user = User.objects.create_user(
            username='teacher_perm', password='pass', user_type='teacher',
        )
        self.student_user = User.objects.create_user(
            username='student_perm', password='pass', user_type='student',
        )
        self.parent_user = User.objects.create_user(
            username='parent_perm', password='pass', user_type='parent',
        )

    def _login_and_get(self, user, url_name, kwargs=None):
        from django.test import Client
        client = Client()
        client.force_login(user)
        from django.urls import reverse
        url = reverse(url_name, kwargs=kwargs)
        return client.get(url, HTTP_HOST='localhost')

    def test_student_cannot_access_mark_attendance(self):
        resp = self._login_and_get(self.student_user, 'students:mark_attendance')
        # Should redirect away with error
        self.assertIn(resp.status_code, [302, 403])

    def test_parent_cannot_access_mark_attendance(self):
        resp = self._login_and_get(self.parent_user, 'students:mark_attendance')
        self.assertIn(resp.status_code, [302, 403])

    def test_student_cannot_access_grading_scale(self):
        resp = self._login_and_get(self.student_user, 'academics:grading_scale')
        self.assertIn(resp.status_code, [302, 403])

    def test_admin_can_access_grading_scale(self):
        resp = self._login_and_get(self.admin_user, 'academics:grading_scale')
        self.assertIn(resp.status_code, [200, 302])


@unittest.skipUnless(
    os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1',
    'Tenant integration tests are opt-in; set RUN_TENANT_INTEGRATION_TESTS=1 to execute.',
)
class GradeRankingTests(TenantTestCase):
    """Subject ranking after grade save."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'Test School'
        tenant.school_type = 'basic'
        return tenant

    def setUp(self):
        connection.set_tenant(self.tenant)
        self.year = AcademicYear.objects.create(
            name='2025/2026', start_date=date(2025, 9, 1),
            end_date=date(2026, 7, 31), is_current=True,
        )
        self.cls = Class.objects.create(name='Basic 7A', academic_year=self.year)
        self.subject = Subject.objects.create(name='English', code='ENG01')

        self.students = []
        for i in range(3):
            u = User.objects.create_user(
                username=f'rank_stu{i}', password='pass', user_type='student',
                first_name=f'Student{i}',
            )
            s = Student.objects.create(
                user=u, current_class=self.cls,
                admission_number=f'RNK{i:03}', date_of_birth=date(2010, 1, 1),
            )
            self.students.append(s)

    def test_ranking_order(self):
        # Student 0: 90, Student 1: 60, Student 2: 80
        scores = [(30, 60), (20, 40), (25, 55)]
        for i, (cs, ex) in enumerate(scores):
            Grade.objects.create(
                student=self.students[i], subject=self.subject,
                academic_year=self.year, term='first',
                class_score=cs, exams_score=ex,
            )
        grades = list(Grade.objects.filter(
            subject=self.subject, academic_year=self.year, term='first',
        ).order_by('-total_score'))

        # Position 1: 90pts, Position 2: 80pts, Position 3: 60pts
        self.assertEqual(grades[0].subject_position, 1)
        self.assertEqual(grades[1].subject_position, 2)
        self.assertEqual(grades[2].subject_position, 3)


# ═══════════════════════════════════════════════════════════════
# VIEW ACCESS-CONTROL TESTS
# ═══════════════════════════════════════════════════════════════

_SKIP_MSG = 'Tenant integration tests are opt-in; set RUN_TENANT_INTEGRATION_TESTS=1 to execute.'


@unittest.skipUnless(os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1', _SKIP_MSG)
class DashboardAccessTests(TenantTestCase):
    """Each role can reach its dashboard and is blocked from others."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'Dashboard Test School'
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
        self.admin = User.objects.create_user(username='adm', password='pass', user_type='admin')
        self.teacher_user = User.objects.create_user(username='tch', password='pass', user_type='teacher')
        Teacher.objects.create(user=self.teacher_user, employee_id='T001')
        self.student_user = User.objects.create_user(username='stu', password='pass', user_type='student')
        Student.objects.create(
            user=self.student_user, current_class=self.cls,
            admission_number='DSH001', date_of_birth=date(2010, 1, 1),
        )
        self.parent_user = User.objects.create_user(username='par', password='pass', user_type='parent')
        self.client = TenantClient(self.tenant)

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
        # Student dashboard redirects to students:student_dashboard
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


@unittest.skipUnless(os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1', _SKIP_MSG)
class ParentViewTests(TenantTestCase):
    """Parent portal access control and data isolation."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'Parent Test School'
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

        self.parent_user = User.objects.create_user(username='parent1', password='pass', user_type='parent')
        self.child_user = User.objects.create_user(username='child1', password='pass', user_type='student')
        self.child = Student.objects.create(
            user=self.child_user, current_class=self.cls,
            admission_number='PAR001', date_of_birth=date(2012, 3, 15),
        )
        from parents.models import Parent
        self.parent = Parent.objects.create(user=self.parent_user, relation='Father')
        self.parent.children.add(self.child)

        # Other parent with their own child
        self.other_parent_user = User.objects.create_user(username='parent2', password='pass', user_type='parent')
        self.other_child_user = User.objects.create_user(username='child2', password='pass', user_type='student')
        self.other_child = Student.objects.create(
            user=self.other_child_user, current_class=self.cls,
            admission_number='PAR002', date_of_birth=date(2012, 5, 20),
        )
        self.other_parent = Parent.objects.create(user=self.other_parent_user, relation='Mother')
        self.other_parent.children.add(self.other_child)

        self.client = TenantClient(self.tenant)

    def test_parent_sees_own_children(self):
        self.client.force_login(self.parent_user)
        resp = self.client.get('/parents/children/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.child_user.first_name or self.child_user.username)

    def test_parent_cannot_see_other_child_details(self):
        self.client.force_login(self.parent_user)
        resp = self.client.get(f'/parents/children/{self.other_child.id}/')
        # Should redirect with "not your child" error
        self.assertEqual(resp.status_code, 302)

    def test_parent_can_see_own_child_details(self):
        self.client.force_login(self.parent_user)
        resp = self.client.get(f'/parents/children/{self.child.id}/')
        self.assertEqual(resp.status_code, 200)

    def test_student_cannot_access_parent_views(self):
        self.client.force_login(self.child_user)
        resp = self.client.get('/parents/children/')
        self.assertIn(resp.status_code, [302, 403])

    def test_parent_sees_child_fees(self):
        self.client.force_login(self.parent_user)
        resp = self.client.get(f'/parents/children/{self.child.id}/fees/')
        self.assertEqual(resp.status_code, 200)

    def test_parent_cannot_see_other_child_fees(self):
        self.client.force_login(self.parent_user)
        resp = self.client.get(f'/parents/children/{self.other_child.id}/fees/')
        self.assertIn(resp.status_code, [302, 403])


# ═══════════════════════════════════════════════════════════════
# RATE LIMITER TESTS
# ═══════════════════════════════════════════════════════════════

@unittest.skipUnless(os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1', _SKIP_MSG)
class LoginRateLimitTests(TenantTestCase):
    """Login rate limiting blocks brute-force attempts."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'Ratelimit School'
        tenant.school_type = 'basic'
        return tenant

    def setUp(self):
        connection.set_tenant(self.tenant)
        cache.clear()
        self.user = User.objects.create_user(username='rl_user', password='correctpass', user_type='admin')
        self.client = TenantClient(self.tenant)

    def test_valid_login_succeeds(self):
        resp = self.client.post('/login/', {'username': 'rl_user', 'password': 'correctpass'})
        self.assertEqual(resp.status_code, 302)  # redirect to dashboard

    def test_invalid_login_returns_200(self):
        resp = self.client.post('/login/', {'username': 'rl_user', 'password': 'wrongpass'})
        self.assertEqual(resp.status_code, 200)  # re-renders login

    def test_rate_limit_after_max_attempts(self):
        from accounts.ratelimit import LOGIN_MAX_ATTEMPTS
        for _ in range(LOGIN_MAX_ATTEMPTS):
            self.client.post('/login/', {'username': 'baduser', 'password': 'badpass'})
        # Next attempt should be blocked
        resp = self.client.post('/login/', {'username': 'baduser', 'password': 'badpass'})
        self.assertEqual(resp.status_code, 429)

    def test_successful_login_resets_counter(self):
        # Fail a few times
        for _ in range(3):
            self.client.post('/login/', {'username': 'rl_user', 'password': 'wrong'})
        # Now succeed
        resp = self.client.post('/login/', {'username': 'rl_user', 'password': 'correctpass'})
        self.assertEqual(resp.status_code, 302)
        # Counter should be reset — log out and try again
        self.client.logout()
        resp = self.client.post('/login/', {'username': 'rl_user', 'password': 'wrong'})
        self.assertEqual(resp.status_code, 200)  # Not 429


# ═══════════════════════════════════════════════════════════════
# STUDENT DASHBOARD TESTS
# ═══════════════════════════════════════════════════════════════

@unittest.skipUnless(os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1', _SKIP_MSG)
class StudentDashboardTests(TenantTestCase):
    """Student dashboard view returns correct context data."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'Student Dash School'
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
        self.student_user = User.objects.create_user(username='sdash', password='pass', user_type='student')
        self.student = Student.objects.create(
            user=self.student_user, current_class=self.cls,
            admission_number='SDASH01', date_of_birth=date(2011, 5, 10),
        )
        # Create some attendance
        for i in range(5):
            Attendance.objects.create(
                student=self.student,
                date=date.today() - timedelta(days=i + 1),
                status='present' if i < 4 else 'absent',
            )
        # Create a grade
        Grade.objects.create(
            student=self.student, subject=self.subject,
            academic_year=self.year, term='first',
            class_score=25, exams_score=55,
        )
        self.client = TenantClient(self.tenant)

    def test_student_dashboard_loads(self):
        self.client.force_login(self.student_user)
        resp = self.client.get('/students/dashboard/')
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_has_attendance_stats(self):
        self.client.force_login(self.student_user)
        resp = self.client.get('/students/dashboard/')
        self.assertIn('attendance_stats', resp.context)
        stats = resp.context['attendance_stats']
        self.assertEqual(stats['total'], 5)
        self.assertEqual(stats['present'], 4)
        self.assertEqual(stats['absent'], 1)

    def test_dashboard_has_subject_analytics(self):
        self.client.force_login(self.student_user)
        resp = self.client.get('/students/dashboard/')
        self.assertIn('subject_analytics', resp.context)
        analytics = resp.context['subject_analytics']
        self.assertEqual(len(analytics), 1)
        self.assertEqual(analytics[0]['name'], 'Math')

    def test_non_student_blocked(self):
        admin = User.objects.create_user(username='not_stu', password='pass', user_type='admin')
        self.client.force_login(admin)
        resp = self.client.get('/students/dashboard/')
        self.assertEqual(resp.status_code, 302)


# ═══════════════════════════════════════════════════════════════
# TENANT ISOLATION TESTS
# ═══════════════════════════════════════════════════════════════

@unittest.skipUnless(os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1', _SKIP_MSG)
class TenantIsolationTests(TenantTestCase):
    """Data created in one tenant schema must not leak into another."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'Isolation School'
        tenant.school_type = 'basic'
        return tenant

    def setUp(self):
        connection.set_tenant(self.tenant)
        cache.clear()

    def test_students_isolated_to_schema(self):
        """Students created in this schema exist here."""
        year = AcademicYear.objects.create(
            name='2025/2026', start_date=date(2025, 9, 1),
            end_date=date(2026, 7, 31), is_current=True,
        )
        cls = Class.objects.create(name='Basic 7A', academic_year=year)
        user = User.objects.create_user(username='iso_stu', password='pass', user_type='student')
        Student.objects.create(
            user=user, current_class=cls,
            admission_number='ISO001', date_of_birth=date(2010, 1, 1),
        )
        self.assertEqual(Student.objects.count(), 1)

    def test_grades_isolated_to_schema(self):
        """Grades in this schema don't see grades from other schemas."""
        self.assertEqual(Grade.objects.count(), 0)

    def test_fees_isolated_to_schema(self):
        """Fees in this schema start at zero."""
        self.assertEqual(StudentFee.objects.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)

    def test_academic_years_isolated(self):
        AcademicYear.objects.create(
            name='Test Year', start_date=date(2025, 9, 1),
            end_date=date(2026, 7, 31), is_current=True,
        )
        self.assertEqual(AcademicYear.objects.filter(is_current=True).count(), 1)


# ═══════════════════════════════════════════════════════════════
# API ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════

@unittest.skipUnless(os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1', _SKIP_MSG)
class APIEndpointTests(TenantTestCase):
    """REST API authentication and basic CRUD."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'API Test School'
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
        self.admin = User.objects.create_user(username='api_adm', password='pass', user_type='admin')
        self.student_user = User.objects.create_user(username='api_stu', password='pass', user_type='student')
        self.student = Student.objects.create(
            user=self.student_user, current_class=self.cls,
            admission_number='API001', date_of_birth=date(2010, 1, 1),
        )
        self.client = TenantClient(self.tenant)

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
# MODEL PROPERTY TESTS
# ═══════════════════════════════════════════════════════════════

@unittest.skipUnless(os.getenv('RUN_TENANT_INTEGRATION_TESTS') == '1', _SKIP_MSG)
class StudentFeePropertyTests(TenantTestCase):
    """StudentFee computed properties: total_paid, balance, update_status."""

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = 'Fee Property School'
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
        self.user = User.objects.create_user(username='fp_stu', password='pass', user_type='student')
        self.student = Student.objects.create(
            user=self.user, current_class=self.cls,
            admission_number='FP001', date_of_birth=date(2010, 1, 1),
        )
        self.admin = User.objects.create_user(username='fp_adm', password='pass', user_type='admin')
        head = FeeHead.objects.create(name='Tuition')
        structure = FeeStructure.objects.create(
            head=head, academic_year=self.year,
            class_level=self.cls, term='first', amount=Decimal('1000.00'),
        )
        self.fee = StudentFee.objects.create(
            student=self.student, fee_structure=structure,
            amount_payable=Decimal('1000.00'),
        )

    def test_balance_is_correct(self):
        self.assertEqual(self.fee.balance, Decimal('1000.00'))
        Payment.objects.create(
            student_fee=self.fee, amount=Decimal('300.00'),
            date=date.today(), recorded_by=self.admin,
        )
        self.assertEqual(self.fee.balance, Decimal('700.00'))

    def test_overpayment_does_not_crash(self):
        Payment.objects.create(
            student_fee=self.fee, amount=Decimal('1200.00'),
            date=date.today(), recorded_by=self.admin,
        )
        self.fee.refresh_from_db()
        self.assertEqual(self.fee.status, 'paid')
        self.assertEqual(self.fee.balance, Decimal('-200.00'))

    def test_payment_auto_generates_reference(self):
        p = Payment.objects.create(
            student_fee=self.fee, amount=Decimal('100.00'),
            date=date.today(), recorded_by=self.admin,
        )
        self.assertTrue(p.reference)
        self.assertGreater(len(p.reference), 5)
