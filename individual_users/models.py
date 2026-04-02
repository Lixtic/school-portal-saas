import secrets
from django.conf import settings
from django.db import models
from django.utils import timezone


class IndividualProfile(models.Model):
    """Extended profile for individual (non-school) platform users."""
    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('teacher', 'Teacher'),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='individual_profile',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer', db_index=True)
    phone_number = models.CharField(max_length=20, blank=True, db_index=True)
    google_id = models.CharField(max_length=255, blank=True, db_index=True)
    avatar_url = models.URLField(blank=True)
    company = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Individual Profile'
        verbose_name_plural = 'Individual Profiles'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"


class AddonSubscription(models.Model):
    """Tracks which addons an individual user is subscribed to."""
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE, related_name='subscriptions',
    )
    addon_slug = models.CharField(max_length=80)
    addon_name = models.CharField(max_length=120)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('profile', 'addon_slug')
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.addon_name} ({self.plan}) — {self.profile}"

    @property
    def is_active(self):
        if self.status != 'active':
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


class APIKey(models.Model):
    """API keys for individual users to access addon marketplace endpoints."""
    profile = models.ForeignKey(
        IndividualProfile, on_delete=models.CASCADE, related_name='api_keys',
    )
    name = models.CharField(max_length=100, help_text='A label for this key')
    prefix = models.CharField(max_length=8, db_index=True, editable=False)
    hashed_key = models.CharField(max_length=128, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    calls_today = models.PositiveIntegerField(default=0)
    calls_total = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.prefix}…)"

    @staticmethod
    def generate():
        """Generate a new API key. Returns (raw_key, prefix, hashed_key)."""
        import hashlib
        raw = 'aura_' + secrets.token_hex(24)  # 53-char key
        prefix = raw[:8]
        hashed = hashlib.sha256(raw.encode()).hexdigest()
        return raw, prefix, hashed

    @staticmethod
    def hash_key(raw_key):
        import hashlib
        return hashlib.sha256(raw_key.encode()).hexdigest()
