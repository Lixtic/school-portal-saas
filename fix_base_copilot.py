with open('templates/base.html', 'r', encoding='utf-8') as f:
    text = f.read()

old_str = "{% if not request.user.is_authenticated or request.user.user_type != 'student' %}"
new_str = "{% if not request.user.is_authenticated or request.user.user_type not in 'student,teacher' %}"

text = text.replace(old_str, new_str)

with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated base.html")
