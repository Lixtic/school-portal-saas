"""Seed Report Cards with sample sets and student entries."""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from individual_users.models import IndividualProfile, ReportCardSet, ReportCardEntry

profile = IndividualProfile.objects.get(id=2)
print(f"Seeding report cards for: {profile}")

# --- Shared data ---
SUBJECTS_B7 = [
    {"subject": "Mathematics", "class_score": 28, "exam_score": 55, "total": 83, "grade": "A", "remark": "Excellent"},
    {"subject": "English Language", "class_score": 25, "exam_score": 48, "total": 73, "grade": "B", "remark": "Very Good"},
    {"subject": "Integrated Science", "class_score": 27, "exam_score": 52, "total": 79, "grade": "A", "remark": "Excellent"},
    {"subject": "Social Studies", "class_score": 22, "exam_score": 44, "total": 66, "grade": "B", "remark": "Very Good"},
    {"subject": "Computing / ICT", "class_score": 30, "exam_score": 58, "total": 88, "grade": "A", "remark": "Excellent"},
    {"subject": "French", "class_score": 20, "exam_score": 40, "total": 60, "grade": "C", "remark": "Good"},
    {"subject": "Creative Arts & Design", "class_score": 26, "exam_score": 50, "total": 76, "grade": "B", "remark": "Very Good"},
    {"subject": "Religious & Moral Education", "class_score": 24, "exam_score": 46, "total": 70, "grade": "B", "remark": "Very Good"},
    {"subject": "Ghanaian Language (Twi)", "class_score": 23, "exam_score": 42, "total": 65, "grade": "C", "remark": "Good"},
    {"subject": "Career Technology", "class_score": 25, "exam_score": 50, "total": 75, "grade": "B", "remark": "Very Good"},
]

GHANAIAN_NAMES = [
    "Kwame Asante", "Ama Serwaa", "Kofi Mensah", "Abena Osei",
    "Yaw Boateng", "Efua Darko", "Kwesi Appiah", "Akosua Frimpong",
    "Kojo Adjei", "Afia Agyemang", "Kwaku Owusu", "Adwoa Ansah",
    "Nana Ofori", "Akua Badu", "Yaa Asantewaa",
]

TOTAL_STUDENTS = len(GHANAIAN_NAMES)


def _vary_subjects(base_subjects, offset):
    """Create realistic grade variation from a base set."""
    import random
    random.seed(42 + offset)
    result = []
    for s in base_subjects:
        class_sc = max(10, min(30, s["class_score"] + random.randint(-6, 4)))
        exam_sc = max(20, min(60, s["exam_score"] + random.randint(-10, 6)))
        total = class_sc + exam_sc
        if total >= 80:
            grade, remark = "A", "Excellent"
        elif total >= 70:
            grade, remark = "B", "Very Good"
        elif total >= 60:
            grade, remark = "C", "Good"
        elif total >= 50:
            grade, remark = "D", "Satisfactory"
        elif total >= 40:
            grade, remark = "E", "Below Average"
        else:
            grade, remark = "F", "Needs Improvement"
        result.append({
            "subject": s["subject"],
            "class_score": class_sc,
            "exam_score": exam_sc,
            "total": total,
            "grade": grade,
            "remark": remark,
        })
    return result


TEACHER_COMMENTS = [
    "{name} is a hardworking student who shows great enthusiasm for learning. Keep up the excellent work!",
    "{name} has shown steady improvement this term. With more effort in homework, even better results are possible.",
    "{name} is a bright and confident student. Focus more on Science and French to achieve all-round excellence.",
    "{name} participates well in class but needs to improve exam preparation skills. I believe in your potential!",
    "{name} is very respectful and punctual. More practice in Mathematics will lead to significant improvement.",
    "{name} has a positive attitude towards learning. Continue reading widely to build your vocabulary and comprehension.",
    "{name} is a natural leader in group work. Translating that energy into personal study will yield great dividends.",
    "{name} shows strong creative ability. Balancing creative interests with core subjects will serve you well.",
    "{name} is quiet but attentive. Don't be afraid to ask questions — your thoughtful contributions are valued.",
    "{name} has had an excellent term overall. Your discipline and focus are commendable. Keep it up!",
    "{name} demonstrates a good grasp of concepts but rushes through exams. Taking time to review answers will help.",
    "{name} is kind and helpful to classmates. Keep balancing good character with academic effort.",
    "{name} has overcome early-term challenges and finished strong. This resilience will take you far.",
    "{name} shows good potential in Science and Computing. Consider joining the Science Club next term.",
    "{name} is a joy to teach. Your curiosity and respect for others make you an asset to the class.",
]

HEAD_COMMENTS = [
    "A very commendable performance. Keep up the good work.",
    "Good effort this term. There is room for improvement in a few areas.",
    "An outstanding result. You are a role model for your peers.",
    "Satisfactory performance. Set higher targets for next term.",
    "You have done well. With more dedication, you can reach the top!",
]

CONDUCT_RATINGS = [
    "excellent", "very_good", "very_good", "good", "excellent",
    "good", "very_good", "excellent", "good", "very_good",
    "good", "satisfactory", "very_good", "excellent", "good",
]

SETS = [
    {
        "title": "Basic 7A — First Term Report Cards 2025/2026",
        "class_name": "Basic 7A",
        "term": "first",
        "academic_year": "2025/2026",
        "school_name": "Aura International School",
    },
    {
        "title": "Basic 7A — Second Term Report Cards 2025/2026",
        "class_name": "Basic 7A",
        "term": "second",
        "academic_year": "2025/2026",
        "school_name": "Aura International School",
    },
    {
        "title": "Basic 8B — First Term Report Cards 2025/2026",
        "class_name": "Basic 8B",
        "term": "first",
        "academic_year": "2025/2026",
        "school_name": "Aura International School",
    },
]

created_sets = 0
created_entries = 0

for set_data in SETS:
    card_set, was_created = ReportCardSet.objects.get_or_create(
        profile=profile,
        title=set_data["title"],
        defaults=set_data,
    )
    if was_created:
        created_sets += 1
        print(f"  + Set: {card_set.title}")
        # Sort students by average score descending for position ranking
        student_entries = []
        for i, name in enumerate(GHANAIAN_NAMES):
            subjects = _vary_subjects(SUBJECTS_B7, offset=i + hash(set_data["term"]))
            avg = sum(s["total"] for s in subjects) / len(subjects)
            student_entries.append((name, i, subjects, avg))

        student_entries.sort(key=lambda x: -x[3])  # rank by average

        entries_to_create = []
        for rank, (name, idx, subjects, avg) in enumerate(student_entries, start=1):
            if avg >= 80:
                grade = "A"
            elif avg >= 70:
                grade = "B"
            elif avg >= 60:
                grade = "C"
            elif avg >= 50:
                grade = "D"
            else:
                grade = "E"
            entries_to_create.append(ReportCardEntry(
                card_set=card_set,
                student_name=name,
                subjects=subjects,
                overall_score=round(avg, 2),
                overall_grade=grade,
                position=rank,
                total_students=TOTAL_STUDENTS,
                conduct=CONDUCT_RATINGS[idx],
                attitude=CONDUCT_RATINGS[(idx + 3) % TOTAL_STUDENTS],
                interest=CONDUCT_RATINGS[(idx + 7) % TOTAL_STUDENTS],
                attendance=f"{170 - idx * 2}/180 days",
                class_teacher_comment=TEACHER_COMMENTS[idx].format(name=name.split()[0]),
                head_teacher_comment=HEAD_COMMENTS[rank % len(HEAD_COMMENTS)],
                promoted=True if set_data["term"] == "second" else None,
                next_class="Basic 8A" if set_data["term"] == "second" else "",
            ))
        ReportCardEntry.objects.bulk_create(entries_to_create)
        created_entries += len(entries_to_create)
        print(f"    → {len(entries_to_create)} student entries")
    else:
        print(f"  = Set: {card_set.title} (exists)")

total_sets = ReportCardSet.objects.filter(profile=profile).count()
total_entries = ReportCardEntry.objects.filter(card_set__profile=profile).count()
print(f"\nCreated {created_sets} sets with {created_entries} entries. Total: {total_sets} sets, {total_entries} entries.")
