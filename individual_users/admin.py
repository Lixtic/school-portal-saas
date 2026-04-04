from django.contrib import admin
from individual_users.models import (
    AddonSubscription, APIKey, IndividualAddon, IndividualProfile,
    IndividualCreditPack, IndividualCreditBalance, IndividualCreditTransaction,
    VerificationCode,
    ToolQuestion, ToolExamPaper, ToolLessonPlan,
    ToolPresentation, ToolSlide,
    AITutorConversation, AITutorMessage,
    LicensureQuestion, LicensureQuizAttempt, LicensureAnswer,
    GESLetter,
    MarkingSession, StudentMark,
    ReportCardSet, ReportCardEntry,
    CompuThinkActivity, LiteracyExercise, CitizenEdActivity, TVETProject,
)


@admin.register(IndividualAddon)
class IndividualAddonAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'category', 'audience', 'is_active', 'position', 'updated_at')
    list_filter = ('category', 'audience', 'is_active')
    list_editable = ('is_active', 'position')
    search_fields = ('name', 'slug', 'tagline')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('position', 'category', 'name')


@admin.register(IndividualProfile)
class IndividualProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'company', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number', 'company')
    list_filter = ('created_at',)
    raw_id_fields = ('user',)


@admin.register(AddonSubscription)
class AddonSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('profile', 'addon_name', 'plan', 'status', 'started_at', 'expires_at')
    list_filter = ('plan', 'status', 'addon_slug')
    search_fields = ('profile__user__username', 'addon_name')


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'profile', 'prefix', 'is_active', 'calls_total', 'last_used_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'prefix', 'profile__user__username')
    readonly_fields = ('prefix', 'hashed_key', 'calls_today', 'calls_total')


@admin.register(IndividualCreditPack)
class IndividualCreditPackAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'credits', 'price', 'badge_label', 'is_active', 'position')
    list_editable = ('price', 'credits', 'is_active', 'position')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('position',)


@admin.register(IndividualCreditBalance)
class IndividualCreditBalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('balance', 'updated_at')


@admin.register(IndividualCreditTransaction)
class IndividualCreditTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'balance_after', 'created_at')
    list_filter = ('transaction_type',)
    search_fields = ('user__username', 'description')
    readonly_fields = ('user', 'transaction_type', 'amount', 'balance_after', 'description', 'payment_reference')


# ── Verification ─────────────────────────────────────────────────────────────

@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'method', 'code', 'attempts', 'created_at', 'expires_at')
    list_filter = ('method',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('code', 'created_at')


# ── Tool Models ──────────────────────────────────────────────────────────────

@admin.register(ToolQuestion)
class ToolQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text_short', 'profile', 'subject', 'question_format', 'difficulty', 'created_at')
    list_filter = ('subject', 'question_format', 'difficulty')
    search_fields = ('question_text', 'topic', 'profile__user__username')
    raw_id_fields = ('profile',)

    @admin.display(description='Question')
    def question_text_short(self, obj):
        return obj.question_text[:80]


@admin.register(ToolExamPaper)
class ToolExamPaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'profile', 'subject', 'target_class', 'duration_minutes', 'created_at')
    list_filter = ('subject',)
    search_fields = ('title', 'profile__user__username')
    raw_id_fields = ('profile',)
    filter_horizontal = ('questions',)


@admin.register(ToolLessonPlan)
class ToolLessonPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'profile', 'subject', 'target_class', 'topic', 'created_at')
    list_filter = ('subject',)
    search_fields = ('title', 'topic', 'profile__user__username')
    raw_id_fields = ('profile',)


class ToolSlideInline(admin.TabularInline):
    model = ToolSlide
    extra = 0
    fields = ('order', 'layout', 'title', 'content')
    ordering = ('order',)


@admin.register(ToolPresentation)
class ToolPresentationAdmin(admin.ModelAdmin):
    list_display = ('title', 'profile', 'subject', 'theme', 'slide_count', 'times_presented', 'created_at')
    list_filter = ('theme', 'subject')
    search_fields = ('title', 'profile__user__username')
    raw_id_fields = ('profile',)
    inlines = [ToolSlideInline]

    @admin.display(description='Slides')
    def slide_count(self, obj):
        return obj.slide_count


@admin.register(ToolSlide)
class ToolSlideAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'presentation', 'layout', 'order')
    list_filter = ('layout',)
    raw_id_fields = ('presentation',)


# ── AI Tutor ─────────────────────────────────────────────────────────────────

class AITutorMessageInline(admin.TabularInline):
    model = AITutorMessage
    extra = 0
    fields = ('role', 'content', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('created_at',)


@admin.register(AITutorConversation)
class AITutorConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'profile', 'mode', 'subject', 'created_at', 'updated_at')
    list_filter = ('mode', 'subject')
    search_fields = ('title', 'profile__user__username')
    raw_id_fields = ('profile',)
    inlines = [AITutorMessageInline]


@admin.register(AITutorMessage)
class AITutorMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'role', 'content_short', 'created_at')
    list_filter = ('role',)
    raw_id_fields = ('conversation',)

    @admin.display(description='Content')
    def content_short(self, obj):
        return obj.content[:80]


# ── Licensure Prep ───────────────────────────────────────────────────────────

@admin.register(LicensureQuestion)
class LicensureQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text_short', 'domain', 'difficulty', 'source', 'correct_option', 'created_at')
    list_filter = ('domain', 'difficulty', 'source')
    search_fields = ('question_text', 'topic')
    raw_id_fields = ('profile',)

    @admin.display(description='Question')
    def question_text_short(self, obj):
        return obj.question_text[:80]


class LicensureAnswerInline(admin.TabularInline):
    model = LicensureAnswer
    extra = 0
    fields = ('question', 'selected_option', 'is_correct', 'time_spent_seconds')
    readonly_fields = ('is_correct',)
    raw_id_fields = ('question',)


@admin.register(LicensureQuizAttempt)
class LicensureQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'profile', 'mode', 'total_questions', 'correct_count', 'completed', 'started_at')
    list_filter = ('mode', 'completed')
    search_fields = ('profile__user__username',)
    raw_id_fields = ('profile',)
    inlines = [LicensureAnswerInline]


@admin.register(LicensureAnswer)
class LicensureAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_option', 'is_correct')
    list_filter = ('is_correct',)
    raw_id_fields = ('attempt', 'question')


# ── GES Letter Writer ────────────────────────────────────────────────────────

@admin.register(GESLetter)
class GESLetterAdmin(admin.ModelAdmin):
    list_display = ('title', 'profile', 'category', 'status', 'ai_generated', 'created_at')
    list_filter = ('category', 'status', 'ai_generated')
    search_fields = ('title', 'recipient_name', 'profile__user__username')
    raw_id_fields = ('profile',)


# ── Paper Marker ─────────────────────────────────────────────────────────────

class StudentMarkInline(admin.TabularInline):
    model = StudentMark
    extra = 0
    fields = ('student_name', 'student_index', 'score', 'total', 'percentage')
    readonly_fields = ('percentage',)


@admin.register(MarkingSession)
class MarkingSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'profile', 'subject', 'class_name', 'total_questions', 'student_count', 'class_average', 'created_at')
    list_filter = ('subject',)
    search_fields = ('title', 'profile__user__username')
    raw_id_fields = ('profile',)
    inlines = [StudentMarkInline]

    @admin.display(description='Students')
    def student_count(self, obj):
        return obj.student_count

    @admin.display(description='Avg %')
    def class_average(self, obj):
        return obj.class_average


@admin.register(StudentMark)
class StudentMarkAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'session', 'score', 'total', 'percentage')
    search_fields = ('student_name', 'student_index')
    raw_id_fields = ('session',)


# ── Report Cards ─────────────────────────────────────────────────────────────

class ReportCardEntryInline(admin.TabularInline):
    model = ReportCardEntry
    extra = 0
    fields = ('student_name', 'overall_score', 'overall_grade', 'position', 'conduct', 'promoted')


@admin.register(ReportCardSet)
class ReportCardSetAdmin(admin.ModelAdmin):
    list_display = ('title', 'profile', 'class_name', 'term', 'academic_year', 'created_at')
    list_filter = ('term', 'academic_year')
    search_fields = ('title', 'profile__user__username')
    raw_id_fields = ('profile',)
    inlines = [ReportCardEntryInline]


@admin.register(ReportCardEntry)
class ReportCardEntryAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'card_set', 'overall_score', 'overall_grade', 'position', 'conduct', 'promoted')
    list_filter = ('conduct', 'promoted')
    search_fields = ('student_name',)
    raw_id_fields = ('card_set',)


# ── Subject-Area Tools ───────────────────────────────────────────────────────

@admin.register(CompuThinkActivity)
class CompuThinkActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'profile', 'activity_type', 'level', 'ai_generated', 'created_at')
    list_filter = ('activity_type', 'level', 'ai_generated')
    search_fields = ('title', 'topic', 'profile__user__username')
    raw_id_fields = ('profile',)


@admin.register(LiteracyExercise)
class LiteracyExerciseAdmin(admin.ModelAdmin):
    list_display = ('title', 'profile', 'exercise_type', 'level', 'ai_generated', 'created_at')
    list_filter = ('exercise_type', 'level', 'ai_generated')
    search_fields = ('title', 'topic', 'profile__user__username')
    raw_id_fields = ('profile',)


@admin.register(CitizenEdActivity)
class CitizenEdActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'profile', 'activity_type', 'level', 'strand', 'ai_generated', 'created_at')
    list_filter = ('activity_type', 'level', 'strand', 'ai_generated')
    search_fields = ('title', 'topic', 'profile__user__username')
    raw_id_fields = ('profile',)


@admin.register(TVETProject)
class TVETProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'profile', 'project_type', 'level', 'strand', 'ai_generated', 'created_at')
    list_filter = ('project_type', 'level', 'strand', 'ai_generated')
    search_fields = ('title', 'topic', 'profile__user__username')
    raw_id_fields = ('profile',)
