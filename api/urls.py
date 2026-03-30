from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'academic-years', views.AcademicYearViewSet, basename='academic-year')
router.register(r'classes', views.ClassViewSet, basename='class')
router.register(r'subjects', views.SubjectViewSet, basename='subject')
router.register(r'students', views.StudentViewSet, basename='student')
router.register(r'attendance', views.AttendanceViewSet, basename='attendance')
router.register(r'grades', views.GradeViewSet, basename='grade')
router.register(r'teachers', views.TeacherViewSet, basename='teacher')
router.register(r'fees', views.StudentFeeViewSet, basename='fee')
router.register(r'payments', views.PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
]
