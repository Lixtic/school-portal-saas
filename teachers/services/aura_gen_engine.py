import json
import random
from typing import Dict, List, Optional
from django.utils import timezone
from django.conf import settings
from teachers.models import LessonPlan, Teacher
from academics.ai_tutor import _post_chat_completion

class AuraGenEngine:
    """
    Aura-T Generative Pedagogical Engine.
    Uses AI service to generate educational content.
    """

    @staticmethod
    def generate_assignment_package(lesson_plan: LessonPlan, topic_prompt: Optional[str] = None) -> Dict:
        """
        Generates a complete assignment package based on a lesson plan or topic using AI.
        """
        topic = topic_prompt if topic_prompt else lesson_plan.topic
        subject = lesson_plan.subject.name
        grade_level = lesson_plan.school_class.name
        
        # Build context from lesson plan if available
        lesson_context = ""
        if lesson_plan:
            lesson_context = f"""
            Objectives: {lesson_plan.objectives}
            Presentation: {lesson_plan.presentation}
            """

        system_prompt = f"""You are Aura-T, an expert pedagogical AI for teachers. 
        Your task is to generate a high-quality, differentiated assignment package for a {grade_level} class on the subject of {subject}.
        
        Topic: {topic}
        Context: {lesson_context}
        
        You must return a valid JSON object with the following structure:
        {{
            "assignment": {{
                "title": "Creative title for the assignment",
                "description": "Student-facing instructions",
                "content": {{
                    "visual_prompt": "Description of an image or diagram students should analyze",
                    "questions": ["Question 1", "Question 2", "Question 3"]
                }}
            }},
            "differentiation": {{
                "support": {{
                    "description": "How to support struggling learners",
                    "modifications": ["Modification 1", "Modification 2"]
                }},
                "standard": {{
                    "description": "Standard expectations",
                    "content": ["Standard Task 1", "Standard Task 2"]
                }},
                "challenge": {{
                    "description": "How to extend for advanced learners",
                    "modifications": ["Extension 1", "Extension 2"]
                }}
            }},
            "rubric": [
                {{
                    "criteria": "Criteria Name",
                    "weight": "Percentage",
                    "levels": {{
                        "excellent": "Description for top marks",
                        "proficient": "Description for passing",
                        "basic": "Description for partial credit",
                        "limited": "Description for minimum credit"
                    }}
                }}
            ]
        }}
        """

        try:
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate a creative and educational assignment package for {topic}."}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.7
            }
            
            response = _post_chat_completion(payload, settings.OPENAI_API_KEY)
            content = response['choices'][0]['message']['content']
            data = json.loads(content)
            
            # Add metadata
            return {
                "meta": {
                    "topic": topic,
                    "subject": subject,
                    "grade": grade_level,
                    "generated_at": timezone.now().isoformat()
                },
                **data
            }
            
        except Exception as e:
            print(f"AI Generation failed: {e}")
            # Fallback to mock if AI fails
            return AuraGenEngine._generate_mock_fallback(topic, subject, grade_level)

    @staticmethod
    def _generate_mock_fallback(topic: str, subject: str, grade_level: str) -> Dict:
        """
        Mock implementation as fallback.
        """
        
        base_assignment = {
            "title": f"{topic}: Apply & Analyze (Offline Mode)",
            "description": f"Based on our lesson on {topic}, complete the following tasks.",
            "learning_objectives": ["Understand core concepts"],
            "estimated_time": "30-45 minutes"
        }

        # 1. Instant Content Generation (Multimodal simulation)
        content = {
            "visual_prompt": f"Create a diagram showing the relationship between {topic} and daily life.",
            "questions": [
                f"Explain the concept of {topic} in your own words.",
                f"List three key features of {topic} discussed in class.",
                f"How does {topic} apply to the real-world scenario we discussed?"
            ]
        }

        # 2. Adaptive Differentiation
        differentiation = AuraGenEngine._generate_differentiation(topic, content)

        # 3. Rubric Co-Design
        rubric = AuraGenEngine._generate_rubric(topic)

        return {
            "meta": {
                "topic": topic,
                "subject": subject,
                "grade": grade_level,
                "generated_at": timezone.now().isoformat()
            },
            "assignment": {
                **base_assignment,
                "content": content
            },
            "differentiation": differentiation,
            "rubric": rubric
        }

    @staticmethod
    def _generate_differentiation(topic: str, base_content: Dict) -> Dict:
        """
        Creates 3 tiered versions of the assignment.
        """
        return {
            "support": {
                "label": "Support (Scaffolded)",
                "description": "Includes sentence starters and vocabulary banks.",
                "modifications": [
                    "Vocabulary Bank: [Key Term 1], [Key Term 2], [Key Term 3]",
                    "Sentence Starter: 'The most important thing about " + topic + " is...'",
                    "Matching exercise instead of open-ended definition."
                ]
            },
            "standard": {
                "label": "Standard (Core)",
                "description": "The standard assignment aligned with grade-level expectations.",
                "content": base_content["questions"]
            },
            "challenge": {
                "label": "Challenge (Extension)",
                "description": "Adds critical thinking and cross-disciplinary analysis.",
                "modifications": [
                    f"Research how {topic} intersects with [Related Field].",
                    "Design an experiment to test the principles of " + topic + ".",
                    "Write a critique of the current understanding of " + topic + "."
                ]
            }
        }

    @staticmethod
    def _generate_rubric(topic: str) -> List[Dict]:
        """
        Generates a grading rubric with success criteria.
        """
        return [
            {
                "criteria": "Conceptual Understanding",
                "weight": "40%",
                "levels": {
                    "excellent": f"Demonstrates deep understanding of {topic} with no errors.",
                    "proficient": f"Demonstrates solid understanding of {topic} with minor errors.",
                    "basic": f"Shows partial understanding of {topic}.",
                    "limited": "Struggles to define key concepts."
                }
            },
            {
                "criteria": "Application & Analysis",
                "weight": "40%",
                "levels": {
                    "excellent": "Applies concepts to new scenarios effectively and creatively.",
                    "proficient": "Applies concepts to standard scenarios correctly.",
                    "basic": "Can apply concepts with guidance.",
                    "limited": "Unable to apply concepts."
                }
            },
            {
                "criteria": "Communication",
                "weight": "20%",
                "levels": {
                    "excellent": "Clear, precise, and well-organized response.",
                    "proficient": "Generally clear response.",
                    "basic": "Response is understandable but lacks clarity.",
                    "limited": "Response is confusing or illegible."
                }
            }
        ]
