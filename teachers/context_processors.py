"""
Context processor to provide teacher-specific data to templates.
"""
from django.db.models import Avg


def teacher_context(request):
    """
    Provides teacher-specific context for Aura-T panel.
    Returns empty dict if user is not authenticated or not a teacher.
    """
    context = {
        'aura_teacher_subjects': [],
        'aura_teacher_classes': [],
        'aura_class_summary': None,
        'aura_struggling_students': [],
    }
    
    if not request.user.is_authenticated:
        return context
    
    if getattr(request.user, 'user_type', None) != 'teacher':
        return context
    
    if not hasattr(request.user, 'teacher'):
        return context
    
    try:
        from academics.models import ClassSubject, AcademicYear, Subject, Class
        from students.models import Student, Grade
        
        teacher = request.user.teacher
        current_year = AcademicYear.objects.filter(is_current=True).first()
        
        # Get subjects and classes this teacher teaches
        teacher_assignments = ClassSubject.objects.filter(
            teacher=teacher
        ).select_related('subject', 'class_name')
        
        subjects = []
        classes = []
        class_ids = set()
        
        for assignment in teacher_assignments:
            if assignment.subject and assignment.subject.name not in subjects:
                subjects.append(assignment.subject.name)
            if assignment.class_name:
                class_ids.add(assignment.class_name.id)
                if assignment.class_name.name not in classes:
                    classes.append(assignment.class_name.name)
        
        context['aura_teacher_subjects'] = subjects[:5]  # Limit to 5
        context['aura_teacher_classes'] = classes[:5]
        
        # Get summary stats
        if class_ids:
            students = Student.objects.filter(current_class_id__in=class_ids)
            total_students = students.count()
            
            # Get struggling students (avg score < 50)
            subject_ids = list(teacher_assignments.values_list('subject_id', flat=True))
            struggling = []
            
            for student in students.select_related('user')[:50]:  # Limit to 50 students
                grades = Grade.objects.filter(
                    student=student, 
                    subject_id__in=subject_ids
                )
                if current_year:
                    grades = grades.filter(academic_year=current_year)
                
                scores = [g.total_score for g in grades if g.total_score is not None]
                if scores:
                    avg = sum(scores) / len(scores)
                    if avg < 50:
                        struggling.append({
                            'name': student.user.first_name or student.user.username,
                            'avg_score': round(avg, 1),
                        })
            
            context['aura_class_summary'] = {
                'total_students': total_students,
                'struggling_count': len(struggling),
            }
            context['aura_struggling_students'] = struggling[:3]  # Top 3 struggling
            
    except Exception as e:
        # Fail silently - don't break page rendering
        import logging
        logging.getLogger(__name__).debug(f"Aura context error: {e}")
    
    return context
