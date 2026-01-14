 #parents/admin.py
from django.contrib import admin
from .models import Parent

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):

    list_display = ['get_full_name', 'relation', 'occupation', 'get_phone']
    search_fields = ['user__first_name', 'user__last_name']
    list_filter = ['relation']
    filter_horizontal = ['children']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'
    
    def get_phone(self, obj):
        return obj.user.phone
    get_phone.short_description = 'Phone'
