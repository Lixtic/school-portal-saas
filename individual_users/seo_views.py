"""
SEO views: XML sitemap, robots.txt, and visual HTML sitemap.

Generates a dynamic sitemap covering:
  - Public storefront pages (home, about, pricing, blog, etc.)
  - Guest curriculum catalog (subject + strand detail pages)
  - Guest AI demo lab
  - City landing pages
  - Visual HTML sitemap as a signup funnel
"""
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from datetime import date

from .guest_views import GES_CURRICULUM
from accounts.views import GHANA_CITIES


def _base_url(request):
    """Return the site root (scheme + host) without trailing slash."""
    return f"{request.scheme}://{request.headers.get('Host', 'schoolpadi.xyz')}"


def sitemap_xml(request):
    """Dynamic XML sitemap covering all public, guest, and SEO pages."""
    base = _base_url(request)
    today = date.today().isoformat()

    urls = []

    # ── Phase 1: Public storefront ──────────────────────────────────────
    static_pages = [
        ('/', '1.0', 'weekly'),
        ('/about/', '0.6', 'monthly'),
        ('/contact/', '0.5', 'monthly'),
        ('/pricing/', '0.9', 'weekly'),
        ('/compare/', '0.7', 'monthly'),
        ('/nacca-resources/', '0.8', 'weekly'),
        ('/get-started/', '0.8', 'monthly'),
        ('/privacy/', '0.3', 'yearly'),
        ('/terms/', '0.3', 'yearly'),
        ('/schools-in/', '0.7', 'weekly'),
        ('/sitemap/', '0.4', 'monthly'),
        ('/blog/', '0.7', 'weekly'),
        ('/login/', '0.5', 'monthly'),
    ]
    for loc, priority, freq in static_pages:
        urls.append(
            f'  <url>\n'
            f'    <loc>{base}{loc}</loc>\n'
            f'    <lastmod>{today}</lastmod>\n'
            f'    <changefreq>{freq}</changefreq>\n'
            f'    <priority>{priority}</priority>\n'
            f'  </url>'
        )

    # ── Blog posts ──────────────────────────────────────────────────────
    blog_slugs = ['grade-management', 'fee-tracking', 'attendance-system', 'ai-engine']
    for slug in blog_slugs:
        urls.append(
            f'  <url>\n'
            f'    <loc>{base}/blog/{slug}/</loc>\n'
            f'    <lastmod>{today}</lastmod>\n'
            f'    <changefreq>monthly</changefreq>\n'
            f'    <priority>0.7</priority>\n'
            f'  </url>'
        )

    # ── City landing pages ──────────────────────────────────────────────
    for city in GHANA_CITIES:
        urls.append(
            f'  <url>\n'
            f'    <loc>{base}/schools-in/{city["slug"]}/</loc>\n'
            f'    <lastmod>{today}</lastmod>\n'
            f'    <changefreq>weekly</changefreq>\n'
            f'    <priority>0.6</priority>\n'
            f'  </url>'
        )

    # ── Guest catalog & tools hub ───────────────────────────────────────
    urls.append(
        f'  <url>\n'
        f'    <loc>{base}/u/guest/</loc>\n'
        f'    <lastmod>{today}</lastmod>\n'
        f'    <changefreq>weekly</changefreq>\n'
        f'    <priority>0.9</priority>\n'
        f'  </url>'
    )
    urls.append(
        f'  <url>\n'
        f'    <loc>{base}/u/guest/tools/</loc>\n'
        f'    <lastmod>{today}</lastmod>\n'
        f'    <changefreq>weekly</changefreq>\n'
        f'    <priority>0.9</priority>\n'
        f'  </url>'
    )

    # ── GES curriculum subject + strand detail pages ────────────────────
    for subj in GES_CURRICULUM:
        for idx, strand in enumerate(subj['strands']):
            urls.append(
                f'  <url>\n'
                f'    <loc>{base}/u/guest/{subj["subject"]}/{idx}/</loc>\n'
                f'    <lastmod>{today}</lastmod>\n'
                f'    <changefreq>monthly</changefreq>\n'
                f'    <priority>0.8</priority>\n'
                f'  </url>'
            )

    # ── Signup / signin (for referral attribution) ──────────────────────
    urls.append(
        f'  <url>\n'
        f'    <loc>{base}/u/signup/</loc>\n'
        f'    <lastmod>{today}</lastmod>\n'
        f'    <changefreq>monthly</changefreq>\n'
        f'    <priority>0.8</priority>\n'
        f'  </url>'
    )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + '\n'.join(urls) + '\n'
        '</urlset>'
    )
    return HttpResponse(xml, content_type='application/xml')


def robots_txt(request):
    """Dynamic robots.txt that blocks crawlers from authenticated/API routes."""
    base = _base_url(request)
    lines = [
        'User-agent: *',
        'Allow: /',
        '',
        '# Block authenticated app routes (expensive API calls)',
        'Disallow: /u/dashboard/',
        'Disallow: /u/tools/',
        'Disallow: /u/settings/',
        'Disallow: /u/credits/',
        'Disallow: /u/addons/',
        'Disallow: /u/referrals/',
        'Disallow: /u/api-keys/',
        'Disallow: /u/signout/',
        'Disallow: /admin/',
        'Disallow: /dashboard/',
        'Disallow: /landlord/',
        '',
        '# Block tenant schema routes',
        'Disallow: /accounts/',
        'Disallow: /teachers/',
        'Disallow: /students/',
        'Disallow: /parents/',
        'Disallow: /finance/',
        'Disallow: /academics/',
        'Disallow: /communication/',
        'Disallow: /homework/',
        'Disallow: /announcements/',
        '',
        '# Allow guest / public storefront',
        'Allow: /u/guest/',
        'Allow: /u/signup/',
        'Allow: /u/signin/',
        'Allow: /blog/',
        'Allow: /schools-in/',
        'Allow: /pricing/',
        'Allow: /about/',
        'Allow: /contact/',
        'Allow: /compare/',
        'Allow: /nacca-resources/',
        'Allow: /sitemap/',
        '',
        f'Sitemap: {base}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


def visual_sitemap(request):
    """HTML sitemap page — acts as a funnel from curiosity to signup."""
    # Build curriculum links
    subjects = []
    for subj in GES_CURRICULUM:
        strands = []
        for idx, strand in enumerate(subj['strands']):
            strands.append({
                'name': strand['name'],
                'url': reverse('individual:guest_strand_detail', args=[subj['subject'], idx]),
            })
        subjects.append({
            'label': subj['label'],
            'icon': subj['icon'],
            'color': subj['color'],
            'strands': strands,
        })

    cities = [
        {'name': c['name'], 'url': reverse('city_landing', args=[c['slug']])}
        for c in GHANA_CITIES
    ]

    blog_posts = [
        {'title': 'How SchoolPadi Automates Grade Management', 'url': '/blog/grade-management/'},
        {'title': 'Real-Time Fee Tracking & Payment Management', 'url': '/blog/fee-tracking/'},
        {'title': 'Attendance Tracking Made Visual', 'url': '/blog/attendance-system/'},
        {'title': 'AI-Powered Tools for Educators', 'url': '/blog/ai-engine/'},
    ]

    return render(request, 'home/sitemap.html', {
        'subjects': subjects,
        'cities': cities,
        'blog_posts': blog_posts,
    })
