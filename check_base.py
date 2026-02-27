import os
import django
from django.template import Template, Context
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school_system.settings")
django.setup()

try:
    with open('templates/base.html', 'r', encoding='utf-8') as f:
        template_string = f.read()
    t = Template(template_string)
    print("Template syntax OK")
except Exception as e:
    print(f"Template syntax error: {e}")
