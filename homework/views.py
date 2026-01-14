from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import Homework
from .forms import HomeworkForm
from students.models import Student
from teachers.models import Teacher

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
        return redirect('homework_list')
        
    if request.method == 'POST':
        form = HomeworkForm(request.POST, request.FILES, teacher=request.user.teacher)
        if form.is_valid():
            homework = form.save(commit=False)
            homework.teacher = request.user.teacher
            homework.save()
            messages.success(request, "Homework assigned successfully.")
            return redirect('homework_list')
    else:
        form = HomeworkForm(teacher=request.user.teacher)
        
    return render(request, 'homework/homework_form.html', {'form': form})

@login_required
def homework_detail(request, pk):
    homework = get_object_or_404(Homework, pk=pk)
    # Optional: Check permission (Teacher owner, or Student in class)
    context = {
        'homework': homework,
        'today': timezone.now().date()
    }
    return render(request, 'homework/homework_detail.html', context)

@login_required
def homework_delete(request, pk):
    homework = get_object_or_404(Homework, pk=pk)
    if request.user.user_type != 'teacher' or homework.teacher.user != request.user:
        messages.error(request, "Access denied.")
        return redirect('homework_list')
        
    if request.method == 'POST':
        homework.delete()
        messages.success(request, "Homework deleted.")
        return redirect('homework_list')
        
    return render(request, 'homework/confirm_delete.html', {'object': homework})

