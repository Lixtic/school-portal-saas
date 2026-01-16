"""
AI Tutor Assistant - Personalized learning chatbot for students
"""
import os
import json
from openai import OpenAI
from django.utils import timezone


def get_tutor_system_prompt(student, subject=None):
    """Generate context-aware system prompt for AI tutor"""
    
    context = f"""You are an expert AI tutor helping {student.user.get_full_name()}, a student in {student.current_class.name if student.current_class else 'school'}.

Your role:
- Provide clear, age-appropriate explanations
- Break down complex topics into simple steps
- Ask guiding questions to help students think critically
- Offer encouragement and positive reinforcement
- Adapt explanations based on student's understanding level

Guidelines:
- Use simple language suitable for the student's grade level
- Include examples and analogies when explaining concepts
- Check for understanding before moving to next concepts
- Never give direct answers to homework - guide students to find answers themselves
- Be patient, supportive, and enthusiastic about learning
"""
    
    if subject:
        context += f"\n\nCurrent Subject Focus: {subject.name}"
        if subject.description:
            context += f"\nSubject Description: {subject.description}"
    
    # Add student's enrolled subjects
    if student.current_class:
        enrolled_subjects = student.current_class.subjects.all()
        if enrolled_subjects:
            context += f"\n\nStudent's Subjects: {', '.join([s.name for s in enrolled_subjects])}"
    
    context += "\n\nAlways maintain an encouraging, supportive tone. Make learning fun and engaging!"
    
    return context


def stream_tutor_response(messages, student, subject=None):
    """
    Stream AI tutor responses using OpenAI
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        yield "data: " + json.dumps({
            "error": "AI Tutor is not configured. Please contact your administrator."
        }) + "\n\n"
        return
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Build conversation with system prompt
        conversation = [
            {"role": "system", "content": get_tutor_system_prompt(student, subject)}
        ]
        conversation.extend(messages)
        
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation,
            stream=True,
            temperature=0.7,
            max_tokens=1000,
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield "data: " + json.dumps({
                    "content": chunk.choices[0].delta.content
                }) + "\n\n"
        
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        yield "data: " + json.dumps({
            "error": f"AI Tutor error: {str(e)}"
        }) + "\n\n"


def generate_practice_questions(subject, topic, difficulty="medium", count=5):
    """Generate practice questions for a subject/topic"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return {"error": "AI Tutor not configured"}
    
    try:
        client = OpenAI(api_key=api_key)
        
        prompt = f"""Generate {count} {difficulty} difficulty practice questions for:
Subject: {subject.name}
Topic: {topic}

Requirements:
- Questions should be clear and educational
- Include a mix of multiple choice, short answer, and problem-solving
- Appropriate for the subject level
- Include correct answers and brief explanations

Format as JSON:
{{
    "questions": [
        {{
            "type": "multiple_choice",
            "question": "...",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "B",
            "explanation": "..."
        }}
    ]
}}"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        return {"error": str(e)}


def explain_concept(subject, concept):
    """Get detailed explanation of a concept"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return "AI Tutor not configured"
    
    try:
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Explain this {subject.name} concept in a clear, student-friendly way with examples: {concept}"
            }],
            temperature=0.7,
            max_tokens=800
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error: {str(e)}"
