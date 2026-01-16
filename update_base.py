
with open(r'd:/school_management/templates/base.html', 'w', encoding='utf-8') as f:
    f.write(r'''{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}School Management System{% endblock %}</title>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <link rel="stylesheet" href="{% static 'css/loader.css' %}">

    <style>
        :root {
            /* New School Theme */
            --primary-dark: #0f3b57;
            --primary-teal: #026e56;
            --primary-light: #e6fcf5;
            --accent-blue: #0b9cc7;
            --secondary-color: #0b9cc7; /* Mapping for legacy usage */
            --accent-color: #026e56; /* Mapping for legacy usage */
            
            --text-main: #0f172a;
            --text-muted: #64748b;
            --surface-light: #f7f9fb;
            --surface-white: #ffffff;
            
            --sidebar-width: 260px;
            --sidebar-collapsed-width: 70px;
            --card-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            
            --gradient-strong: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary-teal) 100%);
        }

        * {
            box-sizing: border-box;
        }

        body {
            font-family: 'Manrope', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--surface-light);
            color: var(--text-main);
            min-height: 100vh;
            margin: 0;
        }

        .main-container {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* Header */
        .header {
            background: #fff;
            color: var(--text-main);
            padding: 0.8rem 0;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            position: sticky;
            top: 0;
            z-index: 1000;
            border-bottom: 1px solid rgba(0,0,0,0.05);
        }

        .header .navbar-brand {
            font-weight: 800;
            font-size: 1.3rem;
            color: var(--primary-dark) !important;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .header-brand-icon {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, var(--primary-teal), var(--accent-blue));
            color: #fff;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.4rem 0.8rem;
            background: rgba(0,0,0,0.03);
            border-radius: 99px;
            color: var(--text-main);
            text-decoration: none;
            transition: all 0.2s ease;
            border: 1px solid rgba(0,0,0,0.04);
        }

        .user-info:hover {
            background: #fff;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            text-decoration: none;
            color: var(--primary-teal);
        }

        .user-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: var(--primary-dark);
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.85rem;
        }

        /* Sidebar */
        .sidebar {
            width: var(--sidebar-width);
            background: var(--primary-dark);
            color: rgba(255,255,255,0.8);
            min-height: 100vh;
            position: fixed;
            left: 0;
            top: 0;
            z-index: 999;
            box-shadow: 4px 0 24px rgba(0,0,0,0.05);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            overflow-y: auto;
            padding-top: 80px;
        }

        .sidebar h4 {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 700;
            margin: 1.5rem 1.5rem 0.75rem;
            color: rgba(255,255,255,0.4);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .sidebar h4::after {
            content: '';
            flex-grow: 1;
            height: 1px;
            background: rgba(255,255,255,0.1);
        }

        /* Navigation Links */
        .nav-item {
            margin: 4px 12px;
        }

        .nav-link {
            color: rgba(255,255,255,0.7) !important;
            padding: 0.7rem 1rem !important;
            border-radius: 8px !important;
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
            text-decoration: none !important;
            transition: all 0.2s ease !important;
            font-weight: 500 !important;
            font-size: 0.95rem;
        }

        .nav-link:hover,
        .nav-link.active {
            background: rgba(255,255,255,0.1) !important;
            color: #fff !important;
            transform: translateX(4px);
        }
        
        .nav-link.active {
            background: var(--primary-teal) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            font-weight: 600 !important;
        }

        .nav-link i {
            font-size: 1.1rem;
            width: 20px;
            text-align: center;
            opacity: 0.9;
        }

        /* Main Content Area */
        .main-content {
            margin-left: var(--sidebar-width);
            min-height: 100vh;
            padding: 2rem;
            transition: margin-left 0.3s ease;
        }

        /* Buttons and pills */
        .btn-primary, .btn-gradient {
            background: var(--primary-teal);
            border: 1px solid transparent;
            color: #fff;
            border-radius: 8px;
            padding: 0.5rem 1.2rem;
            font-weight: 600;
            box-shadow: 0 2px 5px rgba(2, 110, 86, 0.2);
            transition: all 0.2s;
        }

        .btn-primary:hover, .btn-gradient:hover {
            background: #025a46;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(2, 110, 86, 0.3);
        }

        .btn-outline-primary {
            border-color: var(--primary-teal);
            color: var(--primary-teal);
            border-radius: 8px;
            font-weight: 600;
        }

        .btn-outline-primary:hover {
            background: var(--primary-teal);
            color: #fff;
        }

        .card {
            border: 1px solid rgba(0,0,0,0.05);
            border-radius: 12px;
            box-shadow: var(--card-shadow);
            background: #fff;
        }

        /* Custom Dropdowns */
        .select-flat {
            appearance: none;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            background-color: var(--surface-white);
            color: var(--text-main);
            padding: 0.65rem 2.4rem 0.65rem 0.9rem;
            font-weight: 600;
            cursor: pointer;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%2364748b' class='bi bi-chevron-down' viewBox='0 0 16 16'%3E%3Cpath fill-rule='evenodd' d='M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 1rem center;
            background-size: 12px;
            transition: all 0.2s;
        }

        .select-flat:focus {
            border-color: var(--primary-teal);
            box-shadow: 0 0 0 3px rgba(2, 110, 86, 0.1);
            outline: none;
        }

        .select-flat--accent {
            background-color: var(--primary-light);
            color: var(--primary-teal);
            border-color: transparent;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%23026e56' class='bi bi-chevron-down' viewBox='0 0 16 16'%3E%3Cpath fill-rule='evenodd' d='M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z'/%3E%3C/svg%3E");
        }

        .form-control {
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            padding: 0.65rem 0.9rem;
        }

        .form-control:focus {
            border-color: var(--primary-teal);
            box-shadow: 0 0 0 3px rgba(2, 110, 86, 0.1);
        }

        /* Mobile specific */
        .sidebar-toggle {
            position: fixed;
            top: 85px;
            left: 16px;
            z-index: 1001;
            background: var(--primary-teal);
            color: white;
            border: none;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(2, 110, 86, 0.3);
            border: 2px solid #fff;
        }

        .mobile-bubble-menu {
            position: fixed;
            top: 70px;
            left: 12px;
            width: 280px;
            background: var(--primary-dark);
            border-radius: 16px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
            padding: 16px;
            color: #fff;
            display: none;
            z-index: 1003;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .mobile-bubble-menu.show {
            display: block;
            animation: fadeIn 0.2s;
        }
        
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }

        .mobile-bubble-list {
            list-style: none;
            padding: 0;
            margin: 0;
            margin-top: 1rem;
        }

        .mobile-bubble-item a {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            color: rgba(255,255,255,0.8);
            text-decoration: none;
            border-radius: 8px;
            transition: 0.2s;
            font-weight: 500;
        }

        .mobile-bubble-item a:hover {
            background: rgba(255,255,255,0.1);
            color: #fff;
        }

        @media (max-width: 992px) {
            .sidebar {
                transform: translateX(-100%);
            }
            .sidebar.show {
                transform: translateX(0);
            }
            .main-content {
                margin-left: 0;
            }
        }
    </style>
</head>
<body>
    <!-- Global Loading Overlay -->
    <div class="loading-overlay" id="globalLoader">
        <div class="spinner-container">
            <div class="spinner"></div>
            <div class="spinner-text">Loading...</div>
        </div>
    </div>

    <!-- Page Progress Bar -->
    <div class="page-loader" id="pageLoader"></div>

    {% if user.is_authenticated %}
    <div class="main-container">
        <!-- Header -->
        <header class="header">
            <div class="container-fluid px-4">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="navbar-brand">
                        <div class="header-brand-icon">GM</div>
                        <span>Girls Model JHS</span>
                    </div>
                    <div>
                        <a href="#" class="user-info">
                            <div class="user-avatar">
                                {{ user.get_full_name|first|upper }}
                            </div>
                            <div class="d-none d-md-block fs-6 fw-bold ps-1">
                                {{ user.get_full_name }}
                            </div>
                        </a>
                    </div>
                </div>
            </div>
        </header>

        <!-- Toggle Button for Mobile -->
        <button class="sidebar-toggle d-block d-lg-none mobile-menu-trigger" onclick="toggleMobileMenu()">
            <i class="bi bi-list fs-5"></i>
        </button>

        <!-- Mobile Bubble Menu -->
        <div class="mobile-bubble-menu" id="mobileBubbleMenu">
            <div class="d-flex justify-content-between align-items-center mb-3 pb-3 border-bottom border-secondary">
                <div class="d-flex align-items-center gap-2">
                    <div class="user-avatar" style="width: 32px; height: 32px;">{{ user.get_full_name|first|upper }}</div>
                    <span class="fw-bold">{{ user.get_full_name }}</span>
                </div>
                <button class="btn btn-sm btn-outline-light border-0" onclick="toggleMobileMenu()"><i class="bi bi-x fs-5"></i></button>
            </div>
            <ul class="mobile-bubble-list">
                <li class="mobile-bubble-item"><a href="{% url 'dashboard' %}"><i class="bi bi-speedometer2"></i>Dashboard</a></li>
                <li class="mobile-bubble-item"><a href="{% url 'home' %}"><i class="bi bi-house"></i>Home Page</a></li>
                {% if user.user_type == 'teacher' or user.user_type == 'admin' %}
                    <li class="mobile-bubble-item"><a href="{% url 'students:student_list' %}"><i class="bi bi-people"></i>Students</a></li>
                    <li class="mobile-bubble-item"><a href="{% url 'students:mark_attendance' %}"><i class="bi bi-calendar-check"></i>Attendance</a></li>
                    <li class="mobile-bubble-item"><a href="{% url 'academics:manage_activities' %}"><i class="bi bi-calendar-event"></i>Activities</a></li>
                {% endif %}
                {% if user.user_type == 'teacher' %}
                    <li class="mobile-bubble-item"><a href="{% url 'teachers:my_classes' %}"><i class="bi bi-book"></i>My Classes</a></li>
                    <li class="mobile-bubble-item"><a href="{% url 'teachers:enter_grades' %}"><i class="bi bi-journal-plus"></i>Enter Grades</a></li>
                {% endif %}
                {% if user.user_type == 'parent' %}
                <li class="mobile-bubble-item"><a href="{% url 'parents:my_children' %}"><i class="bi bi-person-hearts"></i>My Children</a></li>
                {% endif %}
                <li class="mobile-bubble-item mt-2 pt-2 border-top border-secondary opacity-75"><a href="{% url 'logout' %}"><i class="bi bi-box-arrow-right"></i>Sign Out</a></li>
            </ul>
        </div>

        <!-- Mobile Bubble Overlay -->
        <div class="mobile-bubble-overlay position-fixed top-0 start-0 w-100 h-100 bg-dark bg-opacity-50" id="mobileBubbleOverlay" style="display:none; z-index: 1002;" onclick="toggleMobileMenu()"></div>

        <!-- Sidebar -->
        <nav class="sidebar" id="sidebar">
            <h4 class="mb-2">Main Menu</h4>
            
            <div class="nav-item">
                <a href="{% url 'dashboard' %}" class="nav-link {% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}">
                    <i class="bi bi-speedometer2"></i>
                    <span>Dashboard</span>
                </a>
            </div>

            <div class="nav-item">
                <a href="{% url 'home' %}" class="nav-link {% if request.resolver_match.url_name == 'home' %}active{% endif %}">
                    <i class="bi bi-house-door"></i>
                    <span>Home Page</span>
                </a>
            </div>
            
            {% if user.user_type == 'admin' or user.user_type == 'teacher' %}
            <h4 class="mb-2 mt-4">Academic</h4>
            <div class="nav-item">
                <a href="{% url 'students:student_list' %}" class="nav-link {% if request.resolver_match.url_name == 'student_list' %}active{% endif %}">
                    <i class="bi bi-people"></i>
                    <span>Students</span>
                </a>
            </div>
            <div class="nav-item">
                <a href="{% url 'students:mark_attendance' %}" class="nav-link {% if request.resolver_match.url_name == 'mark_attendance' %}active{% endif %}">
                    <i class="bi bi-calendar-check"></i>
                    <span>Attendance</span>
                </a>
            </div>
            <div class="nav-item">
                <a href="{% url 'academics:manage_activities' %}" class="nav-link {% if request.resolver_match.url_name == 'manage_activities' %}active{% endif %}">
                    <i class="bi bi-calendar-event"></i>
                    <span>Activities</span>
                </a>
            </div>
            {% endif %}
            
            {% if user.user_type == 'teacher' %}
            <h4 class="mb-2 mt-4">Teaching</h4>
            <div class="nav-item">
                <a href="{% url 'teachers:my_classes' %}" class="nav-link {% if request.resolver_match.url_name == 'my_classes' %}active{% endif %}">
                    <i class="bi bi-book"></i>
                    <span>My Classes</span>
                </a>
            </div>
            <div class="nav-item">
                <a href="{% url 'teachers:enter_grades' %}" class="nav-link {% if request.resolver_match.url_name == 'enter_grades' %}active{% endif %}">
                    <i class="bi bi-pencil-square"></i>
                    <span>Enter Grades</span>
                </a>
            </div>
            {% endif %}
            
            {% if user.user_type == 'parent' %}
            <h4 class="mb-2 mt-4">Family</h4>
            <div class="nav-item">
                <a href="{% url 'parents:my_children' %}" class="nav-link {% if request.resolver_match.url_name == 'my_children' %}active{% endif %}">
                    <i class="bi bi-person-hearts"></i>
                    <span>My Children</span>
                </a>
            </div>
            {% endif %}
            
            <div class="mt-auto p-3 border-top border-secondary border-opacity-25">
                <a href="{% url 'logout' %}" class="nav-link text-danger-emphasis">
                    <i class="bi bi-box-arrow-right"></i>
                    <span>Logout</span>
                </a>
            </div>
        </nav>

        <!-- Main Content -->
        <main class="main-content" id="mainContent">
            {% block content %}
            {% endblock %}
        </main>
    </div>

    <!-- Mobile Sidebar Overlay (for sidebar mode) -->
    <div class="position-fixed top-0 start-0 w-100 h-100 bg-dark bg-opacity-50 d-none" id="sidebarOverlay" style="z-index: 998;" onclick="toggleSidebar()"></div>

    <!-- Toast container -->
    <div class="position-fixed top-0 end-0 p-3" style="z-index: 1200; width: 320px;" id="toastContainer"></div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        function toggleMobileMenu() {
            const menu = document.getElementById('mobileBubbleMenu');
            const overlay = document.getElementById('mobileBubbleOverlay');
            if (menu.style.display === 'block') {
                menu.style.display = 'none';
                overlay.style.display = 'none';
            } else {
                menu.style.display = 'block';
                overlay.style.display = 'block';
                menu.classList.add('show');
            }
        }

        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('show');
            document.getElementById('sidebarOverlay').classList.toggle('d-none');
        }

        // Handle window resize for overlay reset
        window.addEventListener('resize', function() {
            if (window.innerWidth > 992) {
                document.getElementById('sidebar').classList.remove('show');
                document.getElementById('sidebarOverlay').classList.add('d-none');
            }
        });

        // Toast helper
        function showToast(message, type = 'info') {
            const container = document.getElementById('toastContainer');
            if (!container) return;
            
            const bgMap = {
                success: 'bg-success text-white', 
                danger: 'bg-danger text-white', 
                warning: 'bg-warning text-dark', 
                info: 'bg-info text-white'
            };
            
            const toastEl = document.createElement('div');
            toastEl.className = `toast align-items-center border-0 ${bgMap[type] || 'bg-white'}`;
            toastEl.role = 'alert';
            toastEl.ariaLive = 'assertive';
            toastEl.ariaAtomic = 'true';
            toastEl.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body fw-medium">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>`;
            container.appendChild(toastEl);
            const toast = new bootstrap.Toast(toastEl, {delay: 3500});
            toast.show();
            toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
        }
        window.showToast = showToast;
    </script>
    <script>
        // Global loader functions
        function showLoader(message = 'Loading...') {
            const loader = document.getElementById('globalLoader');
            if(loader) {
                const text = loader.querySelector('.spinner-text');
                if(text) text.textContent = message;
                loader.classList.add('active');
            }
        }

        function hideLoader() {
            const loader = document.getElementById('globalLoader');
            if(loader) loader.classList.remove('active');
        }

        document.addEventListener('DOMContentLoaded', function() {
            // Loader logic
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                form.addEventListener('submit', function(e) {
                    // Skip forms that explicitly opt out
                    if (form.hasAttribute('data-no-loader')) return;

                    const submitBtn = form.querySelector('button[type="submit"]');
                    if (submitBtn && !submitBtn.classList.contains('no-loader')) {
                        submitBtn.classList.add('btn-loading');
                        showLoader('Processing...');
                    }
                });
            });

             // Page navigation loading
            const links = document.querySelectorAll('a:not([target="_blank"]):not([href^="#"])');
            links.forEach(link => {
                link.addEventListener('click', function(e) {
                    if (this.href && !this.dataset.noLoader && !this.href.includes('javascript:')) {
                         const pageLoader = document.getElementById('pageLoader');
                         if(pageLoader) pageLoader.classList.add('loading');
                    }
                });
            });
            
            window.addEventListener('load', function() {
                hideLoader();
                const pl = document.getElementById('pageLoader');
                if(pl) pl.classList.remove('loading');
            });
        });
        
        window.showLoader = showLoader;
        window.hideLoader = hideLoader;
    </script>
    {% else %}
    {% block login_content %}
    {% endblock %}
    {% endif %}
</body>
</html>
''')
