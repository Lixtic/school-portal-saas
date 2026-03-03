from django.contrib import admin
from .models import Student, Attendance, Grade
from .forms import StudentQuickAddForm

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'get_full_name', 'gender', 'current_class', 'roll_number', 'preferred_language']
    search_fields = ['admission_number', 'user__first_name', 'user__last_name']
    list_filter = ['current_class', 'date_of_admission', 'gender', 'preferred_language']

    fieldsets = (
        (None, {
            'fields': ('user', 'admission_number', 'roll_number', 'current_class', 'date_of_admission',
                       'date_of_birth', 'gender', 'blood_group', 'emergency_contact')
        }),
        ('Location & Background', {
            'fields': ('region', 'city', 'curriculum', 'interests'),
        }),
        ('Aura AI Profile', {
            'description': (
                'These fields personalise Aura\'s vocabulary, accent style, and teaching approach '
                'for this student. The more detail you provide, the more tailored Aura becomes.'
            ),
            'fields': ('preferred_language', 'aura_notes'),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        # For new students, present a minimal quick-add form
        if obj is None:
            defaults = {'form': StudentQuickAddForm}
            defaults.update(kwargs)
            return super().get_form(request, obj, **defaults)
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        # For the quick-add form, the form handles the full save
        if isinstance(form, StudentQuickAddForm) and not change:
            # Form already saved everything in form.save()
            return
        super().save_model(request, obj, form, change)
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'marked_by']
    list_filter = ['status', 'date']
    search_fields = ['student__user__first_name', 'student__user__last_name']
    date_hierarchy = 'date'


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'term', 'class_score', 'exams_score', 
                    'total_score', 'grade', 'subject_position', 'remarks']
    list_filter = ['academic_year', 'term', 'subject', 'grade']
    search_fields = ['student__user__first_name', 'student__user__last_name']
    readonly_fields = ['total_score', 'grade', 'remarks', 'subject_position']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'subject', 'academic_year', 'term')
        }),
        ('Scores', {
            'fields': ('class_score', 'exams_score')
        }),
        ('Auto-Calculated Results', {
            'fields': ('total_score', 'grade', 'remarks', 'subject_position'),
            'classes': ('collapse',)
        }),
        ('Meta', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        })
    )