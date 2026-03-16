from django.db import models
from accounts.models import User

class StudyGroupRoom(models.Model):
    name = models.CharField(max_length=200)
    # Import string to avoid circular dependency
    student_class = models.OneToOneField('academics.Class', on_delete=models.CASCADE, null=True, blank=True, related_name='study_room')
    is_global = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class StudyGroupMessage(models.Model):
    room = models.ForeignKey(StudyGroupRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    is_aura = models.BooleanField(default=False)
    
    BATTLE_TYPE_CHOICES = [
        ('battle',    'Trivia Battle'),
        ('riddle',    'Riddle'),
        ('math',      'Math Challenge'),
        ('scrabble',  'Scrabble Challenge'),
        ('spell',     'Spelling Challenge (Legacy)'),
        ('truefalse', 'True or False'),
    ]

    # Battle tracking
    is_battle_question = models.BooleanField(default=False)
    battle_type = models.CharField(max_length=20, choices=BATTLE_TYPE_CHOICES, default='battle')
    battle_xp = models.IntegerField(default=20)
    battle_answered = models.BooleanField(default=False)
    battle_winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_battles')
    battle_answer = models.CharField(max_length=255, null=True, blank=True) # the expected answer
    
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender or 'Aura'} in {self.room.name}: {self.content[:30]}"
