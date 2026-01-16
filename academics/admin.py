from django.contrib import admin
from .models import AcademicYear, Class, Subject, ClassSubject, Activity, Timetable, SchoolInfo, GalleryImage


def _reset_broken_transaction():
    """Best-effort rollback to clear aborted transaction state without requiring atomic."""
    from django.db import connection

    try:
        connection.rollback()
    except Exception:
        # If rollback fails, close the connection to force a clean one on next access
        connection.close()

    # Ensure we have a usable connection for the next query
    try:
        connection.ensure_connection()
    except Exception:
        # If ensure_connection fails, close to force recreation on next access
        connection.close()

@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'caption']

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current']
    list_editable = ['is_current']

@admin.register(SchoolInfo)
class SchoolInfoAdmin(admin.ModelAdmin):
    # Only allow one instance
    def has_add_permission(self, request):
        try:
            if self.model.objects.exists():
                return False
            return True
        except Exception:
            # If the DB transaction is broken, reset it and deny add to keep admin usable
            _reset_broken_transaction()
            return False

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_year', 'class_teacher']
    list_filter = ['academic_year']
    search_fields = ['name']

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']
    search_fields = ['code', 'name']

@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ['class_name', 'subject', 'teacher']
    list_filter = ['class_name', 'subject']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'tag', 'is_active']
    list_filter = ['is_active', 'tag']
    search_fields = ['title', 'summary', 'tag']
    filter_horizontal = ['assigned_staff']


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ['class_subject', 'day', 'start_time', 'end_time', 'room']
    list_filter = ['day', 'class_subject__class_name']
    search_fields = ['class_subject__teacher__user__first_name', 'class_subject__teacher__user__last_name', 'room']

    def get_deleted_objects(self, objs, request):
        """
        Override to handle missing announcements_notification table during preview.
        """
        from django.db import ProgrammingError, connection, transaction
        
        try:
            return super().get_deleted_objects(objs, request)
        except ProgrammingError as e:
            if 'announcements_notification' in str(e):
                # Rollback the broken transaction in Postgres
                _reset_broken_transaction()
                
                # Return a simplified preview without checking cascade deletes
                deleted_objects = [f"Timetable #{obj.id}" for obj in objs]
                model_count = {self.model._meta.verbose_name_plural: len(objs)}
                perms_needed = set()
                protected = []
                
                return (deleted_objects, model_count, perms_needed, protected)
            else:
                raise e

    def delete_queryset(self, request, queryset):
        """
        Override bulk delete to handle missing announcements_notification table gracefully.
        """
        from django.db import connection, ProgrammingError, transaction
        
        try:
            # Try standard bulk delete first
            queryset.delete()
        except ProgrammingError as e:
            if 'announcements_notification' in str(e):
                # Clear broken transaction state
                _reset_broken_transaction()
                
                # Fallback: Raw SQL delete ignoring cascade to missing table
                ids = list(queryset.values_list('id', flat=True))
                if not ids:
                    return

                with connection.cursor() as cursor:
                    # Format tuple of IDs for SQL IN clause
                    placeholders = ', '.join(['%s'] * len(ids))
                    sql = f"DELETE FROM academics_timetable WHERE id IN ({placeholders})"
                    cursor.execute(sql, ids)
                
                self.message_user(request, f"Successfully deleted {len(ids)} timetables (Force Delete Mode)", level="WARNING")
            else:
                raise e

    def delete_model(self, request, obj):
        """
        Override single instance delete to handle missing announcements_notification table gracefully.
        """
        from django.db import connection, ProgrammingError, transaction
        
        try:
            obj.delete()
        except ProgrammingError as e:
            if 'announcements_notification' in str(e):
                # Clear broken transaction state
                _reset_broken_transaction()
                
                # Fallback: Raw SQL delete within a new savepoint
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM academics_timetable WHERE id = %s", [obj.id])
            else:
                raise e

    def delete_view(self, request, object_id, extra_context=None):
        """
        Override delete view to force-delete when the notifications table is missing.
        This avoids repeated transaction aborts during the standard admin flow.
        """
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        from django.db import transaction, connection, ProgrammingError

        # Clear any broken transaction flag before proceeding
        _reset_broken_transaction()

        try:
            return super().delete_view(request, object_id, extra_context=extra_context)
        except Exception as e:
            # Any failure (missing table or closed connection): reset and force delete
            _reset_broken_transaction()
            try:
                connection.ensure_connection()
            except Exception:
                connection.close()
                connection.ensure_connection()

            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM academics_timetable WHERE id = %s", [object_id])

            self.message_user(request, f"Force-deleted timetable #{object_id} (fallback)", level="WARNING")
            return HttpResponseRedirect(reverse('admin:academics_timetable_changelist'))


# AI Tutor Admin
from .models import TutorSession, TutorMessage, PracticeQuestionSet

@admin.register(TutorSession)
class TutorSessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'started_at', 'message_count')
    list_filter = ('subject', 'started_at')
    search_fields = ('student__user__first_name', 'student__user__last_name')
    readonly_fields = ('started_at', 'ended_at')


@admin.register(TutorMessage)
class TutorMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'role', 'created_at', 'content_preview')
    list_filter = ('role', 'created_at')
    search_fields = ('content',)
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'


@admin.register(PracticeQuestionSet)
class PracticeQuestionSetAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'topic', 'difficulty', 'generated_at', 'score')
    list_filter = ('subject', 'difficulty', 'generated_at')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'topic')
    readonly_fields = ('generated_at',)
