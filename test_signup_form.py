#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from tenants.forms import SchoolSignupForm

# Test form initialization
form = SchoolSignupForm()
print("✅ Form initialized successfully")
print(f"Total fields: {len(form.fields)}")
print(f"\nAll fields: {list(form.fields.keys())}")
print(f"\nRequired fields: {[f for f, field in form.fields.items() if field.required]}")
print(f"\nOptional fields: {[f for f, field in form.fields.items() if not field.required]}")
