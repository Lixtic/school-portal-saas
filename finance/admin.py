from django.contrib import admin
from .models import FeeHead, FeeStructure, StudentFee, Payment

@admin.register(FeeHead)
class FeeHeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('head', 'class_level', 'term', 'academic_year', 'amount')
    list_filter = ('term', 'academic_year', 'class_level')
    search_fields = ('head__name', 'class_level__name')

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('date', 'recorded_by', 'created_at')

@admin.register(StudentFee)
class StudentFeeAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_structure', 'amount_payable', 'total_paid', 'balance', 'status')
    list_filter = ('status', 'fee_structure__term', 'fee_structure__academic_year', 'fee_structure__class_level')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'student__admission_number')
    inlines = [PaymentInline]
    readonly_fields = ('total_paid', 'balance')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student_fee', 'amount', 'date', 'method', 'reference', 'recorded_by')
    list_filter = ('method', 'date')
    search_fields = ('student_fee__student__user__first_name', 'reference')
    autocomplete_fields = ['student_fee']