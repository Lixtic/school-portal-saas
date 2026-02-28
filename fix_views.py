import re

with open('teachers/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all occurrences of the function
pattern = r'(import json\s+from django\.http import JsonResponse\s+from django\.views\.decorators\.csrf import csrf_exempt\s+@login_required\s+@csrf_exempt\s+def aura_t_api\(request\):.*?return JsonResponse\(\{''error'': ''Invalid request''\}, status=400\))'
matches = list(re.finditer(pattern, content, re.DOTALL))

if len(matches) > 1:
    # Keep the first one and remove subsequent ones
    first_match_end = matches[0].end()
    rest = content[first_match_end:]
    for match in matches[1:]:
        rest = rest.replace(match.group(0), '')
    with open('teachers/views.py', 'w', encoding='utf-8') as f:
        f.write(content[:first_match_end] + rest)
    print(f"Removed {len(matches)-1} duplicate(s).")
else:
    print("No duplicates found.")
