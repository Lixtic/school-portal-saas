from django.contrib import admin
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect


class SchoolAdminSite(admin.AdminSite):
    """Custom admin site with proper logout handling for Django 5+"""
    site_header = "School Portal Administration"
    site_title = "School Admin"
    index_title = "Welcome to School Management System"
    
    def logout(self, request, extra_context=None):
        """Handle logout - support both GET and POST for backwards compatibility"""
        auth_logout(request)
        # Redirect to login page
        return redirect('login')


# Replace the default admin site
admin.site = SchoolAdminSite()
admin.sites.site = admin.site