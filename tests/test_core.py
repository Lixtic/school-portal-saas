"""
Core business logic tests.
Opt-in: set RUN_TENANT_INTEGRATION_TESTS=1 to execute.

  $env:RUN_TENANT_INTEGRATION_TESTS='1'; python manage.py test tests.test_core -v2
"""
import os
import unittest
from datetime import date
from decimal import Decimal

from django.db import connection
from django.test import RequestFactory
from django_tenants.test.cases import TenantTestCase

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
            target_class=self.cls, term='first', amount=Decimal('500.00'),
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
