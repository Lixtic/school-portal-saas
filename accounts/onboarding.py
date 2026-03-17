# accounts/onboarding.py
# Role-specific onboarding step definitions.
# 'trigger_view' = "app_name:url_name" resolved from request.resolver_match

ONBOARDING_STEPS = {
    'teacher': [
        {
            'id': 'view_schedule',
            'title': 'View your class schedule',
            'description': 'See all your classes for the week',
            'icon': 'bi-calendar-week',
            'url_name': 'teachers:schedule',
            'trigger_view': 'teachers:schedule',
        },
        {
            'id': 'enter_grades',
            'title': 'Enter student grades',
            'description': 'Record marks for your first assessment',
            'icon': 'bi-pencil-square',
            'url_name': 'teachers:enter_grades',
            'trigger_view': 'teachers:enter_grades',
        },
        {
            'id': 'lesson_plan',
            'title': 'Create a lesson plan',
            'description': 'Plan your first lesson with AI assistance',
            'icon': 'bi-journal-text',
            'url_name': 'teachers:lesson_plan_list',
            'trigger_view': 'teachers:lesson_plan_list',
        },
        {
            'id': 'search_students',
            'title': 'Search for a student',
            'description': 'Find any student quickly by name or ID',
            'icon': 'bi-search',
            'url_name': 'teachers:search_students',
            'trigger_view': 'teachers:search_students',
        },
    ],
    'student': [
        {
            'id': 'explore_dashboard',
            'title': 'Explore your dashboard',
            'description': 'View your grades, attendance, and XP',
            'icon': 'bi-speedometer2',
            'url_name': 'students:student_dashboard',
            'trigger_view': 'students:student_dashboard',
        },
        {
            'id': 'view_schedule',
            'title': 'Check your timetable',
            'description': 'See your class schedule for the week',
            'icon': 'bi-calendar3',
            'url_name': 'students:student_schedule',
            'trigger_view': 'students:student_schedule',
        },
        {
            'id': 'view_report_card',
            'title': 'Download your report card',
            'description': 'Get your full academic report this term',
            'icon': 'bi-file-earmark-text',
            'url_name': 'students:student_dashboard',
            'trigger_view': 'students:report_card',
        },
    ],
    'parent': [
        {
            'id': 'view_children',
            'title': "View your child's profile",
            'description': 'See grades, attendance, and fee details',
            'icon': 'bi-people-fill',
            'url_name': 'parents:my_children',
            'trigger_view': 'parents:my_children',
        },
        {
            'id': 'check_fees',
            'title': 'Review outstanding fees',
            'description': "See what's owed and payment history",
            'icon': 'bi-cash-stack',
            'url_name': 'parents:my_children',
            'trigger_view': 'parents:child_fees',
        },
        {
            'id': 'send_message',
            'title': 'Send a message to school',
            'description': 'Contact admin or teachers directly',
            'icon': 'bi-chat-dots',
            'url_name': 'parents:send_message',
            'trigger_view': 'parents:send_message',
        },
    ],
    'admin': [
        {
            'id': 'add_teacher',
            'title': 'Add your first teacher',
            'description': 'Build your teaching staff roster',
            'icon': 'bi-person-badge',
            'url_name': 'teachers:add_teacher',
            'trigger_view': 'teachers:add_teacher',
        },
        {
            'id': 'manage_fees',
            'title': 'Set up fee structures',
            'description': 'Configure school fees and collectors',
            'icon': 'bi-wallet2',
            'url_name': 'finance:manage_fees',
            'trigger_view': 'finance:manage_fees',
        },
        {
            'id': 'view_analytics',
            'title': 'Explore school analytics',
            'description': 'Get AI-powered performance insights',
            'icon': 'bi-graph-up',
            'url_name': 'accounts:school_analytics',
            'trigger_view': 'accounts:school_analytics',
        },
    ],
}
