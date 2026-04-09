#!/usr/bin/env python3
"""Temporary audit: list empty and noisy CS statements."""
import json, glob

files = sorted(glob.glob('curriculum/data/b*.json'))

print('=== EMPTY CS ===')
for f in files:
    d = json.load(open(f, encoding='utf-8'))
    fname = f.replace('\\', '/').split('/')[-1]
    for g in d['grades']:
        for s in g['strands']:
            for ss in s['sub_strands']:
                for cs in ss['content_standards']:
                    stmt = cs.get('statement', '').strip()
                    if not stmt:
                        print(f'  {fname}: {cs["code"]} -> EMPTY')

print()
print('=== NOISY CS ===')
noise_words = ['Thinking and', 'Collaboration (', '( pat', '( and',
               'Creativity and Inno', '( (', 'Thinking (']
for f in files:
    d = json.load(open(f, encoding='utf-8'))
    fname = f.replace('\\', '/').split('/')[-1]
    for g in d['grades']:
        for s in g['strands']:
            for ss in s['sub_strands']:
                for cs in ss['content_standards']:
                    stmt = cs.get('statement', '').strip()
                    if stmt and any(x in stmt for x in noise_words):
                        print(f'  {fname}: {cs["code"]} -> {stmt[:120]}')

print()
print('=== STATS ===')
total = 0
empty = 0
noisy_count = 0
for f in files:
    d = json.load(open(f, encoding='utf-8'))
    for g in d['grades']:
        for s in g['strands']:
            for ss in s['sub_strands']:
                for cs in ss['content_standards']:
                    total += 1
                    stmt = cs.get('statement', '').strip()
                    if not stmt:
                        empty += 1
                    elif any(x in stmt for x in noise_words):
                        noisy_count += 1
print(f'Total: {total}, Empty: {empty}, Noisy: {noisy_count}, Clean: {total - empty - noisy_count}')
