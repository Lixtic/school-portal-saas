import re

files = [
    'templates/students/add_student.html',
    'templates/teachers/add_teacher.html',
    'templates/teachers/edit_teacher.html'
]

bg_css = '''
{% block extra_css %}
<style>
    /* Gorgeous page background */
    .page-bg-fixed {
        position: fixed;
        inset: 0;
        width: 100vw;
        height: 100vh;
        background-image: url('https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&q=80&w=2070');
        background-size: cover;
        background-position: center;
        opacity: 0.12;
        pointer-events: none;
        z-index: 0;
    }
    [data-bs-theme="dark"] .page-bg-fixed {
        opacity: 0.05;
        filter: grayscale(0.5);
    }
    .form-page-content {
        position: relative;
        z-index: 1;
    }
</style>
{% endblock %}
'''

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    if "page-bg-fixed" in text:
        continue

    # Insert extra_css right before block content
    pattern = re.compile(r'{% block content %}')
    
    # We also need to wrap the contents of block content in .form-page-content if it's not already handled
    # But since block content usually just contains divs, we can make .form-page-content a wrapper
    # Actually, we can just add a div inside the block content and assume we close it at the end? NO, what if it's complex?
    # Safer: Just apply position: relative; z-index: 1; to .row or .container-fluid directly inside the block, or inject it right under block content.
    
    # Wait, add_student.html already has block extra_css.
    pass
