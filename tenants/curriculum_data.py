# ─────────────────────────────────────────────────────────────────────────────
# BECE Syllabus Reference & Curriculum Context Builder
# Structured GES/NaCCA JHS syllabus data for the Curriculum Analyst agent
# ─────────────────────────────────────────────────────────────────────────────

# Official BECE blueprint: subjects, strands, sub-strands, and expected weightings.
# Based on NaCCA Standards-Based Curriculum (SBC) for Basic 7–9 (JHS 1–3).
# Code format: B{level}.{strand}.{sub_strand}.{content_std}.{indicator}

BECE_SYLLABUS = {
    'Mathematics': {
        'code_prefix': 'B7-9.M',
        'bece_weight_pct': 100,
        'strands': {
            'Number': {
                'weight_pct': 35,
                'sub_strands': [
                    'Number and Numeration Systems',
                    'Number Operations',
                    'Fractions, Decimals and Percentages',
                    'Ratio and Proportion',
                ],
                'sample_codes': ['B7.1.1.1.1', 'B8.1.2.1.1', 'B9.1.3.1.1'],
            },
            'Algebra': {
                'weight_pct': 20,
                'sub_strands': [
                    'Patterns and Relations',
                    'Algebraic Expressions',
                    'Equations and Inequalities',
                ],
                'sample_codes': ['B7.2.1.1.1', 'B8.2.2.1.1', 'B9.2.3.1.1'],
            },
            'Geometry and Measurement': {
                'weight_pct': 25,
                'sub_strands': [
                    'Shapes and Space',
                    'Measurement (Length, Area, Volume)',
                    'Position, Transformation and Symmetry',
                ],
                'sample_codes': ['B7.3.1.1.1', 'B8.3.2.1.1', 'B9.3.3.1.1'],
            },
            'Data': {
                'weight_pct': 20,
                'sub_strands': [
                    'Data Collection and Organisation',
                    'Data Representation (Graphs, Charts)',
                    'Probability and Chance',
                ],
                'sample_codes': ['B7.4.1.1.1', 'B8.4.2.1.1'],
            },
        },
    },
    'English Language': {
        'code_prefix': 'B7-9.E',
        'bece_weight_pct': 100,
        'strands': {
            'Oral Language (Listening & Speaking)': {
                'weight_pct': 15,
                'sub_strands': [
                    'Listening Comprehension',
                    'Speaking and Oral Presentation',
                    'Conversation Skills',
                ],
                'sample_codes': ['B7.1.1.1.1', 'B8.1.2.1.1'],
            },
            'Reading': {
                'weight_pct': 30,
                'sub_strands': [
                    'Comprehension (Prose, Poetry, Drama)',
                    'Vocabulary Development',
                    'Summary and Synthesis',
                    'Literary Appreciation',
                ],
                'sample_codes': ['B7.2.1.1.1', 'B9.2.3.1.1'],
            },
            'Grammar and Structure': {
                'weight_pct': 25,
                'sub_strands': [
                    'Parts of Speech and Sentence Structure',
                    'Tenses and Concord',
                    'Punctuation and Capitalization',
                    'Idiomatic Expressions',
                ],
                'sample_codes': ['B7.3.1.1.1', 'B8.3.2.1.1'],
            },
            'Writing': {
                'weight_pct': 30,
                'sub_strands': [
                    'Formal and Informal Letters',
                    'Narrative and Descriptive Writing',
                    'Argumentative and Expository Writing',
                    'Comprehension-Based Writing',
                ],
                'sample_codes': ['B7.4.1.1.1', 'B9.4.3.1.1'],
            },
        },
    },
    'Integrated Science': {
        'code_prefix': 'B7-9.S',
        'bece_weight_pct': 100,
        'strands': {
            'Diversity of Matter': {
                'weight_pct': 25,
                'sub_strands': [
                    'Materials (Classification, Properties)',
                    'Mixtures and Solutions',
                    'Acids, Bases and Salts',
                ],
                'sample_codes': ['B7.1.1.1.1', 'B9.1.2.1.1'],
            },
            'Cycles': {
                'weight_pct': 20,
                'sub_strands': [
                    'Earth Science (Water Cycle, Rock Cycle)',
                    'Life Cycles of Organisms',
                    'Farming and Food Production',
                ],
                'sample_codes': ['B7.2.1.1.1', 'B8.2.2.1.1'],
            },
            'Systems': {
                'weight_pct': 25,
                'sub_strands': [
                    'The Human Body (Digestive, Circulatory, Reproductive)',
                    'Ecosystems and Food Chains',
                    'Solar System',
                ],
                'sample_codes': ['B7.3.1.1.1', 'B9.3.3.1.1'],
            },
            'Energy': {
                'weight_pct': 15,
                'sub_strands': [
                    'Sources and Forms of Energy',
                    'Electricity and Magnetism',
                    'Light, Sound and Heat',
                ],
                'sample_codes': ['B7.4.1.1.1', 'B8.4.2.1.1'],
            },
            'Interactions of Matter': {
                'weight_pct': 15,
                'sub_strands': [
                    'Forces and Motion',
                    'Simple Machines',
                    'Chemical Reactions',
                ],
                'sample_codes': ['B7.5.1.1.1'],
            },
        },
    },
    'Social Studies': {
        'code_prefix': 'B7-9.SS',
        'bece_weight_pct': 100,
        'strands': {
            'Environment': {
                'weight_pct': 25,
                'sub_strands': [
                    'Physical Environment (Climate, Vegetation, Relief)',
                    'Human-Environment Interaction',
                    'Natural Resources and Conservation',
                ],
                'sample_codes': ['B7.1.1.1.1'],
            },
            'Governance, Politics and Stability': {
                'weight_pct': 25,
                'sub_strands': [
                    'Government and Democracy',
                    'National Institutions (Parliament, Judiciary)',
                    'Human Rights and Responsibilities',
                ],
                'sample_codes': ['B7.2.1.1.1', 'B9.2.2.1.1'],
            },
            'Socio-Economic Development': {
                'weight_pct': 25,
                'sub_strands': [
                    'Economic Activities (Agriculture, Industry, Trade)',
                    'Population and Migration',
                    'Science, Technology and Development',
                ],
                'sample_codes': ['B7.3.1.1.1'],
            },
            'Culture and Identity': {
                'weight_pct': 25,
                'sub_strands': [
                    'Ghanaian Culture and Traditions',
                    'National Identity and Patriotism',
                    'Socialisation and Social Organisation',
                ],
                'sample_codes': ['B7.4.1.1.1'],
            },
        },
    },
    'RME (Religious and Moral Education)': {
        'code_prefix': 'B7-9.R',
        'bece_weight_pct': 100,
        'strands': {
            'God, His Creation and Attributes': {
                'weight_pct': 25,
                'sub_strands': [
                    'The Nature of God (Christianity, Islam, ATR)',
                    'Creation and Stewardship',
                ],
                'sample_codes': ['B7.1.1.1.1'],
            },
            'Religious Practices and their Moral Implications': {
                'weight_pct': 25,
                'sub_strands': [
                    'Worship and Prayer',
                    'Religious Festivals and Celebrations',
                    'Rites of Passage',
                ],
                'sample_codes': ['B7.2.1.1.1'],
            },
            'Family Life and Moral Living': {
                'weight_pct': 25,
                'sub_strands': [
                    'The Family (Roles, Responsibilities)',
                    'Moral Teachings (Honesty, Integrity)',
                    'Conflict Resolution',
                ],
                'sample_codes': ['B7.3.1.1.1'],
            },
            'Our Nation Ghana': {
                'weight_pct': 25,
                'sub_strands': [
                    'National Unity and Cohesion',
                    'Authority and Obedience',
                    'Civic Responsibility',
                ],
                'sample_codes': ['B7.4.1.1.1'],
            },
        },
    },
    'Computing (ICT)': {
        'code_prefix': 'B7-9.CT',
        'bece_weight_pct': 100,
        'strands': {
            'Introduction to Computing': {
                'weight_pct': 25,
                'sub_strands': [
                    'Computer Hardware and Software',
                    'Operating Systems',
                    'Health and Safety in ICT',
                ],
                'sample_codes': ['B7.1.1.1.1'],
            },
            'Computational Thinking': {
                'weight_pct': 25,
                'sub_strands': [
                    'Algorithms and Problem-Solving',
                    'Programming Concepts (Scratch, Python basics)',
                    'Logical Reasoning',
                ],
                'sample_codes': ['B7.2.1.1.1', 'B9.2.2.1.1'],
            },
            'Communication Networks': {
                'weight_pct': 25,
                'sub_strands': [
                    'Internet and Web Technologies',
                    'Networking Basics',
                    'Cyber Safety and Digital Citizenship',
                ],
                'sample_codes': ['B7.3.1.1.1'],
            },
            'Productivity Software': {
                'weight_pct': 25,
                'sub_strands': [
                    'Word Processing',
                    'Spreadsheets',
                    'Presentations',
                    'Database Concepts',
                ],
                'sample_codes': ['B7.4.1.1.1'],
            },
        },
    },
    'Career Technology': {
        'code_prefix': 'B7-9.CAD',
        'bece_weight_pct': 100,
        'strands': {
            'Knowing and Understanding the World of Work': {
                'weight_pct': 30,
                'sub_strands': [
                    'Career Awareness and Exploration',
                    'Entrepreneurship Skills',
                    'Work Ethics and Safety',
                ],
                'sample_codes': ['B7.1.1.1.1'],
            },
            'Design and Make': {
                'weight_pct': 40,
                'sub_strands': [
                    'Materials and Tools',
                    'Design Process',
                    'Product Development (Textiles, Woodwork, Metalwork)',
                ],
                'sample_codes': ['B7.2.1.1.1'],
            },
            'Appraising and Using Technology': {
                'weight_pct': 30,
                'sub_strands': [
                    'Technology in Daily Life',
                    'Environmental Impact of Technology',
                    'Innovation and Creativity',
                ],
                'sample_codes': ['B7.3.1.1.1'],
            },
        },
    },
    'French': {
        'code_prefix': 'B7-9.FR',
        'bece_weight_pct': 100,
        'strands': {
            'Oral Communication': {
                'weight_pct': 30,
                'sub_strands': [
                    'Listening Comprehension',
                    'Spoken Interaction and Presentation',
                    'Pronunciation and Intonation',
                ],
                'sample_codes': ['B7.1.1.1.1'],
            },
            'Reading': {
                'weight_pct': 30,
                'sub_strands': [
                    'Reading Comprehension',
                    'Vocabulary Acquisition',
                    'Text Analysis',
                ],
                'sample_codes': ['B7.2.1.1.1'],
            },
            'Writing': {
                'weight_pct': 25,
                'sub_strands': [
                    'Guided Composition',
                    'Letter and Message Writing',
                    'Grammar in Context',
                ],
                'sample_codes': ['B7.3.1.1.1'],
            },
            'Culture': {
                'weight_pct': 15,
                'sub_strands': [
                    'Francophone Culture and Traditions',
                    'Everyday Life in French-Speaking Countries',
                ],
                'sample_codes': ['B7.4.1.1.1'],
            },
        },
    },
}

# Bloom's taxonomy target distribution for a well-balanced BECE-aligned bank
BLOOM_TARGET_DISTRIBUTION = {
    'Knowledge/Recall': 20,       # ~20% of items
    'Comprehension': 25,          # ~25%
    'Application': 30,            # ~30%
    'Analysis': 15,               # ~15%
    'Synthesis/Evaluation': 10,   # ~10%
}


def build_syllabus_summary_text():
    """Render the BECE syllabus as a compact text block for LLM context injection."""
    lines = [
        '=== BECE SYLLABUS REFERENCE (NaCCA Standards-Based Curriculum, JHS B7-B9) ===',
        '',
    ]
    for subject, data in BECE_SYLLABUS.items():
        lines.append(f'■ {subject}  (code prefix: {data["code_prefix"]})')
        for strand_name, strand in data['strands'].items():
            subs = ', '.join(strand['sub_strands'])
            lines.append(f'  ├ {strand_name} ({strand["weight_pct"]}%): {subs}')
        lines.append('')

    lines.append('■ Bloom\'s Target Distribution:')
    for level, pct in BLOOM_TARGET_DISTRIBUTION.items():
        lines.append(f'  {level}: {pct}%')
    lines.append('')
    lines.append('=== END SYLLABUS REFERENCE ===')
    return '\n'.join(lines)


def build_exam_bank_context():
    """
    Query the platform's question/exam data and return a summary string
    for injection into the Curriculum Analyst's context.

    Runs inside the current tenant schema (set by middleware).
    Returns empty string if no data found.
    """
    from django.db.models import Count, Q
    sections = []

    # ── 1. Teacher Question Bank (per-tenant) ──────────────────
    try:
        from teachers.models import QuestionBank, ExamPaper

        total_q = QuestionBank.objects.count()
        if total_q > 0:
            by_subject = list(
                QuestionBank.objects.values('subject__name')
                .annotate(count=Count('id'))
                .order_by('-count')[:15]
            )
            by_difficulty = list(
                QuestionBank.objects.values('difficulty')
                .annotate(count=Count('id'))
                .order_by('difficulty')
            )
            by_format = list(
                QuestionBank.objects.values('question_format')
                .annotate(count=Count('id'))
                .order_by('-count')
            )

            # Topic coverage
            by_topic = list(
                QuestionBank.objects.exclude(topic='')
                .values('topic')
                .annotate(count=Count('id'))
                .order_by('-count')[:20]
            )

            lines = [
                f'── Teacher Question Bank: {total_q} questions ──',
                'By Subject:',
            ]
            for row in by_subject:
                subj = row['subject__name'] or 'Unassigned'
                lines.append(f'  {subj}: {row["count"]}')
            lines.append('By Difficulty:')
            for row in by_difficulty:
                lines.append(f'  {row["difficulty"]}: {row["count"]}')
            lines.append('By Format:')
            for row in by_format:
                lines.append(f'  {row["question_format"]}: {row["count"]}')
            if by_topic:
                lines.append('Top Topics:')
                for row in by_topic:
                    lines.append(f'  {row["topic"]}: {row["count"]}')

            # Exam papers assembled
            paper_count = ExamPaper.objects.count()
            if paper_count:
                lines.append(f'Exam Papers assembled: {paper_count}')

            sections.append('\n'.join(lines))
    except Exception:
        pass

    # ── 2. Homework Questions (per-tenant) ─────────────────────
    try:
        from homework.models import Question as HWQuestion

        hw_total = HWQuestion.objects.count()
        if hw_total > 0:
            by_type = list(
                HWQuestion.objects.values('question_type')
                .annotate(count=Count('id'))
                .order_by('-count')
            )
            by_dok = list(
                HWQuestion.objects.values('dok_level')
                .annotate(count=Count('id'))
                .order_by('dok_level')
            )
            dok_labels = {1: 'Recall', 2: 'Skills/Concepts', 3: 'Strategic Thinking', 4: 'Extended Thinking'}
            lines = [f'── Homework Questions: {hw_total} ──', 'By Type:']
            for row in by_type:
                lines.append(f'  {row["question_type"]}: {row["count"]}')
            lines.append('By DOK Level:')
            for row in by_dok:
                label = dok_labels.get(row['dok_level'], f'Level {row["dok_level"]}')
                lines.append(f'  {label}: {row["count"]}')
            sections.append('\n'.join(lines))
    except Exception:
        pass

    # ── 3. Subjects & Classes (for alignment context) ──────────
    try:
        from academics.models import Subject, Class, AcademicYear

        current_year = AcademicYear.objects.filter(is_current=True).first()
        if current_year:
            subjects = list(Subject.objects.values_list('name', flat=True)[:20])
            classes = list(
                Class.objects.filter(academic_year=current_year)
                .values_list('name', flat=True)[:15]
            )
            if subjects:
                lines = [
                    f'── Active Subjects ({len(subjects)}): {", ".join(subjects)}',
                    f'── Active Classes ({len(classes)}): {", ".join(classes)}',
                ]
                sections.append('\n'.join(lines))
    except Exception:
        pass

    if not sections:
        return ''

    header = '=== PLATFORM EXAM BANK DATA (auto-retrieved) ==='
    footer = '=== END EXAM BANK DATA ==='
    return f'\n\n{header}\n' + '\n\n'.join(sections) + f'\n{footer}'
