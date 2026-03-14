from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum
import json
import re
import math
import csv
from decimal import Decimal
from .models import Homework, Question, Choice, Submission, Answer
from .forms import HomeworkForm
from teachers.models import Teacher
from students.models import Student, Grade
from academics.models import AcademicYear
from academics.ai_tutor import _post_chat_completion, get_openai_chat_model


def _normalize_text(value):
    return re.sub(r'\s+', ' ', (value or '').strip().lower())


def _token_frequency(text):
    frequencies = {}
    for token in re.findall(r'\w+', _normalize_text(text)):
        if len(token) <= 2:
            continue
        frequencies[token] = frequencies.get(token, 0) + 1
    return frequencies


def _cosine_similarity(text_a, text_b):
    freq_a = _token_frequency(text_a)
    freq_b = _token_frequency(text_b)
    if not freq_a or not freq_b:
        return 0.0

    dot = 0.0
    for token, count in freq_a.items():
        dot += count * freq_b.get(token, 0)

    mag_a = math.sqrt(sum(count * count for count in freq_a.values()))
    mag_b = math.sqrt(sum(count * count for count in freq_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _extract_json_payload(content):
    raw = (content or '').strip()
    if not raw:
        return {}
    if raw.startswith('```'):
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
    start = raw.find('{')
    end = raw.rfind('}')
    if start != -1 and end != -1 and end >= start:
        raw = raw[start:end + 1]
    return json.loads(raw)


def _strictness_for_question(question):
    if question.question_type == 'essay':
        return 'High'
    return 'High' if int(getattr(question, 'dok_level', 1) or 1) >= 3 else 'Low'


def _build_grading_prompt(question_text, student_answer, rubric_constraints, strictness):
    system_prompt = (
        "### ROLE DEFINITION\n"
        "You are an Expert Pedagogical Assessor. Your task is to evaluate a student's submission against a provided Question and Rubric. "
        "You must be objective, identifying specific evidence for every point awarded or deducted.\n\n"
        "### EVALUATION PROTOCOL\n"
        "1. Decompose the student answer into atomic claims.\n"
        "2. Verify each claim against the rubric as MATCH, ERROR, or NOISE.\n"
        "3. Identify missing rubric concepts.\n"
        "4. Compute final score as a percentage.\n\n"
        "### OUTPUT FORMAT\n"
        "Return ONLY valid JSON with this schema:\n"
        "{\n"
        "  \"thinking_process\": \"Brief summary of verification steps\",\n"
        "  \"claims_verified\": [\"...\"],\n"
        "  \"errors_detected\": [\"...\"],\n"
        "  \"missing_concepts\": [\"...\"],\n"
        "  \"final_score\": 0-100,\n"
        "  \"feedback\": \"Constructive, 2-sentence feedback addressing missing concepts.\"\n"
        "}"
    )

    user_prompt = (
        f"- Question: {question_text}\n"
        f"- Student Answer: {student_answer}\n"
        f"- Rubric/Answer Key: {rubric_constraints}\n"
        f"- Strictness Level: {strictness} (Low = forgive minor phrasing errors; High = exact terminology required)"
    )

    return {
        "model": get_openai_chat_model(),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
    }


def _fallback_short_score(student_answer, expected_answer, max_points):
    student_norm = _normalize_text(student_answer)
    expected_norm = _normalize_text(expected_answer)

    if not student_norm or not expected_norm:
        return 0.0, "No score awarded due to missing expected answer or response."

    if student_norm == expected_norm:
        return float(max_points), "Exact match with expected answer."

    similarity = _cosine_similarity(student_norm, expected_norm)
    if similarity <= 0:
        return 0.0, "Could not evaluate keywords from expected answer."

    score = round(float(max_points) * similarity, 2)
    if similarity >= 0.78:
        feedback = "Strong keyword match with expected answer."
    elif similarity >= 0.45:
        feedback = "Partial match with expected answer."
    else:
        feedback = "Limited match with expected answer."

    return score, feedback

@login_required
def homework_list(request):
    from datetime import timedelta
    user = request.user
    homeworks = []
    
    if user.user_type == 'teacher':
        try:
            teacher = user.teacher
            homeworks = Homework.objects.filter(teacher=teacher)
        except Teacher.DoesNotExist:
            pass
            
    elif user.user_type == 'student':
        try:
            student = user.student
            if student.current_class:
                homeworks = Homework.objects.filter(target_class=student.current_class)
                # Annotate with submission status if needed, but for now simple list
        except Student.DoesNotExist:
            pass
            
    elif user.user_type == 'parent':
        from parents.models import Parent
        try:
            parent = Parent.objects.get(user=user)
            children = parent.children.all()
            # Collect homeworks for all children
            classes = [child.current_class for child in children if child.current_class]
            homeworks = Homework.objects.filter(target_class__in=classes)
        except Parent.DoesNotExist:
            pass
    elif user.user_type == 'admin':
        homeworks = Homework.objects.select_related('subject', 'target_class', 'teacher', 'teacher__user')
        
    context = {
        'homeworks': homeworks,
        'is_teacher': user.user_type == 'teacher',
        'today': timezone.now().date(),
        'new_since': timezone.now() - timedelta(hours=24),
    }
    return render(request, 'homework/homework_list.html', context)


@login_required
def student_notes_list(request):
    """List class notes (key concepts) for the current user's class or teacher."""
    from .models import ClassNote
    user = request.user
    notes = ClassNote.objects.none()

    if user.user_type == 'student':
        try:
            student = user.student
            if student.current_class:
                notes = ClassNote.objects.filter(
                    target_class=student.current_class
                ).select_related('teacher__user', 'source_deck')
        except Student.DoesNotExist:
            pass
    elif user.user_type == 'teacher':
        try:
            teacher = user.teacher
            notes = ClassNote.objects.filter(
                teacher=teacher
            ).select_related('target_class', 'source_deck')
        except Teacher.DoesNotExist:
            pass
    elif user.user_type in ('admin', 'parent'):
        notes = ClassNote.objects.select_related('teacher__user', 'target_class', 'source_deck')

    return render(request, 'homework/class_notes.html', {'notes': notes})



@login_required
def homework_create(request):
    if request.user.user_type != 'teacher':
        messages.error(request, "Access denied. Only teachers can create homework.")
        return redirect('homework:homework_list')
        
    if request.method == 'POST':
        form = HomeworkForm(request.POST, request.FILES, teacher=request.user.teacher)
        if form.is_valid():
            homework = form.save(commit=False)
            homework.teacher = request.user.teacher
            homework.save()
            # Notify all students in the target class
            from announcements.models import Notification as HWNotification
            students_in_class = Student.objects.filter(
                current_class=homework.target_class
            ).select_related('user')
            hw_notifications = [
                HWNotification(
                    recipient=s.user,
                    message=f"\U0001f4da New assignment: \u201c{homework.title}\u201d \u2013 due {homework.due_date.strftime('%b %d')}",
                    alert_type='announcement',
                )
                for s in students_in_class
            ]
            if hw_notifications:
                HWNotification.objects.bulk_create(hw_notifications, ignore_conflicts=True)
            messages.success(request, "Homework assigned successfully.")
            return redirect('homework:homework_list')
    else:
        # Pre-populate from SOW topic link: ?topic=...&class_id=...&subject_id=...
        initial = {}
        pre_topic = request.GET.get('topic', '').strip()
        pre_class = request.GET.get('class_id', '').strip()
        pre_subject = request.GET.get('subject_id', '').strip()
        if pre_topic:
            initial['title'] = pre_topic
            initial['description'] = f"Complete exercises related to the topic: {pre_topic}"
        if pre_class:
            try:
                from academics.models import Class as AClass
                initial['target_class'] = AClass.objects.get(pk=int(pre_class))
            except Exception:
                pass
        if pre_subject:
            try:
                from academics.models import Subject as ASubject
                initial['subject'] = ASubject.objects.get(pk=int(pre_subject))
            except Exception:
                pass
        form = HomeworkForm(initial=initial, teacher=request.user.teacher)
        
    return render(request, 'homework/homework_form.html', {'form': form})

@login_required
def homework_detail(request, pk):
    homework = get_object_or_404(Homework, pk=pk)
    has_submitted = False
    best_submission = None

    if request.user.user_type == 'student':
        try:
            best_submission = (
                Submission.objects.filter(homework=homework, student=request.user.student)
                .order_by('-score')
                .first()
            )
            has_submitted = best_submission is not None
        except Exception:
            pass

    context = {
        'homework': homework,
        'today': timezone.now().date(),
        'questions_count': homework.questions.count(),
        'has_submitted': has_submitted,
        'best_submission': best_submission,
        'questions': homework.questions.prefetch_related('choices').all(),
    }
    return render(request, 'homework/homework_detail.html', context)


@login_required
def homework_edit(request, pk):
    homework = get_object_or_404(Homework, pk=pk)
    if request.user.user_type != 'teacher' or homework.teacher.user != request.user:
        messages.error(request, "Access denied. You can only edit your own assignments.")
        return redirect('homework:homework_list')

    if request.method == 'POST':
        form = HomeworkForm(request.POST, request.FILES, instance=homework, teacher=request.user.teacher)
        if form.is_valid():
            form.save()
            messages.success(request, "Assignment updated successfully.")
            return redirect('homework:homework_detail', pk=homework.pk)
    else:
        form = HomeworkForm(instance=homework, teacher=request.user.teacher)

    return render(request, 'homework/homework_form.html', {'form': form, 'homework': homework})


@login_required
def homework_delete(request, pk):
    homework = get_object_or_404(Homework, pk=pk)
    if request.user.user_type != 'teacher' or homework.teacher.user != request.user:
        messages.error(request, "Access denied.")
        return redirect('homework:homework_list')
        
    if request.method == 'POST':
        homework.delete()
        messages.success(request, "Homework deleted.")
        return redirect('homework:homework_list')
    # Show a simple confirmation page for deletion
    return render(request, 'homework/confirm_delete.html', {'homework': homework})

@login_required
def homework_ai_generate(request):
    """AJAX endpoint: generate questions via AI for a given topic/settings."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if request.user.user_type != 'teacher':
        return JsonResponse({'error': 'Access denied'}, status=403)

    data = json.loads(request.body or '{}')
    topic        = (data.get('topic') or '').strip()
    subject      = (data.get('subject') or '').strip()
    grade_level  = (data.get('grade_level') or '').strip()
    num_q        = min(max(int(data.get('num_questions') or 5), 1), 20)
    q_type       = (data.get('question_type') or 'mixed').strip().lower()
    dok_min      = int(data.get('dok_min') or 1)
    dok_max      = int(data.get('dok_max') or 2)
    curriculum   = (data.get('curriculum') or 'GES').strip()

    # Build type distribution description
    type_desc = {
        'mcq':   f'{num_q} multiple-choice questions (4 options each, exactly 1 correct)',
        'short': f'{num_q} short-answer questions',
        'essay': f'{num_q} essay / open-ended questions',
        'mixed': (
            f'a mix of question types: roughly 60% multiple-choice (4 options, 1 correct), '
            f'25% short-answer, 15% essay. Total: {num_q} questions'
        ),
    }.get(q_type, f'{num_q} multiple-choice questions (4 options each, exactly 1 correct)')

    system_msg = (
        'You are an expert curriculum designer for the {curriculum} school system. '
        'Generate quiz/assignment questions that are age-appropriate, pedagogically sound, '
        'and aligned to the specified DOK (Depth of Knowledge) levels.\n'
        'CRITICAL: Return ONLY a valid JSON object — no markdown, no prose, no code fences.'
    ).format(curriculum=curriculum)

    user_msg = (
        f'Generate {type_desc} on the topic "{topic}"\n'
        f'Subject: {subject or "General"}\n'
        f'Grade / Class: {grade_level or "Not specified"}\n'
        f'DOK levels: {dok_min} – {dok_max} (distribute questions across this range)\n'
        f'Curriculum: {curriculum}\n\n'
        'Return a JSON object with this exact schema:\n'
        '{\n'
        '  "questions": [\n'
        '    {\n'
        '      "text": "<question text>",\n'
        '      "type": "mcq" | "short" | "essay",\n'
        '      "dok_level": 1-4,\n'
        '      "points": 1-5,\n'
        '      "choices": ["A", "B", "C", "D"],  // only for mcq, else []\n'
        '      "correct_index": 0,               // 0-based index, only for mcq\n'
        '      "correct_answer": "<rubric/key>"   // for short and essay\n'
        '    }\n'
        '  ]\n'
        '}'
    )

    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    payload = {
        'model': get_openai_chat_model(),
        'messages': [
            {'role': 'system', 'content': system_msg},
            {'role': 'user',   'content': user_msg},
        ],
        'response_format': {'type': 'json_object'},
        'temperature': 0.7,
        'max_tokens': 3000,
    }

    try:
        response = _post_chat_completion(payload, api_key)
        raw = response['choices'][0]['message']['content']
        result = _extract_json_payload(raw)
        questions = result.get('questions', [])

        # Normalise and validate each question
        cleaned = []
        for i, q in enumerate(questions):
            q_type_out = q.get('type', 'mcq')
            if q_type_out not in ('mcq', 'short', 'essay'):
                q_type_out = 'mcq'
            dok = int(q.get('dok_level') or 1)
            if dok not in (1, 2, 3, 4):
                dok = 1
            choices = q.get('choices') or []
            correct_index = int(q.get('correct_index') or 0)
            if correct_index >= len(choices):
                correct_index = 0
            cleaned.append({
                'text':          q.get('text', f'Question {i+1}'),
                'type':          q_type_out,
                'dok_level':     dok,
                'points':        min(max(int(q.get('points') or 1), 1), 10),
                'choices':       choices,
                'correct_index': correct_index,
                'correct_answer': q.get('correct_answer', ''),
            })

        return JsonResponse({'questions': cleaned})

    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)


@login_required
def homework_add_questions(request, pk):
    homework = get_object_or_404(Homework, pk=pk)
    if request.user.user_type != 'teacher':
        messages.error(request, "Access denied.")
        return redirect('homework:homework_list')
        
    if request.method == 'POST':
        created_count = 0

        question_keys = [k for k in request.POST.keys() if k.startswith('question_text_')]
        if not question_keys and request.POST.get('question_text'):
            question_keys = ['question_text']

        for key in sorted(question_keys):
            if key == 'question_text':
                q_idx = ''
                question_text = (request.POST.get('question_text') or '').strip()
                q_type = 'mcq'
                dok_level = 1
            else:
                q_idx = key.split('question_text_')[-1]
                question_text = (request.POST.get(key) or '').strip()
                q_type = (request.POST.get(f'question_type_{q_idx}') or 'mcq').strip().lower()
                try:
                    dok_level = int(request.POST.get(f'dok_level_{q_idx}', 1))
                except (TypeError, ValueError):
                    dok_level = 1

            if not question_text:
                continue

            if q_type not in ['mcq', 'short', 'essay']:
                q_type = 'mcq'
            if dok_level not in [1, 2, 3, 4]:
                dok_level = 1

            correct_answer = ''
            if q_type in ['short', 'essay']:
                correct_answer = (request.POST.get(f'expected_answer_{q_idx}') or '').strip()

            question = Question.objects.create(
                homework=homework,
                text=question_text,
                points=1,
                question_type=q_type,
                dok_level=dok_level,
                correct_answer=correct_answer,
            )

            if q_type == 'mcq':
                choice_keys = [k for k in request.POST.keys() if k.startswith(f'choice_text_{q_idx}_')]
                has_correct = False
                for c_key in sorted(choice_keys):
                    c_idx = c_key.split(f'choice_text_{q_idx}_')[-1]
                    choice_text = (request.POST.get(c_key) or '').strip()
                    if not choice_text:
                        continue
                    is_correct = request.POST.get(f'is_correct_{q_idx}_{c_idx}') in ['on', 'true', '1']
                    if is_correct:
                        has_correct = True
                    Choice.objects.create(
                        question=question,
                        text=choice_text,
                        is_correct=is_correct,
                    )

                if not has_correct:
                    first_choice = question.choices.first()
                    if first_choice:
                        first_choice.is_correct = True
                        first_choice.save(update_fields=['is_correct'])

            created_count += 1

        if created_count > 0:
            messages.success(request, f"{created_count} question(s) added successfully.")
            return redirect('homework:homework_add_questions', pk=pk)
        messages.warning(request, "No valid questions were submitted.")

    existing_questions = homework.questions.prefetch_related('choices').all()
    return render(request, 'homework/add_questions.html', {
        'homework': homework,
        'existing_questions': existing_questions,
    })

@login_required
def homework_solve(request, pk):
    homework = get_object_or_404(Homework, pk=pk)
    questions = homework.questions.prefetch_related('choices').all()

    # Ensure student context
    if request.user.user_type != 'student':
        messages.error(request, "Only students can solve homework.")
        return redirect('homework:homework_detail', pk=pk)

    student = request.user.student
    from django.utils import timezone as _tz

    # Determine if this is a retry attempt
    existing_submissions = Submission.objects.filter(homework=homework, student=student).order_by('-attempt_number')
    latest = existing_submissions.first()

    # Allow fresh attempt if retry is permitted and last score was below 50%
    is_retry = False
    attempt_number = 1
    if latest:
        total_pts = homework.questions.aggregate(total=Sum('points'))['total'] or 0
        last_pct = float(latest.score) / float(total_pts) * 100 if total_pts > 0 else 0
        if homework.allow_retry and last_pct < 50:
            is_retry = True
            attempt_number = latest.attempt_number + 1
        else:
            return redirect('homework:homework_results', pk=pk)

    # Mark late if past due date
    _is_late = homework.due_date < _tz.localdate()

    if request.method == 'POST':
        submission = Submission.objects.create(
            homework=homework,
            student=student,
            is_late=_is_late,
            attempt_number=attempt_number,
        )
        
        total_score = 0
        total_points = 0
        
        for question in questions:
            total_points += question.points
            input_value = request.POST.get(f'question_{question.id}')

            if question.question_type in ['short', 'essay']:
                text_response = (input_value or '').strip()
                answer = Answer.objects.create(
                    submission=submission,
                    question=question,
                    text_response=text_response,
                    is_correct=False
                )

                short_score = 0.0
                short_feedback = ""

                if text_response and question.correct_answer and settings.OPENAI_API_KEY:
                    try:
                        grading_prompt = _build_grading_prompt(
                            question_text=question.text,
                            student_answer=text_response,
                            rubric_constraints=question.correct_answer,
                            strictness=_strictness_for_question(question),
                        )
                        resp = _post_chat_completion(grading_prompt, settings.OPENAI_API_KEY)
                        content = resp["choices"][0]["message"]["content"]
                        data = _extract_json_payload(content)
                        final_score = float(data.get("final_score", 0) or 0)
                        bounded_percentage = max(0.0, min(final_score, 100.0))
                        short_score = round((bounded_percentage / 100.0) * float(question.points), 2)

                        feedback_text = (data.get("feedback") or "").strip()
                        missing_concepts = data.get("missing_concepts") or []
                        if isinstance(missing_concepts, list):
                            missing_concepts = [str(item).strip() for item in missing_concepts if str(item).strip()]
                        else:
                            missing_concepts = []

                        if feedback_text and missing_concepts:
                            short_feedback = f"{feedback_text} Missing concepts: {', '.join(missing_concepts[:3])}."
                        elif feedback_text:
                            short_feedback = feedback_text
                        elif missing_concepts:
                            short_feedback = f"Missing concepts: {', '.join(missing_concepts[:3])}."
                        else:
                            short_feedback = "Answer evaluated against rubric constraints."
                    except Exception:
                        short_score, short_feedback = _fallback_short_score(text_response, question.correct_answer, question.points)
                elif text_response and question.correct_answer:
                    short_score, short_feedback = _fallback_short_score(text_response, question.correct_answer, question.points)

                answer.ai_score = short_score
                answer.ai_feedback = short_feedback
                answer.is_correct = short_score >= question.points
                answer.save(update_fields=['ai_score', 'ai_feedback', 'is_correct'])
                total_score += short_score
            else:
                selected_choice_id = input_value
                if selected_choice_id:
                    try:
                        choice = Choice.objects.get(id=selected_choice_id, question=question)
                        is_correct = choice.is_correct
                        if is_correct:
                            total_score += question.points
                            
                        Answer.objects.create(
                            submission=submission,
                            question=question,
                            selected_choice=choice,
                            is_correct=is_correct
                        )
                    except Choice.DoesNotExist:
                        pass
                else:
                    # Unanswered
                    Answer.objects.create(
                        submission=submission,
                        question=question,
                        is_correct=False
                    )
        
        submission.score = total_score
        submission.save()

        # ── Gamification: award XP for homework completion ────────────────
        try:
            _hw_total_points = homework.questions.aggregate(total=Sum('points'))['total'] or 0
            if _hw_total_points > 0:
                _pct = float(total_score) / float(_hw_total_points) * 100
                if _pct >= 50:
                    _xp_amount = max(5, min(25, int(_pct / 4)))  # 12–25 XP range
                    from academics.gamification_models import StudentXP, check_and_unlock_achievements
                    from announcements.models import Notification
                    _xp_profile, _ = StudentXP.objects.get_or_create(student=student)
                    _leveled_up = _xp_profile.add_xp(_xp_amount)
                    _xp_profile.update_streak()
                    _extra = ['homework-ace'] if _pct >= 90 else []
                    check_and_unlock_achievements(student, _xp_profile, extra_slugs=_extra)
                    if _leveled_up:
                        Notification.objects.create(
                            recipient=student.user,
                            message=f'⭐ Level Up! You reached Level {_xp_profile.level} — keep it up!',
                            alert_type='general',
                            link='../../students/aura-portfolio/',
                        )
        except Exception:
            pass  # Gamification must never break homework submission
        # ────────────────────────────────────────────────────────────────────

        messages.success(request, f"Homework submitted! Your score: {total_score}")
        return redirect('homework:homework_results', pk=pk)

    return render(request, 'homework/solve_homework.html', {
        'homework': homework,
        'questions': questions,
        'is_retry': is_retry,
        'attempt_number': attempt_number,
        'is_late': _is_late,
    })

@login_required
def homework_results(request, pk):
    homework = get_object_or_404(Homework, pk=pk)
    student = request.user.student

    # Get best (highest-scoring) submission for display
    submissions = Submission.objects.filter(homework=homework, student=student).order_by('-score')
    submission = submissions.first()
    if not submission:
        return redirect('homework:homework_solve', pk=pk)

    total_points = homework.questions.aggregate(total=Sum('points'))['total'] or 0
    percentage = float(submission.score) / float(total_points) * 100 if total_points > 0 else 0

    # Can retry?
    can_retry = homework.allow_retry and percentage < 50

    # All attempts (for attempt history)
    all_attempts = list(submissions.order_by('attempt_number').values(
        'attempt_number', 'score', 'submitted_at', 'is_late'
    ))

    return render(request, 'homework/results.html', {
        'homework': homework,
        'submission': submission,
        'percentage': round(percentage, 1),
        'total_points': total_points,
        'answers': submission.answers.select_related('question', 'selected_choice'),
        'can_retry': can_retry,
        'all_attempts': all_attempts,
    })


@login_required
def homework_class_results(request, pk):
    """Teacher-only view: class-wide results for a homework assignment."""
    homework = get_object_or_404(Homework, pk=pk)

    # Access control: teacher who owns the HW, or admin
    if request.user.user_type == 'teacher':
        try:
            teacher = Teacher.objects.get(user=request.user)
            if homework.teacher != teacher:
                messages.error(request, "You can only view results for your own assignments.")
                return redirect('homework:homework_detail', pk=pk)
        except Teacher.DoesNotExist:
            return redirect('homework:homework_list')
    elif request.user.user_type != 'admin':
        messages.error(request, "Access denied.")
        return redirect('homework:homework_detail', pk=pk)

    total_points = homework.questions.aggregate(total=Sum('points'))['total'] or 0

    submissions = Submission.objects.filter(homework=homework).select_related('student__user')
    
    results = []
    for sub in submissions:
        pct = round(float(sub.score) / float(total_points) * 100, 1) if total_points > 0 else 0
        results.append({
            'student': sub.student,
            'score': sub.score,
            'percentage': pct,
            'submitted_at': sub.submitted_at,
            'grade': ('A' if pct >= 80 else 'B' if pct >= 70 else 'C' if pct >= 60 else 'D' if pct >= 50 else 'F'),
        })

    # Sort by percentage descending
    results.sort(key=lambda r: r['percentage'], reverse=True)

    # Class-wide stats
    class_size = homework.target_class.student_set.count() if homework.target_class else 0
    submission_count = len(results)
    avg_pct = round(sum(r['percentage'] for r in results) / submission_count, 1) if submission_count else 0
    top_score_pct = results[0]['percentage'] if results else 0
    pass_count = sum(1 for r in results if r['percentage'] >= 50)

    # Per-question stats: correct-answer rate
    questions = homework.questions.prefetch_related('choices').all()
    question_stats = []
    for q in questions:
        correct = q.answer_set.filter(is_correct=True).count()
        attempts = q.answer_set.count()
        question_stats.append({
            'question': q,
            'correct': correct,
            'attempts': attempts,
            'rate': round(correct / attempts * 100, 0) if attempts else 0,
        })

    return render(request, 'homework/class_results.html', {
        'homework': homework,
        'results': results,
        'total_points': total_points,
        'class_size': class_size,
        'submission_count': submission_count,
        'avg_pct': avg_pct,
        'top_score_pct': top_score_pct,
        'pass_count': pass_count,
        'question_stats': question_stats,
        'late_count': sum(1 for s in Submission.objects.filter(homework=homework) if s.is_late),
        'q_chart_json': json.dumps([{
            'label': f'Q{i+1}',
            'correct': qs_item['correct'],
            'incorrect': qs_item['attempts'] - qs_item['correct'],
            'rate': qs_item['rate'],
        } for i, qs_item in enumerate(question_stats)]),
    })


@login_required
def homework_push_grades(request, pk):
    """Push homework scores into the Grade gradebook (class_score, scaled to 30 pts)."""
    homework = get_object_or_404(Homework, pk=pk)

    # Access: teacher owner or admin
    if request.user.user_type == 'teacher':
        try:
            teacher = Teacher.objects.get(user=request.user)
            if homework.teacher != teacher:
                messages.error(request, "You can only push grades for your own assignments.")
                return redirect('homework:homework_class_results', pk=pk)
        except Teacher.DoesNotExist:
            return redirect('homework:homework_list')
    elif request.user.user_type != 'admin':
        messages.error(request, "Access denied.")
        return redirect('homework:homework_class_results', pk=pk)

    TERM_CHOICES = [('first', 'First Term'), ('second', 'Second Term'), ('third', 'Third Term')]

    if request.method == 'POST':
        term = request.POST.get('term', 'first')
        if term not in dict(TERM_CHOICES):
            messages.error(request, "Invalid term selected.")
            return redirect('homework:homework_push_grades', pk=pk)

        academic_year = AcademicYear.objects.filter(is_current=True).first()
        if not academic_year:
            messages.error(request, "No active academic year found. Please set one in Academics.")
            return redirect('homework:homework_class_results', pk=pk)

        total_points = homework.questions.aggregate(total=Sum('points'))['total'] or 0
        submissions = Submission.objects.filter(homework=homework).select_related('student')

        pushed = 0
        updated = 0
        for sub in submissions:
            pct = float(sub.score) / float(total_points) * 100 if total_points > 0 else 0
            # Scale to 30-point class-work contribution (Ghana curriculum: class 30%, exams 70%)
            class_score_value = Decimal(str(round(pct * 30 / 100, 2)))

            _, created = Grade.objects.update_or_create(
                student=sub.student,
                subject=homework.subject,
                academic_year=academic_year,
                term=term,
                defaults={
                    'class_score': class_score_value,
                    'created_by': request.user,
                }
            )
            if created:
                pushed += 1
            else:
                updated += 1

        messages.success(
            request,
            f"Grades pushed to gradebook: {pushed} new, {updated} updated "
            f"({term.title()} Term, {academic_year.name})."
        )
        return redirect('homework:homework_class_results', pk=pk)

    # GET: show confirmation form with term selector
    context = {
        'homework': homework,
        'term_choices': TERM_CHOICES,
        'submission_count': Submission.objects.filter(homework=homework).count(),
    }
    return render(request, 'homework/push_grades_confirm.html', context)


@login_required
def homework_export_csv(request, pk):
    """Download class results for a homework assignment as a CSV file."""
    homework = get_object_or_404(Homework, pk=pk)

    # Access control — same as class_results
    if request.user.user_type == 'teacher':
        try:
            teacher = Teacher.objects.get(user=request.user)
            if homework.teacher != teacher:
                messages.error(request, "You can only export results for your own assignments.")
                return redirect('homework:homework_class_results', pk=pk)
        except Teacher.DoesNotExist:
            return redirect('homework:homework_list')
    elif request.user.user_type != 'admin':
        messages.error(request, "Access denied.")
        return redirect('homework:homework_class_results', pk=pk)

    total_points = homework.questions.aggregate(total=Sum('points'))['total'] or 0
    submissions = Submission.objects.filter(homework=homework).select_related('student__user')

    response = HttpResponse(content_type='text/csv')
    safe_title = re.sub(r'[^\w\s-]', '', homework.title)[:40].strip().replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="results_{safe_title}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Admission No', 'Score', 'Total Points', 'Percentage', 'Grade', 'Submitted At'])

    rows = []
    for sub in submissions:
        pct = round(float(sub.score) / float(total_points) * 100, 1) if total_points > 0 else 0
        grade_letter = 'A' if pct >= 80 else 'B' if pct >= 70 else 'C' if pct >= 60 else 'D' if pct >= 50 else 'F'
        rows.append((sub.student.user.get_full_name(), getattr(sub.student, 'admission_number', ''), sub.score, total_points, pct, grade_letter, sub.submitted_at.strftime('%Y-%m-%d %H:%M')))

    rows.sort(key=lambda r: r[4], reverse=True)
    for row in rows:
        writer.writerow(row)

    return response

