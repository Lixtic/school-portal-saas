import sys

with open('teachers/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace student.parent with student.parents.first() since it's a related_name on Parent.children ManyToManyField
old_logic = '''              # Draft parent updates
              if student.parent:
                  parent_name = student.parent.user.get_full_name() or student.parent.user.username
                  if status == 'struggling':'''

new_logic = '''              # Draft parent updates
              parent = student.parents.first()
              if parent:
                  parent_name = parent.user.get_full_name() or parent.user.username
                  if status == 'struggling':'''

text = text.replace(old_logic, new_logic)

with open('teachers/views.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed parent relation logic.")
