with open('templates/parents/add_parent.html', 'r', encoding='utf-8') as f:
    text = f.read()

bg_css = '''
    .page-bg-fixed {
        position: fixed; inset: 0; width: 100vw; height: 100vh;
        background-image: url('https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&q=80&w=2070');
        background-size: cover; background-position: center;
        opacity: 0.12; pointer-events: none; z-index: 0;
    }
    [data-bs-theme="dark"] .page-bg-fixed { opacity: 0.05; filter: grayscale(0.5); }
    .content-wrapper { position: relative; z-index: 1; }
'''

idx_style = text.find('</style>')
text = text[:idx_style] + bg_css + text[idx_style:]

text = text.replace('{% block content %}\n<div class="container-fluid py-3">', '{% block content %}\n<div class="page-bg-fixed"></div>\n<div class="container-fluid py-3 content-wrapper">')

with open('templates/parents/add_parent.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("done add_parent")
