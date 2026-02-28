import sys

with open('teachers/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'if student.parent:' in line:
        new_lines.append(line.replace('if student.parent:', 'parent = student.parents.first()\n              if parent:'))
    elif 'parent_name = student.parent.user.get_full_name() or student.parent.user.username' in line:
        new_lines.append(line.replace('parent_name = student.parent.user.get_full_name() or student.parent.user.username', 'parent_name = parent.user.get_full_name() or parent.user.username'))
    else:
        new_lines.append(line)

with open('teachers/views.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fixed parent relation logic attempt 3.")
