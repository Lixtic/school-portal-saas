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
