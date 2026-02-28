with open('teachers/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if line.startswith('import json') and lines[i+4] == '@login_required\n' and lines[i+6] == 'def aura_t_api(request):\n':
        pass
    new_lines.append(line)

# Let's just slice it until the line before the second definition
# Find the first one
first_idx = next(i for i, x in enumerate(lines) if x.startswith('def aura_t_api'))
# Find the second one
second_idx = next(i for i, x in enumerate(lines) if x.startswith('def aura_t_api') and i > first_idx)

# Go back from second_idx to find "import json"
split_idx = second_idx
while split_idx > first_idx and not lines[split_idx].startswith('import json'):
    split_idx -= 1

if split_idx > first_idx:
    with open('teachers/views.py', 'w', encoding='utf-8') as f:
        f.writelines(lines[:split_idx])
    print("Fixed!")
