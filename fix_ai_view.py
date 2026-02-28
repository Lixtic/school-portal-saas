import sys, re
with open('teachers/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_str = '''@login_required
def ai_sessions_list(request):
    if not hasattr(request.user, 'teacher'):
         messages.error(request, "Access restricted to teachers.")
         return redirect('dashboard')
         
    teacher = request.user.teacher
    sessions = LessonGenerationSession.objects.filter(teacher=teacher).order_by('-updated_at')
    return render(request, 'teachers/ai_sessions_list.html', {'sessions': sessions})'''

new_str = '''@login_required
def ai_sessions_list(request):
    if not hasattr(request.user, 'teacher'):
         messages.error(request, "Access restricted to teachers.")
         return redirect('dashboard')
         
    teacher = request.user.teacher
    sessions = LessonGenerationSession.objects.filter(teacher=teacher).order_by('-updated_at')
    
    from academics.models import ClassSubject, AcademicYear
    from students.models import Student, Grade
    from parents.models import Parent
    
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get subjects this teacher teaches
    teacher_subjects = list(ClassSubject.objects.filter(teacher=teacher).values_list('subject_id', flat=True))
    
    # Get classes this teacher teaches
    teacher_classes = list(ClassSubject.objects.filter(teacher=teacher).values_list('class_name_id', flat=True))
    
    # Try fetching real students
    students = Student.objects.filter(current_class_id__in=teacher_classes).select_related('user')
    student_data = []
    
    struggling_count = 0
    on_target_count = 0
    excelling_count = 0
    
    parent_updates = []
    
    class_name_display = "All Classes"
    if students.exists():
        classes_names = set(Student.objects.filter(id__in=students).values_list('current_class__name', flat=True))
        class_name_display = ", ".join(filter(None, classes_names))
        
        for student in students:
            # Check grades for this teacher's subjects
            grades = Grade.objects.filter(student=student, subject_id__in=teacher_subjects)
            if current_year:
                grades = grades.filter(academic_year=current_year)
            
            # Simple heuristic
            total_scores = [g.total_score for g in grades if getattr(g, 'total_score', None)]
            avg_score = sum(total_scores)/len(total_scores) if total_scores else None
            
            status = 'good' # default 'Progressing'
            if avg_score is not None:
                if avg_score >= 80: 
                    status = 'excellent'
                    excelling_count += 1
                elif avg_score < 50: 
                    status = 'struggling'
                    struggling_count += 1
                else: 
                    on_target_count += 1
            else:
                on_target_count += 1
                
            student_data.append({
                'id': student.id,
                'name': student.user.get_full_name() or student.user.username,
                'status': status,
                'avg_score': avg_score,
                'tooltip': f"Avg Score: {avg_score:.1f}%" if avg_score else "No grades yet."
            })
            
            # Draft parent updates
            if student.parent:
                parent_name = student.parent.user.get_full_name() or student.parent.user.username
                if status == 'struggling':
                    draftMsg = f"Hi {parent_name}, {student.user.first_name} is having some challenges with recent topics. Let's work together to provide additional support."
                elif status == 'excellent':
                    draftMsg = f"Hi {parent_name}, {student.user.first_name} is doing exceptionally well! Keep up the great work at home."
                else:
                    draftMsg = f"Hi {parent_name}, {student.user.first_name} is progressing smoothly and staying on target."
                    
                parent_updates.append({
                    'parent_name': parent_name,
                    'student_name': student.user.first_name,
                    'draft': draftMsg
                })
    else:
        # Mock Data for testing the UI when there are no real students
        class_name_display = "Basic 8 Science (Mock)"
        student_data = [
            {'name': 'Kwame', 'status': 'good', 'tooltip': 'Progressing well.'},
            {'name': 'Efia', 'status': 'excellent', 'tooltip': 'Excelling. Target Achieved.'},
            {'name': 'Kofi', 'status': 'struggling', 'tooltip': "Struggling with 'Factoring'. Used 'Hint' 4 times."},
            {'name': 'Yaw', 'status': 'good', 'tooltip': 'Progressing well.'},
            {'name': 'Adjoa', 'status': 'good', 'tooltip': 'Progressing well.'},
            {'name': 'Zainab', 'status': 'excellent', 'tooltip': 'Excelling. Target Achieved.'},
            {'name': 'Ama', 'status': 'struggling', 'tooltip': "Requires help with core concepts."},
            {'name': 'Kweku', 'status': 'good', 'tooltip': 'Progressing well.'},
            {'name': 'Abena', 'status': 'excellent', 'tooltip': 'Excelling. Target Achieved.'},
            {'name': 'Esi', 'status': 'good', 'tooltip': 'Progressing well.'},
            {'name': 'Kwesi', 'status': 'struggling', 'tooltip': "Requires help with core concepts."},
            {'name': 'Akosua', 'status': 'good', 'tooltip': 'Progressing well.'},
        ]
        struggling_count = 3
        on_target_count = 6
        excelling_count = 3
        
        parent_updates = [
            {'parent_name': "Mr. Osei", 'student_name': "Ama", 'draft': "Hi Mr. Osei, Ama did great with 'Friction' today, but she's still a bit confused about 'Mass.' Here is a video link..."},
            {'parent_name': "Mrs. Mensah", 'student_name': "Kofi", 'draft': "Hi Mrs. Mensah, Kofi is struggling with 'Negative Coefficients'. I have assigned him to a remedial group tomorrow..."}
        ]
        
    context = {
        'sessions': sessions,
        'student_data': student_data,
        'struggling_count': struggling_count,
        'on_target_count': on_target_count,
        'excelling_count': excelling_count,
        'class_name_display': class_name_display,
        'parent_updates': parent_updates
    }
    return render(request, 'teachers/ai_sessions_list.html', context)'''

# Replace normalize crlf
text = text.replace(old_str.replace('\n', '\r\n'), new_str)
text = text.replace(old_str, new_str)

with open('teachers/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated view")
