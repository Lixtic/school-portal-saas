from django.contrib import admin
from .models import SMSMessage, EmailCampaign

@admin.register(SMSMessage)
class SMSMessageAdmin(admin.ModelAdmin):
    list_display = ('recipient_number', 'status', 'created_at', 'sent_by')
    list_filter = ('status', 'created_at')
    search_fields = ('recipient_number', 'message_body')

@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ('subject', 'recipient_group', 'status', 'created_at')
    list_filter = ('status', 'recipient_group')
