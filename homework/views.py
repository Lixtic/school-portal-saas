from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum
import json
from .models import Homework, Question, Choice, Submission, Answer
from .forms import HomeworkForm
from teachers.models import Teacher
from students.models import Student
from academics.ai_tutor import _post_chat_completion

@login_required
def homework_list(request):
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
        'is_teacher': user.user_type == 'teacher'
    }
    return render(request, 'homework/homework_list.html', context)


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
            messages.success(request, "Homework assigned successfully.")
            return redirect('homework:homework_list')
    else:
        form = HomeworkForm(teacher=request.user.teacher)
        
    return render(request, 'homework/homework_form.html', {'form': form})

@login_required
def homework_detail(request, pk):
    homework = get_object_or_404(Homework, pk=pk)
    has_submitted = False
    
    if request.user.user_type == 'student':
        try:
             submission = Submission.objects.get(homework=homework, student=request.user.student)
             has_submitted = True
             return redirect('homework:homework_results', pk=pk)
        except Submission.DoesNotExist:
             pass
             
    context = {
        'homework': homework,
        'today': timezone.now().date(), 
        'questions_count': homework.questions.count(),
        'has_submitted': has_submitted
    }
    return render(request, 'homework/homework_detail.html', context)


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
        
    return render(request, 'homework/results.html', {'homework': homework, 'submission': submission, 'score_percentage': (submission.score / homework.questions.count()) * 100})

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

            if q_type not in ['mcq', 'short']:
                q_type = 'mcq'
            if dok_level not in [1, 2, 3, 4]:
                dok_level = 1

            correct_answer = ''
            if q_type == 'short':
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
    
    # Check if already submitted
    existing_submission = Submission.objects.filter(homework=homework, student=student).first()
    if existing_submission:
        return redirect('homework:homework_results', pk=pk)
        
    if request.method == 'POST':
        submission = Submission.objects.create(
            homework=homework,
            student=student
        )
        
        total_score = 0
        total_points = 0
        
        for question in questions:
            total_points += question.points
            input_value = request.POST.get(f'question_{question.id}')

            if question.question_type == 'short':
                text_response = (input_value or '').strip()
                answer = Answer.objects.create(
                    submission=submission,
                    question=question,
                    text_response=text_response,
                    is_correct=False
                )

                if text_response and question.correct_answer and settings.OPENAI_API_KEY:
                    try:
                        grading_prompt = {
                            "model": "gpt-4o-mini",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are a strict grading assistant. Return JSON with score (0 to max_points) and feedback." 
                                },
                                {
                                    "role": "user",
                                    "content": (
                                        f"Question: {question.text}\n"
                                        f"Expected answer: {question.correct_answer}\n"
                                        f"Student answer: {text_response}\n"
                                        f"Max points: {question.points}"
                                    )
                                }
                            ],
                            "response_format": {"type": "json_object"},
                            "temperature": 0.2
                        }
                        resp = _post_chat_completion(grading_prompt, settings.OPENAI_API_KEY)
                        content = resp["choices"][0]["message"]["content"]
                        data = json.loads(content)
                        ai_score = max(0, min(float(data.get("score", 0)), question.points))
                        answer.ai_score = ai_score
                        answer.ai_feedback = data.get("feedback", "")
                        answer.is_correct = ai_score >= question.points
                        answer.save()
                        total_score += ai_score
                    except Exception:
                        pass
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
        
        messages.success(request, f"Homework submitted! Your score: {total_score}")
        return redirect('homework:homework_results', pk=pk)

    return render(request, 'homework/solve_homework.html', {
        'homework': homework,
        'questions': questions,
    })

@login_required
def homework_results(request, pk):
    homework = get_object_or_404(Homework, pk=pk)
    student = request.user.student
    submission = get_object_or_404(Submission, homework=homework, student=student)
    
    # Calculate percentage
    total_points = homework.questions.aggregate(total=Sum('points'))['total'] or 0
    percentage = (submission.score / total_points * 100) if total_points > 0 else 0
    
    return render(request, 'homework/results.html', {
        'homework': homework,
        'submission': submission,
        'percentage': round(percentage, 1),
        'total_points': total_points,
        'answers': submission.answers.select_related('question', 'selected_choice')
    })


