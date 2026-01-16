from django.contrib import admin
from django_tenants.admin import TenantAdminMixin

from tenants.models import (
    School, Domain, SubscriptionPlan, AddOn, 
    SchoolSubscription, SchoolAddOn, Invoice, ChurnEvent
)

@admin.register(School)
class SchoolAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'schema_name', 'created_on', 'on_trial', 'is_active')

@admin.register(Domain)
class DomainAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'monthly_price', 'max_students', 'is_active')
    list_filter = ('plan_type', 'is_active')
    search_fields = ('name', 'description')


@admin.register(AddOn)
class AddOnAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'monthly_price', 'is_one_time', 'is_active')
    list_filter = ('category', 'is_one_time', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(SchoolSubscription)
class SchoolSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('school', 'plan', 'status', 'billing_cycle', 'mrr', 'current_period_end')
    list_filter = ('status', 'billing_cycle', 'plan')
    search_fields = ('school__name',)
    readonly_fields = ('mrr', 'created_at', 'updated_at')


@admin.register(SchoolAddOn)
class SchoolAddOnAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'addon', 'is_active', 'purchased_at')
    list_filter = ('is_active', 'addon__category')
    search_fields = ('subscription__school__name', 'addon__name')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'subscription', 'total', 'status', 'issued_at', 'paid_at')
    list_filter = ('status',)
    search_fields = ('invoice_number', 'subscription__school__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ChurnEvent)
class ChurnEventAdmin(admin.ModelAdmin):
    list_display = ('school', 'reason', 'cancelled_at', 'lifetime_value', 'months_subscribed')
    list_filter = ('reason', 'cancelled_at')
    search_fields = ('school__name', 'reason_detail')
