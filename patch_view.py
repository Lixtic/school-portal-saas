import re

with open('teachers/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Instead of blindly replacing simulate AI generation, let's use regex to replace that whole block carefully
pattern = re.compile(
    r"    # Check for AI generation request\n    initial_data = \{\}\n    topic = request\.GET\.get\('topic'\)\n    if topic:\n        # Simulate AI generation\n        initial_data = \{[\s\S]*?messages\.info\(request, f\"AI has drafted a lesson plan for \'\{topic\}'\. Please review and edit\.\"\)",
    re.MULTILINE
)

new_block = '''    # Check for AI generation request (either from topic or structured text)
    initial_data = {}
    
    # Try the new draft session parsing logic
    draft_session = request.GET.get('draft_session')
    if draft_session:
        session = get_object_or_404(LessonGenerationSession, id=draft_session, teacher=teacher)
        # Find the last assistant message
        draft_text = ""
        for msg in reversed(session.messages):
            if msg.get('role') == 'assistant':
                draft_text = msg.get('content', '')
                break
                
        if draft_text:
            from .ges_lessonplan import parse_ges_lesson_text
            parsed_data = parse_ges_lesson_text(draft_text)
            if parsed_data:
                initial_data = parsed_data
                messages.info(request, "Loaded structured AI draft. Please review and edit.")
            else:
                initial_data['introduction'] = draft_text
                messages.info(request, "Loaded AI draft text. Please review and edit.")
                
    # Fallback to simple topic generation
    elif request.GET.get('topic'):
        topic = request.GET.get('topic')
        initial_data = {
            'topic': topic,
            'objectives': f"By the end of the lesson, students will be able to:\\n1. Understand the core concepts of {topic}.\\n2. Apply {topic} to solve simple problems.",
            'introduction': f"Begin with a 5-minute warm-up activity related to {topic}.",
            'presentation': f"1. Define {topic} and key terminology.\\n2. Demonstrate the main concept.",
            'evaluation': f"Distribute a short worksheet on {topic}.",
            'homework': f"Read the chapter on {topic}.",
            'teaching_materials': f"Textbook, Whiteboard"
        }
        messages.info(request, f"AI has drafted a simple outline for '{topic}'. Please review.")'''

text = pattern.sub(new_block, text)

with open('teachers/views.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Check complete")
