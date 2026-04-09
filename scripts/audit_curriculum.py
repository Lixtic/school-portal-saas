"""Audit curriculum JSON data quality: empty statements, missing exemplars, term coverage."""
import json
import glob

print("=== Content Standards with EMPTY statements ===")
total_cs = 0
empty_cs = 0
for f in sorted(glob.glob('curriculum/data/*.json')):
    d = json.load(open(f, encoding='utf-8'))
    name = f.replace('\\', '/').split('/')[-1]
    empty = []
    total = 0
    for g in d['grades']:
        for s in g['strands']:
            for ss in s['sub_strands']:
                for cs in ss['content_standards']:
                    total += 1
                    total_cs += 1
                    if not cs.get('statement', '').strip():
                        empty.append(cs['code'])
                        empty_cs += 1
    if empty:
        shown = empty[:5]
        suffix = '...' if len(empty) > 5 else ''
        print(f"  {name}: {len(empty)}/{total} empty — {shown}{suffix}")
print(f"  TOTAL: {empty_cs}/{total_cs} CS with empty statements")

print("\n=== Sample CS statements (first 3 per subject) ===")
seen_subjects = set()
for f in sorted(glob.glob('curriculum/data/*.json')):
    d = json.load(open(f, encoding='utf-8'))
    name = f.replace('\\', '/').split('/')[-1]
    if name[:2] != 'b7':
        continue
    count = 0
    for g in d['grades']:
        for s in g['strands']:
            for ss in s['sub_strands']:
                for cs in ss['content_standards']:
                    if cs.get('statement', '').strip() and count < 3:
                        print(f"  {name} {cs['code']}: {cs['statement'][:80]}")
                        count += 1
    if count == 0:
        print(f"  {name}: (no CS statements found)")

print("\n=== Indicators with EMPTY statements ===")
total_ind = 0
empty_ind = 0
for f in sorted(glob.glob('curriculum/data/*.json')):
    d = json.load(open(f, encoding='utf-8'))
    name = f.replace('\\', '/').split('/')[-1]
    empty = []
    total = 0
    for g in d['grades']:
        for s in g['strands']:
            for ss in s['sub_strands']:
                for cs in ss['content_standards']:
                    for ind in cs['indicators']:
                        total += 1
                        total_ind += 1
                        if not ind.get('statement', '').strip():
                            empty.append(ind['code'])
                            empty_ind += 1
    if empty:
        shown = empty[:5]
        suffix = '...' if len(empty) > 5 else ''
        print(f"  {name}: {len(empty)}/{total} empty — {shown}{suffix}")
print(f"  TOTAL: {empty_ind}/{total_ind} indicators with empty statements")
