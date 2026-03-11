"""
Management command: seed_addons

Idempotently creates (or updates) the canonical marketplace add-on records
that correspond to the gated features in the codebase.

Run once after migrations:
    python manage.py seed_addons
"""

from django.core.management.base import BaseCommand
from tenants.subscription_models import AddOn


ADDONS = [
    # ── AI & Automation ───────────────────────────────────────────────────
    {
        'slug': 'ai-admissions-assistant',
        'name': 'AI Admissions Assistant',
        'category': 'ai',
        'description': (
            'A 24/7 AI-powered chatbot embedded on your school homepage that '
            'answers prospective parents\' questions about fees, term dates, '
            'admissions requirements, and more. Powered by OpenAI.'
        ),
        'icon': 'bi-robot',
        'monthly_price': '9.99',
        'is_one_time': False,
        'available_for_plans': ['basic', 'pro', 'enterprise'],
    },
    {
        'slug': 'ai-lesson-planner',
        'name': 'AI Lesson Planner (Aura-T)',
        'category': 'ai',
        'description': (
            'Generate full lesson plans, activity ideas, and assessment '
            'questions in seconds using AI. Teachers get an interactive '
            'Copilot session workspace with history and export.'
        ),
        'icon': 'bi-stars',
        'monthly_price': '14.99',
        'is_one_time': False,
        'available_for_plans': ['basic', 'pro', 'enterprise'],
    },
    # ── Premium Features ──────────────────────────────────────────────────
    {
        'slug': 'presentations',
        'name': 'Teacher Presentations',
        'category': 'feature',
        'description': (
            'Create, edit, and deliver rich slide presentations directly '
            'in the platform. Full-screen presenter mode with speaker notes, '
            'laser pointer, drawing overlay, and QR share code.'
        ),
        'icon': 'bi-easel2',
        'monthly_price': '4.99',
        'is_one_time': False,
        'available_for_plans': ['basic', 'pro', 'enterprise'],
    },
    # ── Analytics & Reporting ─────────────────────────────────────────────
    {
        'slug': 'advanced-analytics',
        'name': 'Advanced Analytics',
        'category': 'analytics',
        'description': (
            'Deep-dive school analytics: enrollment trends, fee collection '
            'summary, 30-day attendance heatmap, grade distribution charts, '
            'and recent payment activity — all in one dashboard.'
        ),
        'icon': 'bi-bar-chart-line',
        'monthly_price': '7.99',
        'is_one_time': False,
        'available_for_plans': ['basic', 'pro', 'enterprise'],
    },
    # ── Communication ─────────────────────────────────────────────────────
    {
        'slug': 'fee-email-reminders',
        'name': 'Parent Fee Email Reminders',
        'category': 'communication',
        'description': (
            'Automatically email parents when their ward has an unpaid or '
            'overdue fee balance. Includes a branded HTML email template '
            'with itemised fee summary and due-date urgency escalation.'
        ),
        'icon': 'bi-envelope-check',
        'monthly_price': '3.99',
        'is_one_time': False,
        'available_for_plans': ['basic', 'pro', 'enterprise'],
    },
    {
        'slug': 'web-push-notifications',
        'name': 'Web Push Notifications',
        'category': 'communication',
        'description': (
            'Send real-time browser push notifications to students, teachers, '
            'and parents — even when they\'re not on the portal. '
            'Uses VAPID for secure, standards-based delivery.'
        ),
        'icon': 'bi-bell-fill',
        'monthly_price': '4.99',
        'is_one_time': False,
        'available_for_plans': ['basic', 'pro', 'enterprise'],
    },
    # ── Integrations ──────────────────────────────────────────────────────
    {
        'slug': 'online-payments',
        'name': 'Online Fee Payments (Paystack)',
        'category': 'integration',
        'description': (
            'Let parents and students pay school fees online via card, '
            'mobile money, or bank transfer through Paystack. '
            'Payments auto-reconcile against student fee records.'
        ),
        'icon': 'bi-credit-card',
        'monthly_price': '12.99',
        'is_one_time': False,
        'available_for_plans': ['basic', 'pro', 'enterprise'],
    },
    # ── Storage & Resources ───────────────────────────────────────────────
    {
        'slug': 'resource-library',
        'name': 'Resource Library',
        'category': 'storage',
        'description': (
            'Upload and share teaching resources — worksheets, past papers, '
            'videos, and documents — organised by subject and class. '
            'Students and teachers can download from a searchable library.'
        ),
        'icon': 'bi-folder2-open',
        'monthly_price': '4.99',
        'is_one_time': False,
        'available_for_plans': ['basic', 'pro', 'enterprise'],
    },
    {
        'slug': 'school-gallery',
        'name': 'School Gallery & Media Hub',
        'category': 'storage',
        'description': (
            'A public-facing photo gallery for events, graduations, sports '
            'days, and more. Categorised albums with Cloudinary CDN delivery '
            'for fast, high-quality image viewing.'
        ),
        'icon': 'bi-images',
        'monthly_price': '2.99',
        'is_one_time': False,
        'available_for_plans': ['basic', 'pro', 'enterprise'],
    },
]


class Command(BaseCommand):
    help = 'Idempotently seed marketplace add-on records.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing records (name, description, price, icon). '
                 'By default already-existing slugs are left unchanged.',
        )

    def handle(self, *args, **options):
        update = options['update']
        created_count = 0
        updated_count = 0

        for data in ADDONS:
            slug = data['slug']
            defaults = {k: v for k, v in data.items() if k != 'slug'}

            if update:
                obj, created = AddOn.objects.update_or_create(slug=slug, defaults=defaults)
            else:
                obj, created = AddOn.objects.get_or_create(slug=slug, defaults=defaults)

            if created:
                created_count += 1
                self.stdout.write(f'  Created  → {obj.name}')
            elif update:
                updated_count += 1
                self.stdout.write(f'  Updated  → {obj.name}')
            else:
                self.stdout.write(f'  Skipped  → {obj.name} (already exists)')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. {created_count} created, {updated_count} updated, '
                f'{len(ADDONS) - created_count - updated_count} skipped.'
            )
        )
