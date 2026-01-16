# Generated migration for homepage customization fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0014_schoolinfo_homepage_template'),
    ]

    operations = [
        # Hero Section
        migrations.AddField(
            model_name='schoolinfo',
            name='hero_title',
            field=models.CharField(blank=True, default='', help_text='Main hero heading (leave empty to use school name)', max_length=200),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='hero_subtitle',
            field=models.CharField(blank=True, default='', help_text='Hero subtitle/description', max_length=300),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='cta_primary_text',
            field=models.CharField(default='Portal Login', help_text='Primary call-to-action button text', max_length=50),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='cta_primary_url',
            field=models.CharField(default='/login/', help_text='Primary CTA URL', max_length=200),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='cta_secondary_text',
            field=models.CharField(default='Apply Now', help_text='Secondary call-to-action button text', max_length=50),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='cta_secondary_url',
            field=models.CharField(default='/academics/apply/', help_text='Secondary CTA URL', max_length=200),
        ),
        
        # Stats Section
        migrations.AddField(
            model_name='schoolinfo',
            name='stat1_number',
            field=models.CharField(default='25+', help_text='First statistic number', max_length=20),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='stat1_label',
            field=models.CharField(default='Years of Excellence', help_text='First statistic label', max_length=50),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='stat2_number',
            field=models.CharField(default='1000+', help_text='Second statistic number', max_length=20),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='stat2_label',
            field=models.CharField(default='Students Enrolled', help_text='Second statistic label', max_length=50),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='stat3_number',
            field=models.CharField(default='50+', help_text='Third statistic number', max_length=20),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='stat3_label',
            field=models.CharField(default='Expert Teachers', help_text='Third statistic label', max_length=50),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='stat4_number',
            field=models.CharField(default='98%', help_text='Fourth statistic number', max_length=20),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='stat4_label',
            field=models.CharField(default='Success Rate', help_text='Fourth statistic label', max_length=50),
        ),
        
        # Features/Highlights
        migrations.AddField(
            model_name='schoolinfo',
            name='feature1_title',
            field=models.CharField(default='Academic Excellence', help_text='First feature title', max_length=100),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='feature1_description',
            field=models.TextField(default='Proven track record of outstanding academic performance and university placements.'),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='feature1_icon',
            field=models.CharField(default='fa-award', help_text='FontAwesome icon class (e.g., fa-award)', max_length=50),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='feature2_title',
            field=models.CharField(default='Expert Faculty', help_text='Second feature title', max_length=100),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='feature2_description',
            field=models.TextField(default='Highly qualified and dedicated teachers committed to student success.'),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='feature2_icon',
            field=models.CharField(default='fa-users', help_text='FontAwesome icon class', max_length=50),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='feature3_title',
            field=models.CharField(default='Modern Facilities', help_text='Third feature title', max_length=100),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='feature3_description',
            field=models.TextField(default='State-of-the-art classrooms, laboratories, and sports facilities.'),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='feature3_icon',
            field=models.CharField(default='fa-building', help_text='FontAwesome icon class', max_length=50),
        ),
        
        # About Section
        migrations.AddField(
            model_name='schoolinfo',
            name='about_title',
            field=models.CharField(default='Why Choose Us', help_text='About/Why Choose section title', max_length=100),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='about_description',
            field=models.TextField(blank=True, default='We provide a comprehensive educational experience that nurtures academic excellence, character development, and leadership skills.'),
        ),
        
        # Social Media
        migrations.AddField(
            model_name='schoolinfo',
            name='facebook_url',
            field=models.URLField(blank=True, default='', help_text='Facebook page URL'),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='twitter_url',
            field=models.URLField(blank=True, default='', help_text='Twitter/X profile URL'),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='instagram_url',
            field=models.URLField(blank=True, default='', help_text='Instagram profile URL'),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='linkedin_url',
            field=models.URLField(blank=True, default='', help_text='LinkedIn page URL'),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='youtube_url',
            field=models.URLField(blank=True, default='', help_text='YouTube channel URL'),
        ),
        
        # Additional Settings
        migrations.AddField(
            model_name='schoolinfo',
            name='show_stats_section',
            field=models.BooleanField(default=True, help_text='Display statistics section on homepage'),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='show_programs_section',
            field=models.BooleanField(default=True, help_text='Display academic programs section'),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='show_gallery_preview',
            field=models.BooleanField(default=True, help_text='Display gallery preview section'),
        ),
    ]
