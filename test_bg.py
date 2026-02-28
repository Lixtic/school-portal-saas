import re

with open('templates/students/edit_student.html', 'r', encoding='utf-8') as f:
    text = f.read()

bg_css = '''
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
        opacity: 0.06;
        filter: grayscale(0.5);
    }
    .form-page { 
        position: relative; 
        z-index: 1; 
        max-width: 680px; 
        margin: 0 auto; 
        padding: 1.5rem 1rem; 
    }
'''

# Replace .form-page { max-width: 680px; margin: 0 auto; padding: 1.5rem 1rem; } with g_css
text = re.sub(r'\.form-page \{ max-width: 680px; margin: 0 auto; padding: 1\.5rem 1rem; \}', bg_css, text)

# Add <div class="page-bg-fixed"></div> inside {% block content %} at the top
text = text.replace('{% block content %}', '{% block content %}\n<div class="page-bg-fixed"></div>')

with open('templates/students/edit_student.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Injected test bg")
