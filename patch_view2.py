import re

with open('teachers/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix unterminated f-strings (they need triple quotes if they contain newlines)
text = text.replace('f"By the end of the lesson, students will be able to:\n1. Understand the core concepts of {topic}.\n2. Apply {topic} to solve simple problems."', 'f"By the end of the lesson, students will be able to:\\n1. Understand the core concepts of {topic}.\\n2. Apply {topic} to solve simple problems."')
text = text.replace('f"1. Define {topic} and key terminology.\n2. Demonstrate the main concept."', 'f"1. Define {topic} and key terminology.\\n2. Demonstrate the main concept."')

with open('teachers/views.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed f-string error")
