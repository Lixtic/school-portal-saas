from django.contrib import admin
from .models import Homework

@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ['title', 'target_class', 'subject', 'due_date', 'teacher', 'created_at']
    list_filter = ['target_class', 'subject', 'due_date', 'created_at']
    search_fields = ['title', 'description']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
