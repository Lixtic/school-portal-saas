"""
Test ID card generation functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from students.models import Student
from teachers.models import Teacher
from academics.tutor_models import generate_student_id_card, generate_teacher_id_card
from pathlib import Path

def test_student_id_cards():
    """Generate ID cards for all students"""
    print("\n📚 Testing Student ID Card Generation...")
    print("-" * 50)
    
    students = Student.objects.all()[:3]  # Get first 3 students
    
    if not students:
        print("❌ No students found in database")
        return False
    
    output_dir = Path("id_cards/students")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, student in enumerate(students, 1):
        try:
            card = generate_student_id_card(student)
            filename = f"{output_dir}/student_{student.id}_{student.user.get_full_name().replace(' ', '_')}.png"
            card.save(filename)
            print(f"✅ {i}. Generated: {student.user.get_full_name()} (ID: STU-{student.id:06d})")
            print(f"   → Saved to: {filename}")
        except Exception as e:
            print(f"❌ {i}. Error generating card for {student.user.get_full_name()}: {str(e)}")
            return False
    
    print(f"\n✨ Successfully generated {len(students)} student ID cards")
    return True


def test_teacher_id_cards():
    """Generate ID cards for all teachers"""
    print("\n👨‍🏫 Testing Teacher ID Card Generation...")
    print("-" * 50)
    
    teachers = Teacher.objects.all()[:3]  # Get first 3 teachers
    
    if not teachers:
        print("❌ No teachers found in database")
        return False
    
    output_dir = Path("id_cards/teachers")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, teacher in enumerate(teachers, 1):
        try:
            card = generate_teacher_id_card(teacher)
            filename = f"{output_dir}/teacher_{teacher.id}_{teacher.user.get_full_name().replace(' ', '_')}.png"
            card.save(filename)
            subjects = ", ".join([s.name for s in teacher.subjects.all()[:2]])
            print(f"✅ {i}. Generated: {teacher.user.get_full_name()} (ID: TCH-{teacher.id:06d})")
            print(f"   → Subjects: {subjects if subjects else 'N/A'}")
            print(f"   → Saved to: {filename}")
        except Exception as e:
            print(f"❌ {i}. Error generating card for {teacher.user.get_full_name()}: {str(e)}")
            return False
    
    print(f"\n✨ Successfully generated {len(teachers)} teacher ID cards")
    return True


def test_single_card(user_type='student', user_id=1):
    """Generate a single ID card for testing"""
    print(f"\n🔍 Testing Single {user_type.upper()} ID Card...")
    print("-" * 50)
    
    try:
        if user_type.lower() == 'student':
            student = Student.objects.get(id=user_id)
            card = generate_student_id_card(student)
            filename = f"id_cards/test_student_{student.id}.png"
            card.save(filename)
            print(f"✅ Student: {student.user.get_full_name()}")
            print(f"   ID: STU-{student.id:06d}")
            print(f"   Class: {student.current_class.name if student.current_class else 'N/A'}")
            print(f"   Email: {student.user.email}")
            print(f"   Saved to: {filename}")
        else:
            teacher = Teacher.objects.get(id=user_id)
            card = generate_teacher_id_card(teacher)
            filename = f"id_cards/test_teacher_{teacher.id}.png"
            card.save(filename)
            subjects = ", ".join([s.name for s in teacher.subjects.all()])
            print(f"✅ Teacher: {teacher.user.get_full_name()}")
            print(f"   ID: TCH-{teacher.id:06d}")
            print(f"   Subjects: {subjects if subjects else 'N/A'}")
            print(f"   Email: {teacher.user.email}")
            print(f"   Saved to: {filename}")
        return True
    except (Student.DoesNotExist, Teacher.DoesNotExist):
        print(f"❌ {user_type.capitalize()} with ID {user_id} not found")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def show_available_users():
    """Display available students and teachers"""
    print("\n📋 Available Users in Database:")
    print("-" * 50)
    
    students = Student.objects.all()[:5]
    teachers = Teacher.objects.all()[:5]
    
    if students:
        print("\nStudents:")
        for student in students:
            print(f"  • ID {student.id}: {student.user.get_full_name()} ({student.current_class.name if student.current_class else 'No Class'})")
    else:
        print("❌ No students found")
    
    if teachers:
        print("\nTeachers:")
        for teacher in teachers:
            subjects = ", ".join([s.name for s in teacher.subjects.all()[:2]])
            print(f"  • ID {teacher.id}: {teacher.user.get_full_name()} (Subjects: {subjects if subjects else 'None'})")
    else:
        print("❌ No teachers found")


if __name__ == '__main__':
    print("\n" + "="*50)
    print("🎓 ID Card Generation Test Suite")
    print("="*50)
    
    # Show available users
    show_available_users()
    
    # Run tests
    print("\n" + "="*50)
    print("Running Tests...")
    print("="*50)
    
    student_success = test_student_id_cards()
    teacher_success = test_teacher_id_cards()
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Summary")
    print("="*50)
    print(f"Student ID Cards: {'✅ PASSED' if student_success else '❌ FAILED'}")
    print(f"Teacher ID Cards: {'✅ PASSED' if teacher_success else '❌ FAILED'}")
    print(f"\nID cards saved to: {os.path.abspath('id_cards/')}")
    print("="*50 + "\n")
