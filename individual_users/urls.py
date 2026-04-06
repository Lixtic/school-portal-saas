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
    path('auth/google/callback/', views.google_callback_view, name='google_callback'),
    path('signout/', views.signout_view, name='signout'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
    path('settings/delete-account/', views.delete_account_view, name='delete_account'),

    # Addon marketplace (fixed paths BEFORE dynamic slug)
    path('addons/', views.addons_view, name='addons'),
    path('addons/subscribe/', views.subscribe_addon, name='subscribe_addon'),
    path('addons/trial/', views.trial_addon, name='trial_addon'),
    path('addons/unsubscribe/', views.unsubscribe_addon, name='unsubscribe_addon'),
    path('addons/reorder/', views.reorder_addons, name='reorder_addons'),
    path('addons/verify/', views.verify_addon_payment, name='verify_addon_payment'),
    path('addons/<slug:slug>/', views.addon_detail_view, name='addon_detail'),

    # AI Credits
    path('credits/purchase/<int:pack_id>/', views.purchase_credits, name='purchase_credits'),
    path('credits/verify/', views.verify_credit_purchase, name='verify_credit_purchase'),
    path('credits/history/', views.credit_history, name='credit_history'),

    # Referrals
    path('referrals/', views.referral_view, name='referrals'),

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
    path('tools/lesson-plans/<int:pk>/pdf/', tool_views.lesson_plan_pdf, name='lesson_plan_pdf'),
    path('tools/lesson-plans/<int:pk>/word/', tool_views.lesson_plan_word, name='lesson_plan_word'),
    path('tools/lesson-plans/ai-generate/', tool_views.lesson_plan_ai_generate, name='lesson_plan_ai_generate'),
    path('tools/lesson-plans/ges-generate/', tool_views.lesson_plan_ges_generate, name='lesson_plan_ges_generate'),

    # Slide Decks / Presentations
    path('tools/presentations/', tool_views.deck_list, name='deck_list'),
    path('tools/presentations/new/', tool_views.deck_create, name='deck_create'),
    path('tools/presentations/<int:pk>/editor/', tool_views.deck_editor, name='deck_editor'),
    path('tools/presentations/<int:pk>/present/', tool_views.deck_present, name='deck_present'),
    path('tools/presentations/<int:pk>/print/', tool_views.deck_print, name='deck_print'),
    path('tools/presentations/<int:pk>/notes/', tool_views.deck_notes_print, name='deck_notes_print'),
    path('tools/presentations/<int:pk>/delete/', tool_views.deck_delete, name='deck_delete'),
    path('tools/presentations/<int:pk>/duplicate/', tool_views.deck_duplicate, name='deck_duplicate'),
    path('tools/presentations/api/', tool_views.deck_api, name='deck_api'),
    path('tools/presentations/share/<uuid:token>/', tool_views.deck_share, name='deck_share'),
    path('tools/presentations/<int:pk>/start-remote/', tool_views.deck_start_remote, name='deck_start_remote'),
    path('tools/presentations/remote/<uuid:token>/', tool_views.deck_remote, name='deck_remote'),
    path('tools/presentations/remote/<uuid:token>/api/', tool_views.deck_remote_api, name='deck_remote_api'),
    path('tools/presentations/remote/<uuid:token>/state/', tool_views.deck_remote_state, name='deck_remote_state'),
    path('tools/presentations/poll/<uuid:token>/vote/', tool_views.deck_poll_vote, name='deck_poll_vote'),
    path('tools/presentations/poll/<uuid:token>/results/', tool_views.deck_poll_results, name='deck_poll_results'),

    # GTLE Licensure Prep
    path('tools/licensure/', tool_views.licensure_dashboard, name='licensure_dashboard'),
    path('tools/licensure/start/', tool_views.licensure_quiz_start, name='licensure_quiz_start'),
    path('tools/licensure/quiz/<int:pk>/', tool_views.licensure_quiz_take, name='licensure_quiz_take'),
    path('tools/licensure/quiz/<int:pk>/review/', tool_views.licensure_quiz_review, name='licensure_quiz_review'),
    path('tools/licensure/history/', tool_views.licensure_history, name='licensure_history'),
    path('tools/licensure/api/', tool_views.licensure_api, name='licensure_api'),
    path('tools/licensure/load-bank/', tool_views.licensure_load_bank, name='licensure_load_bank'),

    # GES Promotion Exam Prep
    path('tools/promotion/', tool_views.promotion_dashboard, name='promotion_dashboard'),
    path('tools/promotion/start/', tool_views.promotion_quiz_start, name='promotion_quiz_start'),
    path('tools/promotion/quiz/<int:pk>/', tool_views.promotion_quiz_take, name='promotion_quiz_take'),
    path('tools/promotion/quiz/<int:pk>/review/', tool_views.promotion_quiz_review, name='promotion_quiz_review'),
    path('tools/promotion/history/', tool_views.promotion_history, name='promotion_history'),
    path('tools/promotion/api/', tool_views.promotion_api, name='promotion_api'),
    path('tools/promotion/load-bank/', tool_views.promotion_load_bank, name='promotion_load_bank'),

    # AI Teaching Assistant
    path('tools/ai-tutor/', tool_views.ai_tutor_dashboard, name='ai_tutor_dashboard'),
    path('tools/ai-tutor/api/', tool_views.ai_tutor_api, name='ai_tutor_api'),

    # GES Letter Writer
    path('tools/letters/', tool_views.letter_dashboard, name='letter_dashboard'),
    path('tools/letters/new/', tool_views.letter_create, name='letter_create'),
    path('tools/letters/<int:pk>/edit/', tool_views.letter_edit, name='letter_edit'),
    path('tools/letters/<int:pk>/delete/', tool_views.letter_delete, name='letter_delete'),
    path('tools/letters/<int:pk>/duplicate/', tool_views.letter_duplicate, name='letter_duplicate'),
    path('tools/letters/<int:pk>/print/', tool_views.letter_print, name='letter_print'),
    path('tools/letters/api/', tool_views.letter_api, name='letter_api'),

    # Paper Marker
    path('tools/marker/', tool_views.marker_dashboard, name='marker_dashboard'),
    path('tools/marker/new/', tool_views.marker_create, name='marker_create'),
    path('tools/marker/<int:pk>/', tool_views.marker_session, name='marker_session'),
    path('tools/marker/<int:pk>/edit/', tool_views.marker_edit, name='marker_edit'),
    path('tools/marker/<int:pk>/delete/', tool_views.marker_delete, name='marker_delete'),
    path('tools/marker/api/', tool_views.marker_api, name='marker_api'),

    # Report Card Writer
    path('tools/report-cards/', tool_views.report_card_dashboard, name='report_card_dashboard'),
    path('tools/report-cards/new/', tool_views.report_card_create, name='report_card_create'),
    path('tools/report-cards/<int:pk>/', tool_views.report_card_edit, name='report_card_edit'),
    path('tools/report-cards/<int:pk>/delete/', tool_views.report_card_delete, name='report_card_delete'),
    path('tools/report-cards/<int:pk>/entries/<int:entry_pk>/edit/', tool_views.report_card_entry_edit, name='report_card_entry_edit'),
    path('tools/report-cards/<int:pk>/entries/<int:entry_pk>/print/', tool_views.report_card_print, name='report_card_print'),
    path('tools/report-cards/<int:pk>/print-all/', tool_views.report_card_print_all, name='report_card_print_all'),
    path('tools/report-cards/api/', tool_views.report_card_api, name='report_card_api'),

    # CompuThink Lab (Computing)
    path('tools/computhink/', tool_views.computhink_dashboard, name='computhink_dashboard'),
    path('tools/computhink/<int:pk>/delete/', tool_views.computhink_delete, name='computhink_delete'),
    path('tools/computhink/api/', tool_views.computhink_api, name='computhink_api'),

    # Literacy Toolkit (English & Language)
    path('tools/literacy/', tool_views.literacy_dashboard, name='literacy_dashboard'),
    path('tools/literacy/<int:pk>/delete/', tool_views.literacy_delete, name='literacy_delete'),
    path('tools/literacy/api/', tool_views.literacy_api, name='literacy_api'),

    # CitizenEd (Social Studies)
    path('tools/citizen-ed/', tool_views.citizen_ed_dashboard, name='citizen_ed_dashboard'),
    path('tools/citizen-ed/<int:pk>/delete/', tool_views.citizen_ed_delete, name='citizen_ed_delete'),
    path('tools/citizen-ed/api/', tool_views.citizen_ed_api, name='citizen_ed_api'),

    # TVET Workshop (Career Technology)
    path('tools/tvet/', tool_views.tvet_dashboard, name='tvet_dashboard'),
    path('tools/tvet/<int:pk>/delete/', tool_views.tvet_delete, name='tvet_delete'),
    path('tools/tvet/api/', tool_views.tvet_api, name='tvet_api'),

    # Grade Analytics
    path('tools/grades/', tool_views.grade_analytics_dashboard, name='grade_analytics_dashboard'),
    path('tools/grades/new/', tool_views.grade_book_create, name='grade_book_create'),
    path('tools/grades/<int:pk>/', tool_views.grade_book_detail, name='grade_book_detail'),
    path('tools/grades/<int:pk>/delete/', tool_views.grade_book_delete, name='grade_book_delete'),
    path('tools/grades/<int:pk>/entry/add/', tool_views.grade_entry_add, name='grade_entry_add'),
    path('tools/grades/<int:pk>/entry/<int:entry_pk>/delete/', tool_views.grade_entry_delete, name='grade_entry_delete'),
    path('tools/grades/<int:pk>/bulk-upload/', tool_views.grade_bulk_upload, name='grade_bulk_upload'),

    # Attendance Tracker
    path('tools/attendance/', tool_views.attendance_dashboard, name='attendance_dashboard'),
    path('tools/attendance/new/', tool_views.attendance_register_create, name='attendance_register_create'),
    path('tools/attendance/<int:pk>/', tool_views.attendance_register_detail, name='attendance_register_detail'),
    path('tools/attendance/<int:pk>/take/', tool_views.attendance_take, name='attendance_take'),
    path('tools/attendance/<int:pk>/delete/', tool_views.attendance_register_delete, name='attendance_register_delete'),
    path('tools/attendance/<int:pk>/add-student/', tool_views.attendance_add_student, name='attendance_add_student'),

    # Offline content
    path('tools/offline/', views.offline_manager, name='offline_manager'),
    path('tools/offline/manifest/', tool_views.offline_content_list, name='offline_content_list'),
    path('tools/lesson-plans/<int:pk>/offline/', tool_views.offline_lesson_plan, name='offline_lesson_plan'),
    path('tools/presentations/<int:pk>/offline/', tool_views.offline_deck, name='offline_deck'),
    path('tools/exam-papers/<int:pk>/offline/', tool_views.offline_exam_paper, name='offline_exam_paper'),
    path('tools/letters/<int:pk>/offline/', tool_views.offline_letter, name='offline_letter'),
    path('tools/report-cards/<int:pk>/offline/', tool_views.offline_report_card, name='offline_report_card'),
]

# Teacher shortcut URLs (included under /t/ prefix in main urls.py)
teacher_urlpatterns = [
    path('', views.teacher_redirect, name='teacher_home'),
    path('signup/', views.teacher_redirect, name='teacher_signup'),
    path('signin/', views.teacher_signin_redirect, name='teacher_signin'),
]
