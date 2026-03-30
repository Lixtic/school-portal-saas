from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from students.models import Student, Attendance, Grade
from academics.models import AcademicYear, Class, Subject
from finance.models import StudentFee, Payment
from teachers.models import Teacher

from .serializers import (
    AcademicYearSerializer, ClassSerializer, SubjectSerializer,
    StudentSerializer, AttendanceSerializer, GradeSerializer,
    TeacherSerializer, StudentFeeSerializer, PaymentSerializer,
)


class IsAdminOrTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type in ('admin', 'teacher')


class IsAdminOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'admin'


class AcademicYearViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AcademicYearSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AcademicYear.objects.all()


class ClassViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ClassSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Class.objects.select_related('class_teacher__user')
        year = self.request.query_params.get('year')
        if year:
            qs = qs.filter(academic_year_id=year)
        else:
            qs = qs.filter(academic_year__is_current=True)
        return qs


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Subject.objects.all()


class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrTeacher]

    def get_queryset(self):
        qs = Student.objects.select_related('user', 'current_class')
        class_id = self.request.query_params.get('class_id')
        if class_id:
            qs = qs.filter(current_class_id=class_id)
        return qs


class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAdminOrTeacher]

    def get_queryset(self):
        qs = Attendance.objects.select_related('student__user')
        date = self.request.query_params.get('date')
        class_id = self.request.query_params.get('class_id')
        if date:
            qs = qs.filter(date=date)
        if class_id:
            qs = qs.filter(student__current_class_id=class_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(marked_by=self.request.user)


class GradeViewSet(viewsets.ModelViewSet):
    serializer_class = GradeSerializer
    permission_classes = [IsAdminOrTeacher]

    def get_queryset(self):
        qs = Grade.objects.select_related('student__user', 'subject', 'academic_year')
        class_id = self.request.query_params.get('class_id')
        term = self.request.query_params.get('term')
        subject_id = self.request.query_params.get('subject_id')
        if class_id:
            qs = qs.filter(student__current_class_id=class_id)
        if term:
            qs = qs.filter(term=term)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        return qs.filter(academic_year__is_current=True)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TeacherSerializer
    permission_classes = [IsAdminOnly]

    def get_queryset(self):
        return Teacher.objects.select_related('user')


class StudentFeeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StudentFeeSerializer
    permission_classes = [IsAdminOrTeacher]

    def get_queryset(self):
        qs = StudentFee.objects.select_related('fee_structure__head', 'student__user')
        student_id = self.request.query_params.get('student_id')
        status = self.request.query_params.get('status')
        if student_id:
            qs = qs.filter(student_id=student_id)
        if status:
            qs = qs.filter(status=status)
        return qs


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminOrTeacher]

    def get_queryset(self):
        qs = Payment.objects.select_related('student_fee__student__user')
        fee_id = self.request.query_params.get('fee_id')
        if fee_id:
            qs = qs.filter(student_fee_id=fee_id)
        return qs
