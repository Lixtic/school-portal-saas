"""
Digital Pulse — real-time class check-in system.
Teachers launch a pulse from Command Center; students respond via interactive cards.
"""

from django.db import models


# ─── Q / Chip parsers ────────────────────────────────────────────────────────

def parse_pulse_questions(intro: str):
    """Return (q1_text, q2_text, q3_text) from a lesson plan introduction field."""
    import re
    results = ['', '', '']
    for i, label in enumerate(['Q1:', 'Q2:', 'Q3:']):
        idx = intro.find(label)
        if idx == -1:
            continue
        after = intro[idx + len(label):]
        ends = []
        nxt = f'Q{i + 2}:'
        j = after.find(nxt)
        if j != -1:
            ends.append(j)
        for stop in ['\n\n', '\nTeacher', '\n🟢', '\n🔵']:
            k = after.find(stop)
            if k != -1:
                ends.append(k)
        if ends:
            after = after[:min(ends)]
        results[i] = after.split('\n')[0].strip()

    # ── Backstop: Q1 and Q2 must be T/F declarative statements ──────────────
    # If GPT slipped in an interrogative question ("What is...", "How...", etc.),
    # append "— True or False?" so the student overlay is at least coherent.
    _INTERROGATIVE = re.compile(
        r'^(what|how|who|why|when|where|name|list|describe|explain|define|give|identify)\b',
        re.IGNORECASE
    )
    for idx in (0, 1):  # Q1 and Q2 only
        txt = results[idx]
        if not txt:
            continue
        is_open_question = _INTERROGATIVE.match(txt)
        already_tf = re.search(r'true or false', txt, re.IGNORECASE)
        if is_open_question and not already_tf:
            # Strip trailing "?" and append T/F cue
            txt = txt.rstrip('?').rstrip()
            results[idx] = txt + ' — True or False?'

    return tuple(results)


def parse_q3_chips(plan) -> list:
    """
    Build 3 carousel chip options for the Q3 Context Application question.
    We extract the first meaningful line of SUPPORT PATH and EXTENSION PATH,
    which represent the two learning trajectories the student can self-select into.
    """
    text = plan.presentation or ''
    chips = []

    def _first_line(raw: str) -> str:
        for ln in raw.split('\n'):
            ln = ln.strip().lstrip('–—-•·').strip()
            if ln and not ln.lower().startswith('for students') and len(ln) > 6:
                return ln[:90]
        return ''

    sp_idx = max(text.find('SUPPORT PATH'), text.find('🟢'))
    ep_idx = max(text.find('EXTENSION PATH'), text.find('🔵'))

    sp_body = ''
    ep_body = ''
    if sp_idx != -1:
        after_sp = text[sp_idx:]
        # trim at extension path or double newline
        for stop in ['🔵', 'EXTENSION PATH', '\n\n']:
            k = after_sp.find(stop)
            if k != -1:
                after_sp = after_sp[:k]
        sp_body = after_sp

    if ep_idx != -1:
        after_ep = text[ep_idx:]
        for stop in ['\n\n\n']:
            k = after_ep.find(stop)
            if k != -1:
                after_ep = after_ep[:k]
        ep_body = after_ep

    sp_title = _first_line(sp_body.replace('SUPPORT PATH', '').replace('🟢', ''))
    ep_title = _first_line(ep_body.replace('EXTENSION PATH', '').replace('🔵', ''))

    chips.append(f'🟢 {sp_title}' if sp_title else '🟢 Support Path — I need more scaffolding')
    chips.append(f'🔵 {ep_title}' if ep_title else '🔵 Extension Path — I\'m ready to go deeper')
    chips.append('🤔 Not sure yet — need more time')
    return chips


# ─── Models ──────────────────────────────────────────────────────────────────

class PulseSession(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('closed', 'Closed')]

    lesson_plan = models.ForeignKey(
        'teachers.LessonPlan', on_delete=models.CASCADE, related_name='pulse_sessions',
        null=True, blank=True)
    # Optional: launched from a presentation study guide
    presentation = models.ForeignKey(
        'teachers.Presentation', on_delete=models.CASCADE, related_name='pulse_sessions',
        null=True, blank=True)
    # Explicit class target (used when launched from a presentation, not a lesson plan)
    target_class = models.ForeignKey(
        'academics.Class', on_delete=models.SET_NULL, related_name='pulse_sessions',
        null=True, blank=True)
    teacher = models.ForeignKey(
        'teachers.Teacher', on_delete=models.CASCADE, related_name='pulse_sessions')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    # Parsed question texts (stored so they survive plan edits)
    q1_text = models.TextField(blank=True)
    q2_text = models.TextField(blank=True)
    q3_text = models.TextField(blank=True)
    q3_chips = models.JSONField(default=list)   # ordered list of chip label strings

    created_at = models.DateTimeField(auto_now_add=True)
    closed_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'academics'
        ordering = ['-created_at']

    def __str__(self):
        if self.lesson_plan_id:
            return f'Pulse #{self.pk} — {self.lesson_plan.topic}'
        if self.presentation_id:
            return f'Pulse #{self.pk} — {self.presentation.title}'
        return f'Pulse #{self.pk}'

    def _target_class(self):
        """Resolve the class this session targets (lesson_plan or explicit)."""
        if self.lesson_plan_id:
            return self.lesson_plan.school_class
        return self.target_class

    @property
    def total_students(self):
        """Number of students in the target class."""
        try:
            cls = self._target_class()
            if cls is None:
                return 0
            return cls.students.filter(user__is_active=True).count()
        except Exception:
            return 0

    @property
    def responded_count(self):
        return self.responses.filter(submitted_at__isnull=False).count()

    @property
    def typing_students(self):
        return list(
            self.responses.filter(is_typing=True, submitted_at__isnull=True)
            .select_related('student__user')
            .values_list('student__user__first_name', 'student__user__last_name')
        )


class PulseResponse(models.Model):
    session  = models.ForeignKey(
        PulseSession, on_delete=models.CASCADE, related_name='responses')
    student  = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE, related_name='pulse_responses')

    q1_answer = models.BooleanField(null=True, blank=True)   # True / False
    q2_answer = models.BooleanField(null=True, blank=True)   # True / False
    q3_answer = models.CharField(max_length=200, blank=True) # selected chip

    is_typing    = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'academics'
        unique_together = ('session', 'student')

    def __str__(self):
        return f'Response: {self.student} → pulse #{self.session_id}'
