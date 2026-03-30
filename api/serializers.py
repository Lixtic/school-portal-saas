from rest_framework import serializers
from students.models import Student, Attendance, Grade
from academics.models import AcademicYear, Class, Subject, ClassSubject
from finance.models import FeeHead, FeeStructure, StudentFee, Payment
from teachers.models import Teacher


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ['id', 'name', 'start_date', 'end_date', 'is_current']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code']


class ClassSerializer(serializers.ModelSerializer):
    class_teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = ['id', 'name', 'academic_year', 'class_teacher', 'class_teacher_name']

    def get_class_teacher_name(self, obj):
        if obj.class_teacher:
            return obj.class_teacher.user.get_full_name()
        return None


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    class_name = serializers.CharField(source='current_class.name', default=None)

    class Meta:
        model = Student
        fields = [
            'id', 'full_name', 'admission_number', 'class_name',
            'date_of_birth', 'gender', 'emergency_contact',
        ]

    def get_full_name(self, obj):
        return obj.user.get_full_name()


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'student', 'student_name', 'date', 'status', 'remarks']
        read_only_fields = ['id']


class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = Grade
        fields = [
            'id', 'student', 'student_name', 'subject', 'subject_name',
            'academic_year', 'term', 'class_score', 'exams_score',
            'total_score', 'grade', 'remarks', 'subject_position',
        ]
        read_only_fields = ['id', 'total_score', 'grade', 'remarks', 'subject_position']


class TeacherSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Teacher
        fields = ['id', 'full_name', 'email', 'phone', 'qualification']

    def get_full_name(self, obj):
        return obj.user.get_full_name()


class FeeHeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeHead
        fields = ['id', 'name', 'description']


class StudentFeeSerializer(serializers.ModelSerializer):
    fee_name = serializers.CharField(source='fee_structure.head.name', read_only=True)
    total_paid = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()

    class Meta:
        model = StudentFee
        fields = ['id', 'student', 'fee_name', 'amount_payable', 'status', 'total_paid', 'balance']
        read_only_fields = ['id', 'status']

    def get_total_paid(self, obj):
        return str(obj.total_paid)

    def get_balance(self, obj):
        return str(obj.balance)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'student_fee', 'amount', 'date', 'reference', 'method', 'remarks']
        read_only_fields = ['id', 'reference']
