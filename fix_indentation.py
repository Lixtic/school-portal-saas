import sys

with open('teachers/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for index, line in enumerate(lines):
    if line.startswith('              if parent:'):
        new_lines.append('            if parent:\n')
    elif line.startswith('                    parent_name = parent.user.get_full_name() or parent.user.username'):
        new_lines.append('                parent_name = parent.user.get_full_name() or parent.user.username\n')
    else:
        new_lines.append(line)

with open('teachers/views.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
