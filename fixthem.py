import re
with open('templates/students/edit_student.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'<div class="page-bg-fixed"></div>\n', '', text)
text = text.replace('{% block content %}', '{% block content %}\n<div class="page-bg-fixed"></div>')

with open('templates/students/edit_student.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed edit_student')
