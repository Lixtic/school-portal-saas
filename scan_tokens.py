import tokenize, io

data = open('teachers/views.py', 'rb').read()
lines = data.split(b'\n')
tq = bytes([34, 34, 34])

# Print all triple-quote lines in range 2600-2780
print("=== Triple-quote lines 2600-2780 ===")
for i in range(2600, 2780):
    if tq in lines[i]:
        print(f"L{i+1}: {repr(lines[i])[:80]}")

# Also scan for any triple-quotes before line 2700
print("\n=== All triple-quote occurrences in file with odd-numbered balance ===")
count = 0
for i, line in enumerate(lines):
    occurrences = line.count(tq)
    if occurrences:
        count += occurrences
        print(f"L{i+1} ({occurrences}x, total={count}): {repr(line)[:80]}")
    if i > 2780:
        break
