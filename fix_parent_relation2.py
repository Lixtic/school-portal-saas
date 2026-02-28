import sys

with open('teachers/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Trying the exact string to replace
old_logic = "if student.parent:\n                  parent_name = student.parent.user.get_full_name() or student.parent.user.username"
new_logic = "parent = student.parents.first()\n              if parent:\n                  parent_name = parent.user.get_full_name() or parent.user.username"

text = text.replace(old_logic, new_logic)

with open('teachers/views.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed parent relation logic attempt 2.")
