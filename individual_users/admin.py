from django.contrib import admin
from individual_users.models import AddonSubscription, APIKey, IndividualAddon, IndividualProfile


@admin.register(IndividualAddon)
class IndividualAddonAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'category', 'audience', 'is_active', 'position', 'updated_at')
    list_filter = ('category', 'audience', 'is_active')
    list_editable = ('is_active', 'position')
    search_fields = ('name', 'slug', 'tagline')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('position', 'category', 'name')


@admin.register(IndividualProfile)
class IndividualProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'company', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number', 'company')
    list_filter = ('created_at',)
    raw_id_fields = ('user',)


@admin.register(AddonSubscription)
class AddonSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('profile', 'addon_name', 'plan', 'status', 'started_at', 'expires_at')
    list_filter = ('plan', 'status', 'addon_slug')
    search_fields = ('profile__user__username', 'addon_name')


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'profile', 'prefix', 'is_active', 'calls_total', 'last_used_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'prefix', 'profile__user__username')
    readonly_fields = ('prefix', 'hashed_key', 'calls_today', 'calls_total')
