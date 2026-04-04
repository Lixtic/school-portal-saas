"""
Seed the IndividualAddon table from the hardcoded TEACHER_ADDON_CATALOG + ADDON_CATALOG.
Run:  python scripts/seed_individual_addons.py
"""
import os, sys, django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.db import connection
connection.set_schema_to_public()

from individual_users.models import IndividualAddon
from individual_users.views import TEACHER_ADDON_CATALOG, ADDON_CATALOG


def seed():
    created = 0
    updated = 0

    # Teacher catalog takes priority (has features/taglines)
    teacher_slugs = {a['slug'] for a in TEACHER_ADDON_CATALOG}

    for i, item in enumerate(TEACHER_ADDON_CATALOG):
        obj, was_created = IndividualAddon.objects.update_or_create(
            slug=item['slug'],
            defaults={
                'name': item['name'],
                'tagline': item.get('tagline', ''),
                'description': item.get('description', ''),
                'category': item.get('category', 'productivity'),
                'audience': 'teacher',
                'icon': item.get('icon', 'bi-box-seam'),
                'badge_label': item.get('badge', ''),
                'plans': item.get('plans', ['free']),
                'prices': item.get('prices', {}),
                'features': item.get('features', []),
                'trial_days': 0,
                'position': i,
                'is_active': True,
            },
        )
        if was_created:
            created += 1
        else:
            updated += 1

    # Developer-focused addons that aren't already in teacher catalog
    for i, item in enumerate(ADDON_CATALOG):
        if item['slug'] in teacher_slugs:
            continue
        obj, was_created = IndividualAddon.objects.update_or_create(
            slug=item['slug'],
            defaults={
                'name': item['name'],
                'tagline': item.get('tagline', ''),
                'description': item.get('description', ''),
                'category': item.get('category', 'productivity'),
                'audience': 'developer',
                'icon': item.get('icon', 'bi-box-seam'),
                'badge_label': item.get('badge', ''),
                'plans': item.get('plans', ['free']),
                'prices': item.get('prices', {}),
                'features': item.get('features', []),
                'trial_days': 0,
                'position': 100 + i,
                'is_active': True,
            },
        )
        if was_created:
            created += 1
        else:
            updated += 1

    print(f"Done. Created: {created}, Updated: {updated}, Total: {IndividualAddon.objects.count()}")


if __name__ == '__main__':
    seed()
