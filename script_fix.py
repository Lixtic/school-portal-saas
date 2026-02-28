with open('templates/academics/school_settings_new.html', 'r', encoding='utf-8') as f:
    text = f.read()

new_prefix = '''{% block extra_css %}
<style>
    .page-bg-fixed {
        position: fixed; inset: 0; width: 100vw; height: 100vh;
        background-image: url('https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&q=80&w=2070');
        background-size: cover; background-position: center;
        opacity: 0.12; pointer-events: none; z-index: 0;
    }
    [data-bs-theme="dark"] .page-bg-fixed { opacity: 0.05; filter: grayscale(0.5); }
    .content-wrapper { position: relative; z-index: 1; }
</style>
{% endblock %}

{% block content %}
<div class="page-bg-fixed"></div>
<div class="content-wrapper">
<style>'''

text = text.replace('{% block content %}\n<style>', new_prefix)
idx = text.rfind('{% endblock %}')
text = text[:idx] + '</div>\n' + text[idx:]

with open('templates/academics/school_settings_new.html', 'w', encoding='utf-8') as f:
    f.write(text)

