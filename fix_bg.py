import re

files_with_form_page = ['templates/students/add_student.html']
files_with_no_css = ['templates/teachers/add_teacher.html', 'templates/teachers/edit_teacher.html']

bg_css_form_page = '''
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
    .form-page { 
        position: relative; 
        z-index: 1; 
        max-width: 680px; 
        margin: 0 auto; 
        padding: 1.5rem 1rem; 
    }
'''

for file_path in files_with_form_page:
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    if 'page-bg-fixed' not in text:
        text = re.sub(r'\.form-page \{ max-width: 680px; margin: 0 auto; padding: 1\.5rem 1rem; \}', bg_css_form_page, text)
        text = text.replace('{% block content %}', '{% block content %}\n<div class="page-bg-fixed"></div>')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'{file_path} updated')

bg_css_block = '''
{% block extra_css %}
<style>
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
    .content-wrapper { position: relative; z-index: 1; }
</style>
{% endblock %}
'''

for file_path in files_with_no_css:
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    if 'page-bg-fixed' not in text:
        text = text.replace('{% block content %}', bg_css_block + '\n{% block content %}\n<div class="page-bg-fixed"></div>\n<div class="content-wrapper">')
        text = text.replace('{% endblock %}', '</div>\n{% endblock %}')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'{file_path} updated')

