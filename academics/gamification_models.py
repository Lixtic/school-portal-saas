from django.db import models
from django.utils import timezone
from students.models import Student

class StudentXP(models.Model):
    """
    Gamification profile for a student.
    Tracks total XP, level, and streaks.
    """
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='gamification_profile')
    total_xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    
    # Activity tracking for streaks
    current_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def level_progress(self):
        """Standard 100 XP per level progression"""
        return self.total_xp % 100

    @property
    def xp_to_next_level(self):
        return 100 - (self.total_xp % 100)

    def __str__(self):
        return f"{self.student} - Lvl {self.level} ({self.total_xp} XP)"

    def add_xp(self, amount):
        """Add XP and recalculate level."""
        self.total_xp += amount
        
        # Simple level formula: Level = 1 + (XP / 100)
        # Or slightly progressive: 100 * level
        # Let's keep it simple: 100 XP per level for now.
        # But let's check for level up
        new_level = 1 + (self.total_xp // 100)
        
        leveled_up = False
        if new_level > self.level:
            self.level = new_level
            leveled_up = True
            
        self.save()
        return leveled_up

    def update_streak(self):
        """Call this when user performs an action."""
        today = timezone.now().date()
        
        if self.last_activity_date == today:
            return  # Already counted for today
            
        if self.last_activity_date:
            delta = today - self.last_activity_date
            if delta.days == 1:
                self.current_streak += 1
            else:
                self.current_streak = 1
        else:
            self.current_streak = 1
            
        self.last_activity_date = today
        self.save()


class Achievement(models.Model):
    """
    Definition of an achievement (Badge).
    """
    slug = models.SlugField(max_length=50, unique=True, help_text="Unique identifier for code reference")
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default="🏆", help_text="Emoji or Icon class")
    xp_reward = models.IntegerField(default=50)
    
    # Criteria (optional, for display or logic)
    category = models.CharField(max_length=50, default="General")
    
    def __str__(self):
        return self.name


class StudentAchievement(models.Model):
    """
    Unlock record for an achievement.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'achievement']
        ordering = ['-unlocked_at']

    def __str__(self):
        return f"{self.student} unlocked {self.achievement.name}"


class AuraSessionState(models.Model):
    """
    Shared State Manager — the Redux-style single source of truth for all
    Aura sessions (text chat + voice).  Persisted in PostgreSQL so lesson
    progress, vocabulary level, and student mood are never lost when the
    student switches between modes.
    """
    LESSON_STATE_CHOICES = [
        ('IDLE',        'Not started'),
        ('HOOK',        'Hook'),
        ('NUGGET_1',    'Nugget 1'),
        ('NUGGET_2',    'Nugget 2'),
        ('NUGGET_3',    'Nugget 3'),
        ('NUGGET_4',    'Nugget 4'),
        ('NUGGET_5',    'Nugget 5'),
        ('STRESS_TEST', 'Stress Test'),
        ('DONE',        'Done'),
    ]
    MOOD_CHOICES = [
        ('positive',   'Positive'),
        ('neutral',    'Neutral'),
        ('negative',   'Negative'),
        ('frustrated', 'Frustrated'),
    ]

    student     = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='aura_state')
    lesson_state = models.CharField(max_length=30, default='IDLE', choices=LESSON_STATE_CHOICES)
    vocab_level  = models.IntegerField(default=3)   # 1–6, mirrors _get_complexity_instruction()
    mood         = models.CharField(max_length=20, default='neutral', choices=MOOD_CHOICES)
    updated_by   = models.CharField(max_length=10, default='text')  # 'text' | 'voice'
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Aura Session State'

    def __str__(self):
        return f"{self.student} | {self.lesson_state} | L{self.vocab_level} | {self.mood}"

    def as_dict(self):
        return {
            'lesson_state': self.lesson_state,
            'vocab_level':  self.vocab_level,
            'mood':         self.mood,
            'updated_by':   self.updated_by,
            'updated_at':   self.updated_at.isoformat() if self.updated_at else None,
        }

    def as_prompt_injection(self):
        """
        Return a text block injected into the system prompt so Aura knows
        where the student left off regardless of which interface they used.
        """
        if self.lesson_state in ('IDLE', ''):
            return ''
        lines = ['\n\n─── SHARED SESSION STATE ───']
        lines.append(
            f'The student was at [LESSON_STATE: {self.lesson_state}] in a previous '
            f'{self.updated_by} session.'
        )
        if self.lesson_state == 'DONE':
            lines.append('The previous lesson is complete — start a fresh topic when ready.')
        else:
            lines.append(
                f'Resume from [LESSON_STATE: {self.lesson_state}] — do NOT restart '
                f'from HOOK. Continue from where you left off.'
            )
        lines.append(f'Student Vocabulary Level: {self.vocab_level}/6 (last assessed).')
        lines.append(
            f'  → Keep language pitched at this level (scale: 1=simplest, 3=intermediate, 6=expert).'
        )
        lines.append(
            f'  → Only emit [VOCAB_LEVEL: N] if you observe clear competence shift '
            f'(2+ consecutive signals).'
        )
        if self.mood in ('negative', 'frustrated'):
            lines.append(
                f'Student mood was {self.mood} in the last session — be extra encouraging today.'
            )
        lines.append('────────────────────────────────────')
        return '\n'.join(lines)
