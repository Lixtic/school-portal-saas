"""Seed CompuThink Lab with 8 sample activities across all types."""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from individual_users.models import IndividualProfile, CompuThinkActivity

# Use Sir Ray's teacher profile
profile = IndividualProfile.objects.get(id=2)
print(f"Seeding CompuThink activities for: {profile}")

ACTIVITIES = [
    {
        "title": "Sorting a Deck of Cards — Algorithm Design",
        "activity_type": "algorithm",
        "level": "b7",
        "strand": "Computational Thinking",
        "topic": "Sorting algorithms",
        "instructions": (
            "You have a shuffled deck of 10 numbered cards (1-10). "
            "Design a step-by-step algorithm to sort them from smallest to largest. "
            "Your algorithm should be clear enough that someone who has never sorted cards could follow it."
        ),
        "content": {
            "problem": "Given 10 shuffled cards numbered 1 to 10, arrange them in order from smallest to largest.",
            "steps": [
                "Look at the first two cards in your hand.",
                "If the left card is bigger than the right card, swap them.",
                "Move to the next pair of cards and compare again.",
                "Continue until you reach the end of the cards.",
                "Go back to the start and repeat until no more swaps are needed.",
                "When you complete a pass with zero swaps, the cards are sorted!",
            ],
            "hints": [
                "Think about how you naturally sort cards in a card game.",
                'This method is called "Bubble Sort" because smaller values bubble to the front.',
                "Count how many comparisons you make — is there a pattern?",
            ],
            "expected_output": "Cards arranged in order: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10",
            "extension": "Try with 20 cards. Does your algorithm still work? How many more steps does it take? Can you think of a faster way?",
        },
        "answer_key": (
            "Bubble Sort algorithm: compare adjacent pairs and swap if out of order; "
            "repeat passes until sorted. Best case O(n), worst case O(n²). "
            "Students should recognise the repetitive comparison pattern."
        ),
    },
    {
        "title": "Planning a School Event — Pseudocode",
        "activity_type": "pseudocode",
        "level": "b7",
        "strand": "Computational Thinking",
        "topic": "Event planning with pseudocode",
        "instructions": (
            "Write pseudocode for a program that helps organise your school's Independence Day celebration. "
            "The program should collect the number of students attending, calculate how many chairs and "
            "refreshments are needed, and print a summary."
        ),
        "content": {
            "problem": (
                "Write pseudocode for a School Event Planner that asks for number of students, "
                "calculates resources needed (1 chair per student, 2 refreshments per student), "
                "and displays a planning summary."
            ),
            "steps": [
                "START",
                'DISPLAY "Welcome to Event Planner"',
                "INPUT number_of_students",
                "SET chairs = number_of_students",
                "SET refreshments = number_of_students * 2",
                "SET tables = number_of_students / 8 (rounded up)",
                'DISPLAY "Chairs needed: " + chairs',
                'DISPLAY "Refreshments: " + refreshments',
                'DISPLAY "Tables needed: " + tables',
                "END",
            ],
            "hints": [
                "Pseudocode is not a real programming language — write in simple English-like steps.",
                "Use keywords like START, END, INPUT, DISPLAY, SET, IF, WHILE.",
                "Think about what information you need BEFORE you can calculate.",
            ],
            "expected_output": "A clear pseudocode listing that another student can read and understand without any coding knowledge.",
            "extension": 'Add an IF statement: if students > 200, display "Use the Assembly Hall", otherwise "Use the Classroom Block".',
        },
        "answer_key": (
            "Students should demonstrate: sequential flow, use of variables, arithmetic operations, "
            "and clear INPUT/OUTPUT statements. Extension: correct IF-ELSE branching logic."
        ),
    },
    {
        "title": "Finding Patterns in Adinkra Symbols",
        "activity_type": "pattern",
        "level": "b8",
        "strand": "Computational Thinking",
        "topic": "Pattern recognition with cultural symbols",
        "instructions": (
            "Examine the set of Adinkra symbols provided. Identify repeating geometric patterns "
            "(symmetry, rotation, reflection) in at least 5 symbols. Create a classification table "
            "grouping them by their pattern type."
        ),
        "content": {
            "problem": (
                "Adinkra symbols from Akan culture use geometric patterns. Classify these symbols by "
                "identifying the mathematical transformations present in each: rotation symmetry, "
                "reflection symmetry, repetition, or fractal-like patterns."
            ),
            "steps": [
                "Study each Adinkra symbol carefully.",
                "For each symbol, check: Does it look the same if you rotate it 90°? 180°?",
                "Check: Does it look the same in a mirror (reflection)?",
                "Check: Are there smaller shapes that repeat inside the larger shape?",
                "Create a table with columns: Symbol Name, Rotation, Reflection, Repetition.",
                "Mark Yes/No for each property.",
                "Group symbols that share the same pattern properties.",
            ],
            "hints": [
                "Gye Nyame has interesting rotational properties.",
                "Sankofa shows reflection symmetry.",
                "Think about how a computer might detect these patterns automatically.",
            ],
            "expected_output": "A completed classification table with at least 5 symbols analysed and grouped by shared geometric properties.",
            "extension": "Can you write simple rules (like an algorithm) that a computer could use to detect whether a shape has reflection symmetry?",
        },
        "answer_key": (
            "Key patterns: Gye Nyame — rotational symmetry (180°); "
            "Adinkrahene — concentric circles (repetition); Sankofa — reflection; "
            "Dwennimmen — 4-fold rotational symmetry; "
            "Funtunfunefu — reflection symmetry with interlocking pattern."
        ),
    },
    {
        "title": "Breaking Down 'Cook Jollof Rice' into Sub-tasks",
        "activity_type": "decomposition",
        "level": "b7",
        "strand": "Computational Thinking",
        "topic": "Decomposition with everyday tasks",
        "instructions": (
            'Decompose the task "Cook Jollof Rice for the class" into smaller sub-tasks. '
            "Each sub-task should be simple enough that someone with no cooking experience can follow it. "
            "Identify which sub-tasks can happen at the same time (parallel) and which must happen in order (sequential)."
        ),
        "content": {
            "problem": "Break down the complex task of cooking Jollof Rice into the smallest possible sub-tasks, and identify dependencies between tasks.",
            "steps": [
                "List ALL ingredients needed (rice, tomatoes, onions, oil, spices, water, protein).",
                "Sub-task 1: Wash and soak rice (15 min)",
                "Sub-task 2: Blend tomatoes, pepper, and onions (5 min)",
                "Sub-task 3: Heat oil in pot (3 min)",
                "Sub-task 4: Fry onions until golden (5 min) — depends on Sub-task 3",
                "Sub-task 5: Add blended tomatoes, cook until oil floats (20 min) — depends on Sub-tasks 2 & 4",
                "Sub-task 6: Add spices and stock (2 min) — depends on Sub-task 5",
                "Sub-task 7: Add drained rice and water (5 min) — depends on Sub-tasks 1 & 6",
                "Sub-task 8: Cover and cook on low heat (30 min) — depends on Sub-task 7",
            ],
            "hints": [
                "Some tasks can happen at the SAME TIME — which ones?",
                "Sub-tasks 1 and 2 can happen in parallel while Sub-task 3 heats the oil!",
                "In computing, this is like how a computer runs multiple processes simultaneously.",
            ],
            "expected_output": "A decomposition diagram showing all sub-tasks with arrows showing which tasks depend on others, and which can run in parallel.",
            "extension": "Calculate the total time if tasks run sequentially vs. with parallelism. How much time do you save?",
        },
        "answer_key": (
            "Sequential time: ~85 min. With parallel execution (soaking rice + blending while heating oil): ~65 min. "
            'Key concept: decomposition reveals opportunities for parallelism, reducing total time. Dependencies create a "critical path".'
        ),
    },
    {
        "title": "School Library Catalogue — Abstraction Exercise",
        "activity_type": "abstraction",
        "level": "b9",
        "strand": "Computational Thinking",
        "topic": "Abstraction in system design",
        "instructions": (
            "Your school wants a digital library system. A real library has thousands of details about each book. "
            "Decide which details are ESSENTIAL for the catalogue system and which can be ignored. "
            'Create an abstracted "Book" model with only the necessary attributes.'
        ),
        "content": {
            "problem": (
                "From the full set of real-world book properties, identify the essential attributes needed "
                "for a functional school library catalogue. Remove unnecessary details (abstraction) while keeping the system useful."
            ),
            "steps": [
                "List ALL possible properties of a physical book (at least 15).",
                'For each property, ask: "Does a student NEED this to find and borrow the book?"',
                "Mark each as ESSENTIAL, USEFUL, or UNNECESSARY.",
                "Create your abstracted Book model with only Essential and Useful properties.",
                "Compare your model with a classmate — did you make the same choices?",
            ],
            "hints": [
                "Essential: title, author, ISBN, available/borrowed status.",
                "Useful: genre, publication year, shelf location.",
                "Unnecessary for basic catalogue: weight, page thickness, cover material, printing company.",
                "Abstraction means keeping what matters and hiding what doesn't!",
            ],
            "expected_output": 'A "Book" model with 6-10 well-chosen attributes, with justification for each inclusion and exclusion.',
            "extension": 'Now design a "Borrower" model. What attributes does the library need to track about students who borrow books?',
        },
        "answer_key": (
            "Good abstraction: Book(title, author, isbn, genre, year, shelf_number, is_available, borrower_name, due_date). "
            "Rejected: physical weight, smell, colour of cover, typeface — these don't help find or manage books. "
            "Key insight: different systems need different levels of abstraction."
        ),
    },
    {
        "title": "Build a GHS Currency Calculator in Scratch",
        "activity_type": "coding",
        "level": "b8",
        "strand": "Programming",
        "topic": "Currency conversion program",
        "instructions": (
            "Create a Scratch program that converts between Ghanaian Cedis (GHS) and other currencies. "
            "The program should: ask the user which currency to convert to, accept an amount in GHS, "
            "calculate and display the converted amount, and allow multiple conversions."
        ),
        "content": {
            "problem": (
                "Build an interactive currency converter in Scratch that handles at least 3 currencies: "
                "USD, GBP, and EUR. Use variables to store exchange rates and allow the user to perform multiple conversions."
            ),
            "steps": [
                "Create variables: amount_ghs, converted_amount, exchange_rate.",
                "When green flag clicked: display welcome message.",
                'Ask "Which currency? (1=USD, 2=GBP, 3=EUR)".',
                "Use IF-ELSE blocks to set the exchange_rate based on choice.",
                'Ask "Enter amount in GHS".',
                "Calculate: converted_amount = amount_ghs * exchange_rate.",
                "Display the result with the currency symbol.",
                'Ask "Convert again? (yes/no)" — use a REPEAT UNTIL loop.',
                "Test with known values to verify accuracy.",
            ],
            "hints": [
                "Exchange rates (approximate): 1 GHS = 0.067 USD, 0.053 GBP, 0.062 EUR.",
                'Use the "ask and wait" block for user input.',
                "Store the answer in a variable before doing calculations.",
                'Use "join" blocks to combine text and numbers in the output.',
            ],
            "expected_output": "A working Scratch program that correctly converts GHS to at least 3 currencies, with a loop for multiple conversions.",
            "extension": "Add reverse conversion (USD/GBP/EUR to GHS). Add a 4th currency of your choice.",
        },
        "answer_key": (
            "Test cases: 100 GHS = 6.70 USD, 5.30 GBP, 6.20 EUR. "
            "Students should demonstrate: variable usage, conditional logic (IF-ELSE), "
            "arithmetic operations, loops, and user input/output."
        ),
    },
    {
        "title": "Is This Real or AI-Generated? — AI Literacy",
        "activity_type": "ai_literacy",
        "level": "b9",
        "strand": "AI Literacy",
        "topic": "Identifying AI-generated content",
        "instructions": (
            "You will be shown 6 short texts — some written by humans and some generated by AI. "
            "For each text, decide if it is human-written or AI-generated, and explain your reasoning. "
            "Then discuss: What are the ethical implications of AI-generated content?"
        ),
        "content": {
            "problem": "Develop critical thinking skills to identify AI-generated text and understand the implications of AI content generation in society.",
            "steps": [
                "Read each of the 6 provided text samples carefully.",
                'For each sample, note: Does it feel generic or specific? Are there personal experiences? Does it have a consistent "voice"?',
                "Make your prediction: Human or AI? Write your confidence level (Low/Medium/High).",
                "After revealing answers, discuss: What clues helped you identify AI text?",
                "Group discussion: When is AI-generated content helpful? When is it harmful?",
                'Create a "Responsible AI Use" poster with 5 guidelines for your school.',
            ],
            "hints": [
                "AI text often sounds confident but may lack specific personal details.",
                "AI tends to use formal language and balanced viewpoints.",
                "Human writing often has more personality, slang, or cultural references.",
                "Neither humans nor AI are always easy to identify — that's the challenge!",
            ],
            "expected_output": "A completed analysis sheet with predictions, reasoning, and a group poster with AI use guidelines.",
            "extension": "Use an AI tool (with teacher permission) to generate a paragraph about your school. Then rewrite it in your own voice. Compare the two versions.",
        },
        "answer_key": (
            "Key indicators of AI text: overly balanced tone, lack of personal anecdotes, formulaic structure, "
            "no cultural specificity. Ethical discussion points: academic honesty, misinformation risks, "
            "job displacement, digital equity, responsible use in education."
        ),
    },
    {
        "title": "Create a School Timetable with a Spreadsheet",
        "activity_type": "productivity",
        "level": "b7",
        "strand": "Digital Productivity",
        "topic": "Spreadsheet skills for timetable creation",
        "instructions": (
            "Use a spreadsheet application (Google Sheets or Microsoft Excel) to create a weekly class timetable. "
            "Apply formatting, formulas, and conditional formatting to make it professional and functional."
        ),
        "content": {
            "problem": (
                "Design a weekly school timetable in a spreadsheet that is visually clear, "
                "uses proper formatting, and includes a formula to count the number of periods per subject."
            ),
            "steps": [
                'Open a new spreadsheet. Set column A as "Time" and columns B-F as Monday-Friday.',
                "Enter time slots in column A (e.g., 8:00-8:40, 8:40-9:20, etc.).",
                "Fill in subjects for each period across the week.",
                "Apply cell formatting: bold headers, borders, centre-align text.",
                "Use colour coding: Maths=blue, English=green, Science=yellow, etc.",
                "Use COUNTIF formula to count how many periods each subject has per week.",
                "Add a summary row at the bottom showing total periods per subject.",
                "Apply conditional formatting to highlight any empty periods in red.",
            ],
            "hints": [
                'COUNTIF syntax: =COUNTIF(B2:F10, "Mathematics")',
                "For colour coding, select cells then Format then Fill Colour.",
                "Merge cells for break/lunch periods spanning all columns.",
                'Use "Wrap Text" if subject names are long.',
            ],
            "expected_output": "A complete, colour-coded weekly timetable with subject counts using COUNTIF formulas and conditional formatting for empty slots.",
            "extension": 'Add a second sheet for "Teacher Timetable" that shows which teacher is in which class each period. Use VLOOKUP to link the two sheets.',
        },
        "answer_key": (
            "Students should demonstrate: cell formatting (borders, colours, alignment), "
            "COUNTIF formula usage, conditional formatting rules, merged cells for breaks, "
            "and a clean professional layout. Bonus: VLOOKUP connecting two sheets."
        ),
    },
]

created = 0
for a in ACTIVITIES:
    obj, was_created = CompuThinkActivity.objects.get_or_create(
        profile=profile,
        title=a["title"],
        defaults=a,
    )
    if was_created:
        created += 1
        print(f"  + {obj.title}")
    else:
        print(f"  = {obj.title} (exists)")

total = CompuThinkActivity.objects.filter(profile=profile).count()
print(f"\nCreated {created} new activities. Total for {profile}: {total}")
