from django.contrib import admin
from .models import Vendor, ExpenseCategory, Expense, Asset

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type', 'phone', 'contact_person')
    search_fields = ('name', 'service_type')

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'category', 'date', 'vendor')
    list_filter = ('category', 'date')
    search_fields = ('title', 'description')

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'location', 'condition')
    list_filter = ('condition', 'category')
    search_fields = ('name', 'code')
