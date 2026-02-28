import re
import codecs

with open('teachers/ges_lessonplan.py', 'rb') as f:
    raw = f.read()
    
if raw.startswith(codecs.BOM_UTF16_LE):
    text = raw.decode('utf-16-le')
elif raw.startswith(codecs.BOM_UTF16_BE):
    text = raw.decode('utf-16-be')
else:
    text = raw.decode('utf-8', errors='ignore')

# Fix parsing of PHASE 2 and PHASE 3. The current regex cuts off at \n PHASE x, but we need it to be non-greedy and catch everything until the next PHASE literal
# Also fix the weird characters in the file if present

# Update parse_ges_lesson_text

pattern = re.compile(r"def parse_ges_lesson_text.*", re.DOTALL)
new_func = '''def parse_ges_lesson_text(text: str) -> Dict[str, str]:
    """Best-effort parser that extracts key fields from a GES-formatted lesson text."""
    if not text:
        return {}

    compact_text = text.replace("\\r\\n", "\\n")
    compact_text = re.sub(r"[*_#]", "", compact_text)
    compact_text = re.sub(r"\\n{3,}", "\\n\\n", compact_text)

    def _search(pattern, flags=re.IGNORECASE | re.DOTALL):
        match = re.search(pattern, compact_text, flags)
        return match.group(1).strip() if match else ""

    week_number = _search(r"WEEK\\s*(\\d+)")
    subject = _search(r"(?:Subject|SUBJECT)\\s*:\\s*(.+?)(?:\\n|$)")
    class_level = _search(r"(?:Class|Class Level)\\s*:\\s*([^\\n]+?)(?:\\s+Class Size:|\\n|$)")
    content_standard = _search(r"Content Standard\\s*:\\s*(.+?)(?:\\n|Indicator:|$)")
    indicator = _search(r"Indicator\\s*:\\s*(.+?)(?:\\n|Lesson:|$)")
    performance_indicator = _search(r"Performance Indicator\\s*:\\s*(.+?)(?:\\n|Core Competencies:|$)")
    
    # Extract phases using lookahead to match everything until the next phase or end of string
    phase_1_starter = _search(r"PHASE\\s*1\\s*:\\s*STARTER\\s*(.+?)(?=\\n\\s*PHASE|$)")
    phase_2_new = _search(r"PHASE\\s*2\\s*:\\s*(?:NEW LEARNING|NEW)\\s*(.+?)(?=\\n\\s*PHASE|$)")
    phase_3_reflection = _search(r"PHASE\\s*3\\s*:\\s*REFLECTION\\s*(.+?)(?=\\n\\s*PHASE|$)")
    
    reference = _search(r"Reference:\\s*(.+?)(?:\\n|$)")

    if not phase_1_starter:
        phase_1_starter = _search(r"Starter\\s*(?:\\(.*?\\))?\\s*:\\s*(.+?)(?:\\n|$)")
    if not phase_2_new:
        phase_2_new = _search(r"(?:New Learning|Presentation|Activity)\\s*(?:\\(.*?\\))?\\s*:\\s*(.+?)(?:\\n|$)")
    if not phase_3_reflection:
        phase_3_reflection = _search(r"(?:Reflection|Assessment|Evaluation)\\s*(?:\\(.*?\\))?\\s*:\\s*(.+?)(?:\\n|$)")

    topic = indicator or subject or "GES AI Draft Lesson"
    objectives = performance_indicator or ""

    return {
        "week_number": week_number,
        "subject": subject,
        "class_level": class_level,
        "content_standard": content_standard,
        "indicator": indicator,
        "topic": topic,
        "objectives": objectives,
        "introduction": phase_1_starter,
        "presentation": phase_2_new,
        "evaluation": phase_3_reflection,
        "teaching_materials": reference,
    }
'''

text = pattern.sub(new_func, text)

with open('teachers/ges_lessonplan.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated parser")
