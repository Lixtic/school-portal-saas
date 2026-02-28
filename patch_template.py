import re

with open('templates/teachers/lesson_plan_detail.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Make the presentation/activity badge and area bigger.
# Also fix presentation format by wrapping it in a better layout
# We want it to respect newlines exactly as is. linebreaks does this, but keeping it inside a div is good.
# For our new format, the lesson procedure part "Presentation" often has phases.
# Let's adjust styles for the presentation.

text = text.replace(
    '<div class="ps-3 border-start border-3 border-primary">\n                                    {{ lesson_plan.presentation|linebreaks }}\n                                </div>',
    '<div class="ps-3 border-start border-3 border-primary" style="white-space: pre-wrap; font-family: inherit;">\n                                    {{ lesson_plan.presentation|safe }}\n                                </div>'
)

# Also let's do safe for others just in case the AI generated bolding (markdown isn't rendered but maybe some formatting is).
text = text.replace('{{ lesson_plan.introduction|linebreaks }}', '{{ lesson_plan.introduction|safe|linebreaksbr }}')
text = text.replace('{{ lesson_plan.presentation|linebreaks }}', '{{ lesson_plan.presentation|safe|linebreaksbr }}')
text = text.replace('{{ lesson_plan.evaluation|linebreaks }}', '{{ lesson_plan.evaluation|safe|linebreaksbr }}')

with open('templates/teachers/lesson_plan_detail.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated template")
