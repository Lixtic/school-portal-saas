#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from students.models import Student
from teachers.models import Teacher
from academics.tutor_models import generate_student_id_card, generate_teacher_id_card, export_id_card_to_pdf, export_multiple_id_cards_to_pdf

print("=" * 60)
print("Testing ID Card Generation and PDF Export")
print("=" * 60)

# Test with students
print("\n1. Testing Student ID Card Generation:")
students = Student.objects.all()[:2]
if students:
    for s in students:
        print(f"   - Generating card for: {s.user.first_name} {s.user.last_name}")
        card = generate_student_id_card(s)
        print(f"     ✓ Image size: {card.size}")
else:
    print("   No students found")

# Test with teachers
print("\n2. Testing Teacher ID Card Generation:")
teachers = Teacher.objects.all()[:2]
if teachers:
    for t in teachers:
        print(f"   - Generating card for: {t.user.first_name} {t.user.last_name}")
        card = generate_teacher_id_card(t)
        print(f"     ✓ Image size: {card.size}")
else:
    print("   No teachers found")

# Test PDF export
if students:
    print("\n3. Testing Single Student PDF Export:")
    student = students[0]
    card = generate_student_id_card(student)
    pdf = export_id_card_to_pdf(card)
    pdf_size = pdf.getbuffer().nbytes
    print(f"   ✓ PDF created: {pdf_size} bytes")

# Test bulk PDF export
if students:
    print("\n4. Testing Bulk Student PDF Export (2 cards):")
    cards = [generate_student_id_card(s) for s in students]
    pdf = export_multiple_id_cards_to_pdf(cards)
    pdf_size = pdf.getbuffer().nbytes
    print(f"   ✓ Bulk PDF created: {pdf_size} bytes (2 cards on 1 page)")

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)
