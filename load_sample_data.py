import os
import django
from datetime import date, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from accounts.models import User
from academics.models import AcademicYear, Class, Subject, ClassSubject, SchoolInfo, Timetable
from students.models import Student, Attendance, Grade
from teachers.models import Teacher
from parents.models import Parent
from finance.models import FeeHead, FeeStructure, StudentFee, Payment
from announcements.models import Announcement

print("🚀 Starting to load sample data...")

# Create School Info
print("\n🏫 Configuring School Info...")
info, created = SchoolInfo.objects.get_or_create(
    id=1,
    defaults={
        'name': "St. Peter's Methodist Junior High School",
        'address': "P.O. Box 77, Kumasi, Ghana",
        'phone': "+233 24 000 0000",
        'email': "info@stpetermethodist.edu.gh",
        'motto': "Knowledge, Character & Service"
    }
)
if created:
    print("✅ Created School Info")
else:
    print("ℹ️  School Info already exists")

# Create Academic Year
print("\n📅 Creating Academic Year...")
ay, created = AcademicYear.objects.get_or_create(
    name="2025-2026",
    defaults={
        'start_date': date(2025, 9, 2),
        'end_date': date(2026, 6, 30),
        'is_current': True
    }
)
if created:
    print(f"✅ Created Academic Year: {ay.name}")
else:
    print(f"ℹ️  Academic Year already exists: {ay.name}")

# Create Subjects
print("\n📚 Creating Subjects...")
subjects_data = [
    ("MATH", "Mathematics"),
    ("ENG", "English Language"),
    ("SCI", "Integrated Science"),
    ("SOC", "Social Studies"),
    ("RME", "Religious & Moral Education"),
    ("CCA", "Creative Arts"),
    ("ICT", "ICT"),
    ("PHE", "Physical Education"),
]

subjects = {}
for code, name in subjects_data:
    subj, created = Subject.objects.get_or_create(
        code=code,
        defaults={'name': name}
    )
    subjects[code] = subj
    if created:
        print(f"✅ Created Subject: {name}")
    else:
        print(f"ℹ️  Subject already exists: {name}")

# Create Classes
print("\n🏫 Creating Classes...")
classes_data = [
    "JHS 1A",
    "JHS 1B",
    "JHS 2A",
    "JHS 2B",
    "JHS 3A",
]

classes = {}
for class_name in classes_data:
    cls, created = Class.objects.get_or_create(
        name=class_name,
        academic_year=ay
    )
    classes[class_name] = cls
    if created:
        print(f"✅ Created Class: {class_name}")
    else:
        print(f"ℹ️  Class already exists: {class_name}")

# Create Teachers
print("\n👨‍🏫 Creating Teachers...")
teachers_data = [
    ("teacher1", "Kwame", "Mensah", "kwame.mensah@school.com", "T001", "Mathematics & Science"),
    ("teacher2", "Akosua", "Boateng", "akosua.boateng@school.com", "T002", "English & Social Studies"),
    ("teacher3", "Kofi", "Asante", "kofi.asante@school.com", "T003", "ICT & Creative Arts"),
    # Teachers from Duty Roster - Using T100+ to avoid conflicts
    ("zaminu", "Zakaria", "Aminu", "zakaria.aminu@school.com", "T104", "General Subjects"),
    ("awahab", "Alidu", "Abdul Wahab", "alidu.wahab@school.com", "T105", "General Subjects"),
    ("rgyapanin", "Ray", "Gyapanin", "ray.gyapanin@school.com", "T106", "General Subjects"),
    ("bnurudeen", "Bakuri", "Nurudeen", "bakuri.nurudeen@school.com", "T107", "General Subjects"),
    ("ihmukarama", "Issah", "Haruna Mukarama", "issah.mukarama@school.com", "T108", "General Subjects"),
    ("mahmed", "Mahama", "Ahmed", "mahama.ahmed@school.com", "T109", "General Subjects"),
    ("sadia", "Saaka", "Adia", "saaka.adia@school.com", "T110", "General Subjects"),
    ("aafaustina", "Adu", "Asamoah Faustina", "adu.faustina@school.com", "T111", "General Subjects"),
    ("arufai", "Awal", "Rufai", "awal.rufai@school.com", "T112", "General Subjects"),
    ("bhappy", "Badisoma", "Happy", "badisoma.happy@school.com", "T113", "General Subjects"),
    ("aramatu", "Atiku", "Ramatu", "atiku.ramatu@school.com", "T114", "General Subjects"),
]

teachers = {}
for username, fname, lname, email, emp_id, qual in teachers_data:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': fname,
            'last_name': lname,
            'email': email,
            'user_type': 'teacher',
        }
    )
    if created:
        user.set_password('password123')
        user.save()
        print(f"✅ Created Teacher User: {username}")
    
    teacher, created = Teacher.objects.get_or_create(
        user=user,
        defaults={
            'employee_id': emp_id,
            'date_of_birth': date(1985, 5, 15),
            'date_of_joining': date(2020, 8, 1),
            'qualification': qual
        }
    )
    teachers[username] = teacher
    if created:
        print(f"✅ Created Teacher Profile: {fname} {lname}")

# Assign subjects to teachers
teachers['teacher1'].subjects.add(subjects['MATH'], subjects['SCI'])
teachers['teacher2'].subjects.add(subjects['ENG'], subjects['SOC'])
teachers['teacher3'].subjects.add(subjects['ICT'], subjects['CCA'])

# Create Class Subjects (assign teachers to teach subjects in classes)
print("\n📖 Assigning Teachers to Classes...")
class_subject_assignments = [
    (classes['JHS 1A'], subjects['MATH'], teachers['teacher1']),
    (classes['JHS 1A'], subjects['ENG'], teachers['teacher2']),
    (classes['JHS 1A'], subjects['SCI'], teachers['teacher1']),
    (classes['JHS 1B'], subjects['MATH'], teachers['teacher1']),
    (classes['JHS 1B'], subjects['ENG'], teachers['teacher2']),
    (classes['JHS 2A'], subjects['ICT'], teachers['teacher3']),
]

for cls, subj, teacher in class_subject_assignments:
    cs, created = ClassSubject.objects.get_or_create(
        class_name=cls,
        subject=subj,
        defaults={'teacher': teacher}
    )
    if created:
        print(f"✅ Assigned {teacher.user.get_full_name()} to teach {subj.name} in {cls.name}")

# Create Students
print("\n👨‍🎓 Creating Students...")
students_data = [
    ("student1", "Ama", "Owusu", "ama.owusu@email.com", "S001", "JHS 1A", "101", "female"),
    ("student2", "Kwabena", "Osei", "kwabena.osei@email.com", "S002", "JHS 1A", "102", "male"),
    ("student3", "Abena", "Agyeman", "abena.agyeman@email.com", "S003", "JHS 1A", "103", "female"),
    ("student4", "Yaw", "Appiah", "yaw.appiah@email.com", "S004", "JHS 1A", "104", "male"),
    ("student5", "Efua", "Nkrumah", "efua.nkrumah@email.com", "S005", "JHS 1B", "105", "female"),
    ("student6", "Kofi", "Danquah", "kofi.danquah@email.com", "S006", "JHS 1B", "106", "male"),
    ("student7", "Adwoa", "Mensah", "adwoa.mensah@email.com", "S007", "JHS 2A", "201", "female"),
    ("student8", "Kwame", "Boakye", "kwame.boakye@email.com", "S008", "JHS 2A", "202", "male"),
]

students = {}
for username, fname, lname, email, adm_no, class_key, roll, gender in students_data:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': fname,
            'last_name': lname,
            'email': email,
            'user_type': 'student',
        }
    )
    if created:
        user.set_password('password123')
        user.save()
        print(f"✅ Created Student User: {username}")
    
    student, created = Student.objects.get_or_create(
        user=user,
        defaults={
            'admission_number': adm_no,
            'date_of_birth': date(2010, 3, 10),
            'gender': gender,
            'date_of_admission': date(2023, 9, 1),
            'current_class': classes[class_key],
            'roll_number': roll,
            'emergency_contact': "+233244567890"
        }
    )
    students[username] = student
    if created:
        print(f"✅ Created Student Profile: {fname} {lname} - {class_key}")

# Create Sample Grades
print("\n📊 Creating Sample Grades...")
sample_grades = [
    (students['student1'], subjects['MATH'], 25, 60),  # Class work, Exams
    (students['student1'], subjects['ENG'], 28, 65),
    (students['student1'], subjects['SCI'], 22, 55),
    (students['student2'], subjects['MATH'], 20, 50),
    (students['student2'], subjects['ENG'], 23, 58),
    (students['student3'], subjects['MATH'], 27, 68),
    (students['student3'], subjects['ENG'], 29, 70),
]

for student, subject, class_score, exam_score in sample_grades:
    grade, created = Grade.objects.get_or_create(
        student=student,
        subject=subject,
        academic_year=ay,
        term='first',
        defaults={
            'class_score': class_score,
            'exams_score': exam_score,
        }
    )
    if created:
        print(f"✅ Created Grade: {student.user.get_full_name()} - {subject.name} - Total: {grade.total_score}")

# Create Sample Attendance
print("\n📅 Creating Sample Attendance...")
today = date.today()
for i in range(10):
    attendance_date = today - timedelta(days=i)
    for student in [students['student1'], students['student2'], students['student3']]:
        status = 'present' if i < 8 else 'absent'  # 8 present, 2 absent
        att, created = Attendance.objects.get_or_create(
            student=student,
            date=attendance_date,
            defaults={
                'status': status,
                'marked_by': User.objects.filter(user_type='admin').first()
            }
        )
        if created and i == 0:  # Only print for first day
            print(f"✅ Created Attendance for {student.user.get_full_name()}")

# Create Parents
print("\n👨‍👩‍👧 Creating Parents...")
parents_data = [
    ("parent1", "Samuel", "Owusu", "samuel.owusu@email.com", "father", ["student1"]),
    ("parent2", "Grace", "Osei", "grace.osei@email.com", "mother", ["student2"]),
    ("parent3", "Joseph", "Agyeman", "joseph.agyeman@email.com", "father", ["student3"]),
]

for username, fname, lname, email, relation, child_usernames in parents_data:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': fname,
            'last_name': lname,
            'email': email,
            'user_type': 'parent',
        }
    )
    if created:
        user.set_password('password123')
        user.save()
        print(f"✅ Created Parent User: {username}")
    
    parent, created = Parent.objects.get_or_create(
        user=user,
        defaults={
            'relation': relation,
            'occupation': 'Business Person'
        }
    )
    
    # Link children
    for child_username in child_usernames:
        if child_username in students:
            parent.children.add(students[child_username])
    
    if created:
        print(f"✅ Created Parent Profile: {fname} {lname}")

# Create Admin if needed for finance/announcements (ensure consistency)
admin_user = User.objects.filter(username='admin').first()
if not admin_user:
    # Fallback to creating one if missing (though usually created via createsuperuser)
    try:
        admin_user = User.objects.create_superuser('admin', 'admin@school.com', 'admin123', user_type='admin')
        print("✅ Created fallback Admin User for records")
    except Exception:
        # If admin exists but username logic failed or other issue, grab first superuser
        admin_user = User.objects.filter(is_superuser=True).first()

# Create Finance Data
print("\n💰 Creating Finance Data...")

# Fee Heads
fee_heads = {}
for name, desc in [("Tuition Fee", "Basic tuition per term"), ("PTA Dues", "Parent-Teacher Association Levies"), ("ICT Fee", "Computer Lab Maintenance")]:
    head, created = FeeHead.objects.get_or_create(name=name, defaults={'description': desc})
    fee_heads[name] = head
    if created:
        print(f"✅ Created Fee Head: {name}")

# Fee Structures (for all classes)
fee_structures = []
for cls_name, cls in classes.items():
    # Tuition
    fs_tuition, created = FeeStructure.objects.get_or_create(
        head=fee_heads["Tuition Fee"],
        class_level=cls,
        academic_year=ay,
        term='first',
        defaults={'amount': 450.00, 'due_date': date(2024, 9, 30)}
    )
    
    # PTA
    fs_pta, created = FeeStructure.objects.get_or_create(
        head=fee_heads["PTA Dues"],
        class_level=cls,
        academic_year=ay,
        term='first',
        defaults={'amount': 50.00, 'due_date': date(2024, 9, 30)}
    )
    
    fee_structures.extend([fs_tuition, fs_pta])

print(f"✅ Created/Verified Fee Structures for {len(classes)} classes")

# Assign Fees to Students & Make Payments
for username, student in students.items():
    # Assign all fees for their class
    student_fees = []
    class_fees = FeeStructure.objects.filter(class_level=student.current_class, academic_year=ay, term='first')
    
    for structure in class_fees:
        sf, created = StudentFee.objects.get_or_create(
            student=student,
            fee_structure=structure,
            defaults={'amount_payable': structure.amount}
        )
        student_fees.append(sf)
    
    # Record a random payment for student1
    if username == 'student1' and student_fees:
        fee_to_pay = student_fees[0] # Pay Tuition
        # Check if already paid to avoid dupes on re-run
        if fee_to_pay.balance > 0 and not fee_to_pay.payments.exists():
            Payment.objects.create(
                student_fee=fee_to_pay,
                amount=200.00,
                date=date.today(),
                method='Cash',
                recorded_by=admin_user,
                reference=f"REC-{random.randint(1000, 9999)}"
            )
            print(f"✅ Recorded part-payment for {username}")

# Create Announcements
print("\n📢 Creating Announcements...")
announcements_data = [
    ("Welcome Back!", "We are excited to start the new academic year. Please refer to the notice board for the term schedule.", "all"),
    ("PTA Meeting", "The first PTA meeting will be held on Friday, 15th September.", "parents"),
    ("Staff Meeting", "All teachers are to attend a mandatory briefing on Monday morning.", "staff"),
    ("Exam Schedule Out", "The mid-term exam timetable has been released.", "students"),
]

for title, content, target in announcements_data:
    ann, created = Announcement.objects.get_or_create(
        title=title,
        defaults={
            'content': content,
            'target_audience': target,
            'created_by': admin_user
        }
    )
    if created:
        print(f"✅ Created Announcement: {title}")

# Create Duty Roster
print("\n📅 Creating Duty Roster...")
from teachers.models import DutyWeek, DutyAssignment

# Use retrieved 'ay' (AcademicYear) from above
term = 'first'
# Explicit dates from the PDF
duty_weeks_data = [
    # (Week Num, Start, End, Assignments List of (username, role), Remarks)
    (1, date(2025, 9, 2), date(2025, 9, 5), [], "All Prefects, All Teachers"),
    (2, date(2025, 9, 8), date(2025, 9, 12), [], "All Prefects, All Teachers"),
    (3, date(2025, 9, 15), date(2025, 9, 19), [('zaminu', 'Teacher on Duty')], "Prefects: Zakaria Suturatu, Abdulai Mariam"),
    (4, date(2025, 9, 22), date(2025, 9, 26), [('awahab', 'Teacher on Duty')], "Prefects: Ganiw Barkisu, Amankwa Eliham"),
    (5, date(2025, 9, 29), date(2025, 10, 3), [('rgyapanin', 'Teacher on Duty')], "Prefects: Umar Khadijah, Yakubu Rawda"),
    (6, date(2025, 10, 6), date(2025, 10, 10), [('awahab', 'Teacher on Duty')], "Prefects: Adam Asana, Shaibu Leena"),
    (7, date(2025, 10, 13), date(2025, 10, 17), [('zaminu', 'Teacher on Duty')], "Prefects: Mohammed Ruhaima, Beidulai Isma"),
    (8, date(2025, 10, 20), date(2025, 10, 24), [('bnurudeen', 'Teacher on Duty')], "Prefects: Achulo M. Farida, Abu Zulaiha"),
    (9, date(2025, 10, 27), date(2025, 10, 31), [('rgyapanin', 'Teacher on Duty')], "Prefects: Zakaria Rahima, Hadi Afraw"),
    (10, date(2025, 11, 3), date(2025, 11, 7), [('zaminu', 'Teacher on Duty'), ('ihmukarama', 'Teacher on Duty')], "Prefects: Fuseini Afishetu, Zakaria Suturatu"),
    (11, date(2025, 11, 10), date(2025, 11, 14), [('mahmed', 'Teacher on Duty')], "Prefects: Achulo M. Farida, Umar Khadijah"),
    (12, date(2025, 11, 17), date(2025, 11, 21), [('bnurudeen', 'Teacher on Duty'), ('sadia', 'Teacher on Duty')], "Prefects: Yakubu Rawda, Amankwa Eliham"),
    (13, date(2025, 11, 24), date(2025, 11, 28), [('awahab', 'Teacher on Duty')], "Prefects: Sumaila Magfira, Ganiw Barkisu"),
    (14, date(2025, 12, 1), date(2025, 12, 5), [('rgyapanin', 'Teacher on Duty'), ('aafaustina', 'Teacher on Duty'), ('arufai', 'Teacher on Duty')], "Prefects: Alhassan Tabdila, Mumuni Maweyatu"),
    (15, date(2025, 12, 8), date(2025, 12, 12), [('mahmed', 'Teacher on Duty'), ('bhappy', 'Teacher on Duty'), ('aramatu', 'Teacher on Duty')], "Prefects: Kudjo Hikmah, Sulemana Etsan"),
    (16, date(2025, 12, 15), date(2025, 12, 18), [], "All Prefects, All Teachers. VACATION DAY – THURSDAY, 18th DECEMBER, 2025"),
]

for week_num, s_date, e_date, assignments, remarks in duty_weeks_data:
    dw, created = DutyWeek.objects.get_or_create(
        academic_year=ay,
        term=term,
        week_number=week_num,
        defaults={
            'start_date': s_date,
            'end_date': e_date,
            'remarks': remarks
        }
    )
    if created:
        print(f"✅ Created Duty Week {week_num}")
        for t_username, role in assignments:
            if t_username in teachers:
                DutyAssignment.objects.create(
                    week=dw,
                    teacher=teachers[t_username],
                    role=role
                )
                print(f"   -> Assigned {t_username} as {role}")

# ----------------------------------------------------
# SECOND TERM DUTY ROSTER
# ----------------------------------------------------
print("\n📅 Creating 2nd Term Duty Roster...")
term2 = 'second'
start_date_t2 = date(2026, 1, 8) # Thursday

# Reuse logic from First Term (first 12 entries)
# Map dates for 12 weeks
# Week 1 starts Jan 8 (Thu) -> Ends Jan 9 (Fri)
# Week 2 starts Jan 12 (Mon) -> Ends Jan 16 (Fri)
# ...
duty_weeks_data_t2 = []

# Recopy assignments from the first term data for 1-12
# item structure: (wk, start, end, assignments, remarks)
first_term_info = duty_weeks_data[:12] # Slice first 12

current_start = start_date_t2
for i, (old_wk, _, _, asses, rems) in enumerate(first_term_info):
    wk_num = i + 1
    
    # Calculate End Date
    if wk_num == 1:
        # First week starts Thu Jan 8 -> Fri Jan 9
        current_end = current_start + timedelta(days=1)
        next_start = current_start + timedelta(days=4) # Next Mon is Jan 12 (8+4=12)
    else:
        # Regular Mon-Fri week
        current_end = current_start + timedelta(days=4) # Mon+4 = Fri
        next_start = current_start + timedelta(days=7) # Next Mon

    duty_weeks_data_t2.append((wk_num, current_start, current_end, asses, rems))
    
    # Update for next loop
    current_start = next_start

for week_num, s_date, e_date, assignments, remarks in duty_weeks_data_t2:
    dw, created = DutyWeek.objects.get_or_create(
        academic_year=ay,
        term=term2,
        week_number=week_num,
        defaults={
            'start_date': s_date,
            'end_date': e_date,
            'remarks': remarks
        }
    )
    if created:
        print(f"✅ Created 2nd Term Duty Week {week_num} ({s_date} - {e_date})")
        for t_username, role in assignments:
            if t_username in teachers:
                DutyAssignment.objects.create(
                    week=dw,
                    teacher=teachers[t_username],
                    role=role
                )
                print(f"   -> Assigned {t_username} as {role}")

print("\n" + "="*60)
print("🎉 SAMPLE DATA LOADED SUCCESSFULLY!")
print("="*60)
print("\n📋 LOGIN CREDENTIALS:")
print("\n🔐 Admin:")
print("   Username: admin")
print("   Password: admin123")
print("\n👨‍🏫 Teachers:")
print("   Username: teacher1 / teacher2 / teacher3")
print("   Password: password123")
print("\n👨‍🎓 Students:")
print("   Username: student1 / student2 / student3 / etc.")
print("   Password: password123")
print("\n👨‍👩‍👧 Parents:")
print("   Username: parent1 / parent2 / parent3")
print("   Password: password123")
print("\n" + "="*60)
print("✅ You can now login and test the system!")
print("="*60)