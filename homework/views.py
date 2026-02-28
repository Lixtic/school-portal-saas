from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import Homework, Question, Choice, Submission, Answer
from .forms import HomeworkForm
from teachers.models import Teacher
from students.models import Student

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
        question_text = request.POST.get('question_text')
        
        if question_text:
            question = Question.objects.create(
                homework=homework,
                text=question_text,
                points=1
            )
            
            # Process 4 choices
            correct_choice_idx = request.POST.get('correct_choice')
            
            for i in range(1, 5):
                choice_text = request.POST.get(f'choice_{i}')
                if choice_text:
                    Choice.objects.create(
                        question=question,
                        text=choice_text,
                        is_correct=(str(i) == correct_choice_idx)
                    )
            
            messages.success(request, "Question added successfully.")
            return redirect('homework:homework_add_questions', pk=pk)

    return render(request, 'homework/add_questions.html', {'homework': homework})

@login_required
def homework_solve(request, pk):
    homework = get_object_or_404(Homework, pk=pk)
    
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
        
        for question in homework.questions.all():
            selected_choice_id = request.POST.get(f'question_{question.id}')
            
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

    return render(request, 'homework/solve_homework.html', {'homework': homework})

@login_required
def homework_results(request, pk):
    homework = get_object_or_404(Homework, pk=pk)
    student = request.user.student
    submission = get_object_or_404(Submission, homework=homework, student=student)
    
    # Calculate percentage
    total_questions = homework.questions.count()
    percentage = (submission.score / total_questions * 100) if total_questions > 0 else 0
    
    return render(request, 'homework/results.html', {
        'homework': homework,
        'submission': submission,
        'percentage': round(percentage, 1),
        'answers': submission.answers.select_related('question', 'selected_choice')
    })


