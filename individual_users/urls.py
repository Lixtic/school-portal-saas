from django.urls import path
from individual_users import views
from individual_users import tool_views

app_name = 'individual'

urlpatterns = [
    # Auth
    path('signup/', views.signup_view, name='signup'),
    path('signin/', views.signin_view, name='signin'),
    path('verify/', views.verify_view, name='verify'),
    path('verify/resend/', views.resend_code_view, name='verify_resend'),
    path('auth/google/', views.google_auth_view, name='google_auth'),
    path('signout/', views.signout_view, name='signout'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Settings
    path('settings/', views.settings_view, name='settings'),

    # Addon marketplace
    path('addons/', views.addons_view, name='addons'),
    path('addons/subscribe/', views.subscribe_addon, name='subscribe_addon'),
    path('addons/unsubscribe/', views.unsubscribe_addon, name='unsubscribe_addon'),
    path('addons/verify/', views.verify_addon_payment, name='verify_addon_payment'),

    # Paystack webhook (no auth required, HMAC-verified)
    path('webhook/paystack/', views.paystack_individual_webhook, name='paystack_individual_webhook'),

    # API keys
    path('api-keys/', views.api_keys_view, name='api_keys'),
    path('api-keys/revoke/', views.revoke_api_key, name='revoke_api_key'),

    # API status endpoint
    path('api/status/', views.api_status, name='api_status'),

    # ── Tools (teacher portal bridge) ────────────────────────────────────────
    path('tools/', tool_views.tools_hub, name='tools_hub'),

    # Question Bank
    path('tools/questions/', tool_views.question_bank_list, name='question_bank'),
    path('tools/questions/new/', tool_views.question_create, name='question_create'),
    path('tools/questions/<int:pk>/edit/', tool_views.question_edit, name='question_edit'),
    path('tools/questions/<int:pk>/delete/', tool_views.question_delete, name='question_delete'),
    path('tools/questions/ai-generate/', tool_views.question_ai_generate, name='question_ai_generate'),

    # Exam Papers
    path('tools/exam-papers/', tool_views.exam_paper_list, name='exam_papers'),
    path('tools/exam-papers/new/', tool_views.exam_paper_create, name='exam_paper_create'),
    path('tools/exam-papers/<int:pk>/', tool_views.exam_paper_detail, name='exam_paper_detail'),
    path('tools/exam-papers/<int:pk>/delete/', tool_views.exam_paper_delete, name='exam_paper_delete'),

    # Lesson Plans
    path('tools/lesson-plans/', tool_views.lesson_plan_list, name='lesson_plans'),
    path('tools/lesson-plans/new/', tool_views.lesson_plan_create, name='lesson_plan_create'),
    path('tools/lesson-plans/<int:pk>/', tool_views.lesson_plan_detail, name='lesson_plan_detail'),
    path('tools/lesson-plans/<int:pk>/edit/', tool_views.lesson_plan_edit, name='lesson_plan_edit'),
    path('tools/lesson-plans/<int:pk>/delete/', tool_views.lesson_plan_delete, name='lesson_plan_delete'),
    path('tools/lesson-plans/<int:pk>/print/', tool_views.lesson_plan_print, name='lesson_plan_print'),
    path('tools/lesson-plans/ai-generate/', tool_views.lesson_plan_ai_generate, name='lesson_plan_ai_generate'),
    path('tools/lesson-plans/ges-generate/', tool_views.lesson_plan_ges_generate, name='lesson_plan_ges_generate'),

    # Slide Decks / Presentations
    path('tools/presentations/', tool_views.deck_list, name='deck_list'),
    path('tools/presentations/new/', tool_views.deck_create, name='deck_create'),
    path('tools/presentations/<int:pk>/editor/', tool_views.deck_editor, name='deck_editor'),
    path('tools/presentations/<int:pk>/present/', tool_views.deck_present, name='deck_present'),
    path('tools/presentations/<int:pk>/print/', tool_views.deck_print, name='deck_print'),
    path('tools/presentations/<int:pk>/delete/', tool_views.deck_delete, name='deck_delete'),
    path('tools/presentations/<int:pk>/duplicate/', tool_views.deck_duplicate, name='deck_duplicate'),
    path('tools/presentations/api/', tool_views.deck_api, name='deck_api'),
    path('tools/presentations/share/<uuid:token>/', tool_views.deck_share, name='deck_share'),

    # GTLE Licensure Prep
    path('tools/licensure/', tool_views.licensure_dashboard, name='licensure_dashboard'),
    path('tools/licensure/start/', tool_views.licensure_quiz_start, name='licensure_quiz_start'),
    path('tools/licensure/quiz/<int:pk>/', tool_views.licensure_quiz_take, name='licensure_quiz_take'),
    path('tools/licensure/quiz/<int:pk>/review/', tool_views.licensure_quiz_review, name='licensure_quiz_review'),
    path('tools/licensure/history/', tool_views.licensure_history, name='licensure_history'),
    path('tools/licensure/api/', tool_views.licensure_api, name='licensure_api'),
    path('tools/licensure/load-bank/', tool_views.licensure_load_bank, name='licensure_load_bank'),

    # AI Teaching Assistant
    path('tools/ai-tutor/', tool_views.ai_tutor_dashboard, name='ai_tutor_dashboard'),
    path('tools/ai-tutor/api/', tool_views.ai_tutor_api, name='ai_tutor_api'),

    # GES Letter Writer
    path('tools/letters/', tool_views.letter_dashboard, name='letter_dashboard'),
    path('tools/letters/new/', tool_views.letter_create, name='letter_create'),
    path('tools/letters/<int:pk>/edit/', tool_views.letter_edit, name='letter_edit'),
    path('tools/letters/<int:pk>/delete/', tool_views.letter_delete, name='letter_delete'),
    path('tools/letters/<int:pk>/print/', tool_views.letter_print, name='letter_print'),
    path('tools/letters/api/', tool_views.letter_api, name='letter_api'),
]

# Teacher shortcut URLs (included under /t/ prefix in main urls.py)
teacher_urlpatterns = [
    path('', views.teacher_redirect, name='teacher_home'),
    path('signup/', views.teacher_redirect, name='teacher_signup'),
    path('signin/', views.teacher_signin_redirect, name='teacher_signin'),
]
