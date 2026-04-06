"""Seed Day 1-2 social media posts + in-app promo banner from Content Creator agent."""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
django.setup()

from django.db import connection
from tenants.models import SocialMediaPost, PromoBanner

connection.set_schema_to_public()

SIGNUP_LINK = '/signup/'
CAMPAIGN = '7-Day Launch Campaign'

DAY1_THEME = 'Intro / value prop'
DAY2_THEME = 'Attendance & parent communication'

POSTS = [
    # ── Day 1 ──────────────────────────────────────
    {
        'day': 1, 'campaign': CAMPAIGN, 'theme': DAY1_THEME,
        'platform': 'linkedin',
        'headline': 'Digitise your school in weeks — not months.',
        'copy': (
            'SchoolPadi helps busy heads and admins run attendance, fees, '
            'communication and reports in one simple platform. Less paperwork, '
            'faster decisions, happier parents and teachers.\n\n'
            'Want a smooth rollout your staff will actually use?'
        ),
        'cta': 'Book a 15-min demo',
        'cta_link': SIGNUP_LINK,
        'image_note': 'Smiling admin at desk using laptop; SchoolPadi dashboard overlay.',
        'hashtags': '#SchoolPadi #EdTech #SchoolLeadership #SchoolAdmin',
    },
    {
        'day': 1, 'campaign': CAMPAIGN, 'theme': DAY1_THEME,
        'platform': 'x',
        'hook': 'Running a school shouldn\u2019t mean drowning in paperwork.',
        'copy': (
            'SchoolPadi centralises attendance, fees, communication & reports '
            '\u2014 simple, secure, trusted by schools.\n\n'
            'See it in 15 mins.'
        ),
        'cta': 'See it in 15 mins',
        'cta_link': SIGNUP_LINK,
        'hashtags': '#EdTech #SchoolManagement',
    },
    {
        'day': 1, 'campaign': CAMPAIGN, 'theme': DAY1_THEME,
        'platform': 'instagram',
        'copy': (
            'Meet SchoolPadi \u2014 the simple app that helps schools track attendance, '
            'manage fees, and keep parents in the loop.\n\n'
            'Less admin, more time for teaching.\n\n'
            'Tap the link in bio to book a demo. \U0001f469\u200d\U0001f3eb\U0001f4da'
        ),
        'cta': 'Link in bio',
        'cta_link': SIGNUP_LINK,
        'image_note': 'Carousel: 1) headline card, 2) dashboard screenshot, 3) smiling teacher with tablet.',
        'hashtags': '#SchoolPadi #TeachersOfInstagram #SchoolLife',
    },

    # ── Day 2 ──────────────────────────────────────
    {
        'day': 2, 'campaign': CAMPAIGN, 'theme': DAY2_THEME,
        'platform': 'linkedin',
        'headline': 'Reduce absenteeism with real-time attendance alerts.',
        'copy': (
            'Missing students create learning gaps. SchoolPadi sends instant parent alerts, '
            'generates attendance reports and highlights trends so you can intervene early.\n\n'
            'Schools see improved punctuality and stronger parent engagement.'
        ),
        'cta': 'Request a case study',
        'cta_link': SIGNUP_LINK,
        'image_note': 'Dashboard attendance heatmap + parent SMS mockup.',
        'hashtags': '#Attendance #ParentEngagement #EdTech',
    },
    {
        'day': 2, 'campaign': CAMPAIGN, 'theme': DAY2_THEME,
        'platform': 'x',
        'hook': 'Instant attendance alerts = faster follow-ups.',
        'copy': (
            'Use SchoolPadi to notify parents automatically, track trends, '
            'and reduce unexplained absences.'
        ),
        'cta': 'Learn how',
        'cta_link': SIGNUP_LINK,
        'hashtags': '#SchoolAdmin #EdTech',
    },
    {
        'day': 2, 'campaign': CAMPAIGN, 'theme': DAY2_THEME,
        'platform': 'instagram',
        'copy': (
            'Say goodbye to manual registers.\n\n'
            'With SchoolPadi, teachers mark attendance in seconds and parents '
            'get automatic alerts \u2014 keeping everyone informed.\n\n'
            'Want to try? Link in bio.'
        ),
        'cta': 'Link in bio',
        'cta_link': SIGNUP_LINK,
        'image_note': 'Short video/GIF of teacher tapping to mark attendance; animated parent notification.',
        'hashtags': '#SchoolPadi #ParentCommunication #TeachersOfInstagram',
    },
]

# ── Seed posts ──
created = 0
for data in POSTS:
    obj, was_created = SocialMediaPost.objects.get_or_create(
        day=data['day'],
        platform=data['platform'],
        campaign=data['campaign'],
        defaults={
            'theme': data['theme'],
            'headline': data.get('headline', ''),
            'hook': data.get('hook', ''),
            'copy': data['copy'],
            'cta': data.get('cta', ''),
            'cta_link': data.get('cta_link', ''),
            'image_note': data.get('image_note', ''),
            'hashtags': data.get('hashtags', ''),
            'source_agent': 'content',
        },
    )
    if was_created:
        created += 1

print(f'Social media posts: {created} created, {len(POSTS) - created} already existed.')

# ── In-app promo banner ──
banner, b_created = PromoBanner.objects.get_or_create(
    headline='Digitise your school in weeks — not months.',
    defaults={
        'body': 'Run attendance, fees, communication & reports in one simple platform. Book a 15-min demo.',
        'cta_text': 'Book a Demo',
        'cta_link': SIGNUP_LINK,
        'style': 'gradient',
        'audience': 'all',
        'is_active': True,
        'source_agent': 'content',
    },
)
print(f'Promo banner: {"created" if b_created else "already exists"} — "{banner.headline}"')
