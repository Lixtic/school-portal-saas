"""Seed TVET Practicals with sample projects across all 6 types."""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from individual_users.models import IndividualProfile, TVETProject

profile = IndividualProfile.objects.get(id=2)
print(f"Seeding TVET projects for: {profile}")

PROJECTS = [
    # ── 1. Project Plan — Carpentry ───────────────────────────────────────
    {
        "title": "Design & Build a Wooden Book Shelf",
        "project_type": "project_plan",
        "level": "b9",
        "strand": "design",
        "topic": "Woodworking fundamentals — measuring, cutting, joining",
        "description": (
            "Students will design and construct a small free-standing wooden book shelf "
            "(3 shelves, approximately 90 cm tall × 60 cm wide × 25 cm deep) using locally "
            "available softwood (Wawa or Ceiba). The project covers the full design-build cycle: "
            "sketching, dimensioning, material estimation, cutting, joining, sanding, and finishing."
        ),
        "content": {
            "objectives": [
                "Draw a labelled working sketch with dimensions in centimetres.",
                "Calculate the total board length needed and estimate material cost.",
                "Demonstrate safe use of basic carpentry tools: handsaw, plane, try square, marking gauge.",
                "Apply at least TWO joining techniques: butt joint with nails/screws and a simple dado/housing joint.",
                "Sand and apply a finish (varnish or paint) to the completed shelf.",
            ],
            "materials": [
                "Wawa or Ceiba softwood planks (25 mm × 250 mm × various lengths)",
                "Sandpaper (grades 80, 120, 240)",
                "Wood glue (PVA-based)",
                "Nails (50 mm panel pins) and/or wood screws (40 mm)",
                "Varnish or wood stain + brush",
                "Pencil, ruler, try square, marking gauge",
                "Handsaw (crosscut), smoothing plane, hammer, screwdriver",
                "Workbench with clamp/vice",
            ],
            "steps": [
                "1. DESIGN PHASE (Day 1): Sketch the shelf from front and side views. Label all dimensions. List all components (2 sides, 3 shelves, 1 back panel optional).",
                "2. MATERIAL ESTIMATION (Day 1): Calculate total board-metres required. Visit a local timber market — record current prices per metre for Wawa.",
                "3. MARKING OUT (Day 2): Transfer dimensions from sketch to wood using pencil, try square, and marking gauge. Mark waste areas with an 'X'.",
                "4. CUTTING (Day 2-3): Secure wood in vice. Cut components using crosscut saw. Ensure cuts are square using try square. Keep offcuts for patching.",
                "5. JOINTING (Day 3-4): Cut housing/dado joints on side panels for shelves (10 mm deep). Dry-fit all components to check alignment before gluing.",
                "6. ASSEMBLY (Day 4): Apply wood glue to joints. Assemble shelves into side panels. Reinforce with nails/screws. Check for square using diagonal measurements.",
                "7. SANDING (Day 5): Sand all surfaces starting with 80-grit, then 120-grit, then 240-grit. Sand along the grain, never across it.",
                "8. FINISHING (Day 5-6): Apply 2 coats of varnish or wood stain. Allow 24 hours drying between coats. Light sand with 240-grit between coats.",
                "9. QUALITY CHECK (Day 6): Verify shelf is stable, level, and free of rough spots. Test load-bearing capacity with books.",
            ],
            "safety_notes": [
                "Always cut AWAY from your body. Secure wood in a vice before sawing.",
                "Wear safety goggles when sawing, planing, and sanding.",
                "Use a dust mask when sanding, especially with power tools.",
                "Keep work area clean — wood shavings are a fire hazard.",
                "Handle varnish in a well-ventilated area. Avoid skin contact with solvents.",
                "Report any tool damage to the instructor immediately. Never use a blunt saw.",
            ],
            "assessment": {
                "Design & Planning (15)": "Accurate sketch with dimensions, complete materials list, realistic cost estimate",
                "Tool Use & Technique (20)": "Correct and safe use of all tools, accurate cutting, clean joints",
                "Assembly & Fit (20)": "Square, stable construction. Joints tight. No visible gaps.",
                "Surface Finish (15)": "Smooth sanding. Even varnish/stain. No drips or rough patches.",
                "Functionality (15)": "Shelf stands unsupported. Holds at least 10 books. Level shelves.",
                "Time Management & Cleanup (15)": "Completed on schedule. Work area left clean. Tools returned.",
            },
            "extension": [
                "Add decorative carving or branding to the side panels using a chisel or pyrography tool.",
                "Research: What is kiln-dried vs. air-dried timber? Why does moisture content matter?",
                "Business Challenge: Calculate the selling price if you add 40% profit margin. Design a marketing flyer.",
            ],
        },
        "answer_key": (
            "Material calculation example:\n"
            "- 2 side panels: 900 mm × 250 mm = 1.8 m @ 250 mm wide\n"
            "- 3 shelves: 600 mm × 250 mm = 1.8 m @ 250 mm wide\n"
            "- Total board: ~3.6 m of 25 mm × 250 mm planks\n"
            "- At approx. GHS 15/metre, material cost ≈ GHS 54 (planks only)\n"
            "- Add sandpaper (GHS 10), nails (GHS 5), glue (GHS 15), varnish (GHS 25) = ~GHS 109 total\n\n"
            "Housing joint: A rectangular groove (dado) cut across the grain of the side panel, "
            "10 mm deep × 25 mm wide, into which the shelf sits flush. Stronger than butt joints."
        ),
    },

    # ── 2. Safety Quiz — General Workshop ─────────────────────────────────
    {
        "title": "Workshop Safety & First Aid Assessment",
        "project_type": "safety_quiz",
        "level": "b7",
        "strand": "health_safety",
        "topic": "General workshop safety rules and first aid basics",
        "description": (
            "A comprehensive safety assessment covering workshop rules, personal protective equipment "
            "(PPE), hazard identification, fire safety, and basic first aid. Every TVET student must "
            "pass this assessment before being allowed to use workshop tools and equipment."
        ),
        "content": {
            "objectives": [
                "Identify at least 5 types of Personal Protective Equipment (PPE) and their uses.",
                "Explain the colour coding of safety signs (red, yellow, blue, green).",
                "Demonstrate the correct response to common workshop emergencies: cuts, burns, electric shock.",
                "List 5 general workshop safety rules.",
                "Identify fire extinguisher types and their appropriate uses.",
            ],
            "materials": [
                "PPE samples: safety goggles, gloves, ear defenders, dust mask, steel-toe boots, apron",
                "Safety signs posters (prohibition, warning, mandatory, safe condition)",
                "First aid kit: bandages, antiseptic, burn gel, plasters, eye wash",
                "Fire extinguisher chart showing types (water, foam, CO2, powder, wet chemical)",
            ],
            "steps": [
                "1. PPE IDENTIFICATION: Match each PPE item to the hazard it protects against.",
                "2. SAFETY SIGNS: Classify 10 workshop signs by colour/shape (red circle = prohibition, yellow triangle = warning, blue circle = mandatory, green square = safe condition).",
                "3. HAZARD SPOTTING: Look at the provided workshop photograph and identify at least 8 safety hazards.",
                "4. FIRST AID SCENARIOS: Respond to 3 scenarios: (a) classmate cuts finger on a sharp edge, (b) hot metal burns someone's hand, (c) someone touches a live wire.",
                "5. FIRE SAFETY: (a) Draw the Fire Triangle (heat + fuel + oxygen). (b) Match extinguisher types to fire classes. (c) Describe the RACE procedure (Rescue, Alarm, Contain, Evacuate).",
                "6. WRITTEN QUIZ: 20 multiple-choice questions covering all topics above. Pass mark: 80% (16/20).",
            ],
            "safety_notes": [
                "This is an ASSESSMENT — students should study the workshop safety manual before attempting.",
                "Practical demonstrations must be supervised by a qualified instructor.",
                "Never attempt to fight an electrical fire with water.",
                "The first rule of first aid: ensure YOUR OWN safety before helping others.",
            ],
            "assessment": {
                "PPE Knowledge (20)": "Correctly identifies 5+ PPE items and matches to hazards",
                "Safety Signs (15)": "Correctly classifies 8+ out of 10 signs",
                "Hazard Spotting (20)": "Identifies 6+ hazards in workshop photograph",
                "First Aid Response (25)": "Correct procedure for all 3 scenarios, prioritises safety",
                "Fire Safety (20)": "Accurate Fire Triangle, correct extinguisher matching, knows RACE",
            },
            "extension": [
                "Research: What are Ghana's workplace safety laws? (Factories, Offices and Shops Act, 1970)",
                "Create a safety induction booklet for new students joining the TVET workshop.",
                "Interview a local tradesperson: What safety practices do they follow on the job?",
            ],
        },
        "answer_key": (
            "PPE matches:\n"
            "- Safety goggles → eye protection from flying particles, chemicals, sparks\n"
            "- Gloves → hand protection from cuts, heat, chemicals\n"
            "- Ear defenders → hearing protection from loud machinery\n"
            "- Dust mask → respiratory protection from sawdust, fumes\n"
            "- Steel-toe boots → foot protection from falling heavy objects\n"
            "- Apron → body protection from sparks, spills, sharp objects\n\n"
            "Safety sign colours:\n"
            "- Red circle with line = PROHIBITION (Do Not...)\n"
            "- Yellow triangle = WARNING (Danger/Caution)\n"
            "- Blue circle = MANDATORY (You Must...)\n"
            "- Green square = SAFE CONDITION (Exit, First Aid)\n\n"
            "First Aid:\n"
            "(a) Cut: Apply pressure with clean cloth, elevate hand, clean wound, apply bandage.\n"
            "(b) Burn: Cool under running water for 20 minutes. Do NOT apply butter/toothpaste. Cover with sterile dressing.\n"
            "(c) Electric shock: Do NOT touch the person. Switch off power at the source. Call for help. If safe, use CPR if needed."
        ),
    },

    # ── 3. Tool Identification — Metalwork / Auto Mechanics ───────────────
    {
        "title": "Automotive Hand Tools — Identification & Use",
        "project_type": "tool_id",
        "level": "b8",
        "strand": "tools",
        "topic": "Identifying and correctly using common automotive hand tools",
        "description": (
            "Students learn to identify, name, describe, and demonstrate the correct use of "
            "25 common automotive hand tools used in vehicle maintenance and repair. This knowledge "
            "is fundamental before students can work on any vehicle systems."
        ),
        "content": {
            "objectives": [
                "Correctly name and identify 25 common automotive hand tools from sight.",
                "Describe the specific function of each tool.",
                "Demonstrate proper handling and storage of at least 10 tools.",
                "Explain when to use metric vs. imperial tool sizes.",
                "Identify 5 situations where using the WRONG tool can cause injury or damage.",
            ],
            "materials": [
                "Tool set: combination spanners (8-19 mm), socket set (1/4\" and 1/2\" drive)",
                "Screwdrivers: flat-head (various sizes), Phillips #1, #2, #3",
                "Pliers: combination, long-nose, circlip (internal and external), locking (mole grips)",
                "Hammers: ball-pein, rubber mallet, dead-blow",
                "Allen keys (hex keys) metric set, Torx key set",
                "Adjustable spanner, pipe wrench, torque wrench",
                "Wire brush, feeler gauges, vernier caliper",
                "Tool identification worksheet with numbered photographs",
            ],
            "steps": [
                "1. VISUAL ID (30 min): Teacher displays 25 tools. Students write the name and one-sentence description for each.",
                "2. MATCHING EXERCISE: Match tool name cards to labelled photographs on the worksheet.",
                "3. DEMONSTRATION: Teacher demonstrates correct grip, use, and storage for each tool category (spanners, screwdrivers, pliers, hammers, measuring).",
                "4. PRACTICAL: Students select the correct tool for 10 given tasks (e.g., 'Remove a 14 mm bolt' → 14 mm combination spanner or 14 mm socket).",
                "5. SAFETY SCENARIOS: Discuss what happens when you: use pliers instead of a spanner on a bolt, use the wrong screwdriver size, over-torque with a breaker bar.",
                "6. METRIC vs. IMPERIAL: Explain why both systems exist in Ghana (Japanese/European cars = metric, older American cars = imperial). Practise reading imperial socket sizes.",
                "7. ASSESSMENT: Timed practical — students identify 20 tools and demonstrate correct use of 5 selected tools.",
            ],
            "safety_notes": [
                "Always PULL a spanner towards you, never push. This prevents knuckle injuries if the spanner slips.",
                "Inspect tools before use. Do not use a spanner with a cracked jaw or a screwdriver with a damaged tip.",
                "Keep tools clean and oiled to prevent rust. Return tools to the correct slot in the toolbox after use.",
                "Never use a tool as a hammer unless it IS a hammer.",
                "Wear gloves when handling oily tools to prevent slipping and skin irritation.",
            ],
            "assessment": {
                "Visual Identification (30)": "Correctly names 20+ out of 25 tools",
                "Function Description (20)": "Accurately describes the use of 15+ tools",
                "Practical Demonstration (30)": "Correct grip, technique, and tool selection for 5 tasks",
                "Safety Awareness (20)": "Identifies risks of wrong tool use, demonstrates safe handling",
            },
            "extension": [
                "Create a labelled poster of all 25 tools for the workshop wall.",
                "Visit a local 'fitting shop' (mechanic workshop). List 10 additional tools you see that were not covered in class.",
                "Business Task: Price a complete beginner mechanic toolbox. Compare prices at Abossey Okai (Accra) vs. online shops.",
            ],
        },
        "answer_key": (
            "Key tool functions:\n"
            "- Combination spanner: Open end for fast loosening, ring end for final tightening. Always use correct size.\n"
            "- Socket set: Provides full contact around bolt head — faster and less likely to round off bolt.\n"
            "- Torque wrench: Tightens bolts to a specific force (measured in Nm or ft-lbs). Essential for cylinder head bolts, wheel nuts.\n"
            "- Feeler gauges: Thin metal strips for measuring small gaps (valve clearance, spark plug gap).\n"
            "- Vernier caliper: Precise measurement of diameter, depth, and internal dimensions to 0.02 mm.\n"
            "- Long-nose pliers: Reaching into tight spaces, holding small components. NOT for turning bolts.\n"
            "- Ball-pein hammer: Metalwork shaping, riveting. The ball end is for peening (spreading) metal.\n\n"
            "Metric vs. Imperial: Most vehicles in Ghana use metric (Toyota, Nissan, Hyundai, VW). "
            "Some older American vehicles (Ford, Chevrolet) use imperial sizes (e.g., 1/2\", 9/16\", 3/4\")."
        ),
    },

    # ── 4. Innovation Challenge — Catering / Food Technology ──────────────
    {
        "title": "Nutritious School Lunch from Local Ingredients",
        "project_type": "innovation",
        "level": "shs1",
        "strand": "innovation",
        "topic": "Designing a balanced, affordable school lunch using indigenous Ghanaian ingredients",
        "description": (
            "The Ghana School Feeding Programme serves over 3 million pupils daily. Your challenge: "
            "design an improved, nutritionally balanced school lunch menu using ONLY locally available "
            "ingredients. The meal must cost no more than GHS 3 per serving, include all three "
            "macronutrient groups (carbohydrates, proteins, fats), provide at least one vitamin-rich "
            "vegetable, and be culturally acceptable to Ghanaian children."
        ),
        "content": {
            "objectives": [
                "Design a balanced lunch menu meeting all macronutrient requirements within the GHS 3 budget.",
                "Calculate the cost per serving using current local market prices.",
                "Identify the nutritional content of at least 5 local Ghanaian food items.",
                "Apply food safety principles in meal preparation (temperature control, hygiene, storage).",
                "Present the menu with a persuasive pitch to a panel of 'school officials' (classmates).",
            ],
            "materials": [
                "Local ingredients: rice, maize, beans (cowpeas), groundnuts, palm oil, tomatoes, onions, peppers, kontomire (cocoyam leaves), garden eggs, dried fish, eggs, bananas",
                "Kitchen equipment: cooking pots, stirring sticks, knives, chopping board, measuring cups",
                "Nutrition charts showing macronutrient and micronutrient content of Ghanaian foods",
                "Cost worksheet for calculating per-serving price",
                "Food safety checklist (handwashing, temperature, cross-contamination)",
            ],
            "steps": [
                "1. RESEARCH (Day 1): Study the nutritional content of 10 local ingredients. Record carbs, protein, fat, and key vitamins/minerals for each.",
                "2. MENU DESIGN (Day 2): Create a lunch menu with: 1 starch, 1 protein, 1 vegetable, 1 fruit. Example: Waakye (rice+beans) + kontomire stew + boiled egg + banana.",
                "3. COST CALCULATION (Day 2): Visit the school canteen or local market. Record prices. Calculate cost per serving for 50 students.",
                "4. NUTRITION ANALYSIS (Day 3): Using the nutrition chart, calculate approximate calories, protein (g), and key vitamins per serving. Compare to recommended levels.",
                "5. FOOD SAFETY PLAN (Day 3): Write a food safety checklist for your meal: proper handwashing, cooking temperatures, safe storage, preventing cross-contamination.",
                "6. TEST COOK (Day 4): Prepare 5 sample servings under teacher supervision. Classmates taste-test and rate (1-5) for taste, appearance, portion size.",
                "7. PRESENTATION (Day 5): Present your menu with: nutrition data, cost breakdown, taste-test results, and a persuasive argument for why the school should adopt it.",
            ],
            "safety_notes": [
                "Wash hands with soap before and after handling food.",
                "Cook all proteins (eggs, fish, beans) to safe internal temperatures.",
                "Keep raw and cooked foods separated to prevent cross-contamination.",
                "Ensure cooking area is clean. Tie back hair and wear an apron.",
                "Allergies: Ask classmates about food allergies before taste-testing. Common: groundnuts, eggs, fish.",
                "Handle knives safely — always cut on a chopping board, curl fingers under when holding food.",
            ],
            "assessment": {
                "Nutritional Balance (20)": "Meal includes all 3 macronutrients + vitamins. Matches recommended daily intake levels.",
                "Cost Efficiency (20)": "Total per-serving cost ≤ GHS 3. Realistic market prices used.",
                "Taste & Presentation (15)": "Average taste-test score ≥ 3.5/5. Visually appealing.",
                "Food Safety (15)": "Complete food safety checklist. Demonstrates proper hygiene during cooking.",
                "Innovation (15)": "Creative use of local ingredients. Novel combinations or preparation methods.",
                "Business Pitch (15)": "Clear presentation. Persuasive arguments. Responds to questions confidently.",
            },
            "extension": [
                "Create a full 5-day lunch menu (Monday-Friday) that uses different ingredients each day.",
                "Calculate the annual cost to feed 500 students using your menu. Present to the headteacher.",
                "Research: What is the Ghana School Feeding Programme? What are its successes and challenges?",
            ],
        },
        "answer_key": (
            "Sample balanced menu within GHS 3:\n"
            "- Waakye (rice + beans): GHS 1.20 — provides carbohydrates + plant protein\n"
            "- Kontomire stew with palm oil: GHS 0.80 — vitamins A, C, K + healthy fats\n"
            "- 1 boiled egg: GHS 0.70 — complete protein + B vitamins\n"
            "- 1 small banana: GHS 0.30 — potassium, fibre, natural sugar\n"
            "- TOTAL: GHS 3.00 per serving\n\n"
            "Approximate nutrition per serving:\n"
            "- Calories: ~650 kcal (target for school lunch: 600-700 kcal)\n"
            "- Protein: ~22 g (beans + egg)\n"
            "- Key vitamins: A (palm oil + kontomire), C (tomatoes + peppers), Iron (beans + kontomire)\n\n"
            "Waakye is particularly nutritious because combining rice (cereal) with beans (legume) "
            "provides complementary amino acids, creating a complete protein similar to meat."
        ),
    },

    # ── 5. Assessment Rubric — Dressmaking / Fashion ──────────────────────
    {
        "title": "Sewing a Simple A-Line Skirt — Rubric",
        "project_type": "rubric",
        "level": "b9",
        "strand": "materials",
        "topic": "Basic garment construction — pattern drafting, cutting, and stitching",
        "description": (
            "A detailed rubric and guide for assessing students as they draft a pattern, cut fabric, "
            "and sew a simple A-line skirt. This project tests fundamental dressmaking skills: "
            "body measurement, pattern drafting, fabric layout, cutting, stitching (hand and machine), "
            "finishing (hemming, waistband), and pressing."
        ),
        "content": {
            "objectives": [
                "Take accurate body measurements: waist, hip, and desired length.",
                "Draft a basic A-line skirt pattern using measurements and standard ease allowances.",
                "Lay out the pattern on fabric economically (minimising waste) and cut accurately.",
                "Sew the skirt using appropriate seams (side seams, darts if needed) by hand or machine.",
                "Finish with a waistband and hem. Press the completed garment professionally.",
            ],
            "materials": [
                "Fabric: 1.5 metres of cotton print (ankara/African print or plain cotton)",
                "Measuring tools: tape measure, metre rule, set square, French curve",
                "Pattern paper (brown paper/newspaper), pencil, eraser",
                "Pins, tailor's chalk, fabric scissors, paper scissors",
                "Thread (matching colour), hand needles, sewing machine (if available)",
                "Iron and ironing board",
                "Waistband interfacing or elastic (25 mm wide)",
            ],
            "steps": [
                "1. MEASUREMENT (Day 1): Take waist, hip, and length measurements. Record on a measurement chart. Add ease: +2 cm at waist, +4 cm at hip.",
                "2. PATTERN DRAFTING (Day 1-2): Using standard A-line skirt block, draft the front and back pattern pieces on paper. Mark grain line, notches, and seam allowances (1.5 cm).",
                "3. FABRIC PREPARATION (Day 2): Press fabric to remove creases. Check grain line. Fold fabric selvedge to selvedge.",
                "4. LAYOUT & CUTTING (Day 2): Pin pattern to fabric following grain line. Cut using fabric scissors with long, smooth strokes. Transfer all markings with tailor's chalk.",
                "5. STITCHING (Day 3-4): Sew darts first (if included). Join side seams with 1.5 cm seam allowance. Press seams open. Finish raw edges (zigzag or overlock).",
                "6. WAISTBAND (Day 4): Attach waistband or elastic casing. Ensure even gathering if using elastic.",
                "7. HEMMING (Day 5): Turn up hem (3-4 cm). Press. Stitch with blind hem or machine hemming.",
                "8. FINAL PRESSING (Day 5): Press all seams, waistband, and hem. Check overall appearance.",
            ],
            "safety_notes": [
                "Handle fabric scissors with care. Never cut paper with fabric scissors (it dulls the blade).",
                "When using a sewing machine: keep fingers away from the needle area. Secure loose clothing and hair.",
                "Iron safety: never leave a hot iron face-down on fabric. Always unplug when not in use.",
                "Pins: keep in a pincushion, not in your mouth. Pick up dropped pins immediately.",
                "Good posture: adjust chair height when machine sewing to avoid back and neck strain.",
            ],
            "assessment": {
                "Measurement Accuracy (10)": "All 3 measurements within ±0.5 cm of instructor's check. Ease correctly added.",
                "Pattern Drafting (15)": "Smooth curves, correct proportions, all markings present (grain line, notches, seam allowance).",
                "Cutting (15)": "Clean edges, correct grain alignment, minimal fabric waste. Pattern pieces match sizes.",
                "Stitching Quality (20)": "Straight seams, consistent 1.5 cm seam allowance, no puckering, even tension.",
                "Finishing (15)": "Neat waistband/elastic, even hem, raw edges finished, no loose threads.",
                "Pressing (10)": "All seams pressed flat, sharp creases where appropriate, professional appearance.",
                "Fit & Drape (15)": "Skirt hangs evenly, correct length, comfortable waist fit, A-line silhouette visible.",
            },
            "extension": [
                "Add patch pockets or decorative topstitching to personalise the skirt.",
                "Research: How does the Ghanaian fashion industry contribute to the economy? Name 3 famous Ghanaian fashion designers.",
                "Challenge: Modify the A-line pattern to create a flared or pencil skirt variation.",
            ],
        },
        "answer_key": (
            "A-line skirt pattern basics:\n"
            "- Front and back pieces are similar but the back may have a slightly deeper dart for hip curve.\n"
            "- Standard ease: +2 cm at waist (comfort), +4 cm at hip (movement).\n"
            "- Grain line runs parallel to selvedge (lengthwise grain) for proper drape.\n"
            "- Seam allowance: 1.5 cm on side seams, 3-4 cm on hem.\n\n"
            "Common student errors:\n"
            "1. Forgetting to add seam allowance → garment too small\n"
            "2. Cutting off-grain → skirt twists on the body\n"
            "3. Inconsistent seam width → wavy seam lines\n"
            "4. Not pressing seams before crossing them → bulk and puckering\n"
            "5. Hem too narrow or uneven → unprofessional finish"
        ),
    },

    # ── 6. Workshop Plan — Electrical Installation ────────────────────────
    {
        "title": "Wiring a Simple Lighting Circuit",
        "project_type": "workshop",
        "level": "shs1",
        "strand": "tools",
        "topic": "Domestic electrical installation — single-switch lighting circuit",
        "description": (
            "Students learn to wire a basic domestic lighting circuit on a practice board. The circuit "
            "includes a consumer unit (MCB), a one-gang one-way switch, a ceiling rose/batten holder, "
            "and a lamp. Students practise cable stripping, termination, and testing under strict "
            "safety protocols."
        ),
        "content": {
            "objectives": [
                "Draw a circuit diagram for a single-switch lighting circuit using standard electrical symbols.",
                "Identify components: MCB, cable (twin & earth 1.5 mm²), switch, ceiling rose, lamp holder.",
                "Strip, prepare, and terminate cables safely and neatly.",
                "Wire the circuit on a practice board following the diagram.",
                "Test the circuit for continuity, insulation resistance, and correct polarity using a multimeter.",
            ],
            "materials": [
                "Practice board (wooden board with mounted components)",
                "1.5 mm² twin and earth cable (3-core: live=brown, neutral=blue, earth=green/yellow)",
                "6A MCB (miniature circuit breaker) or fuse holder",
                "One-gang one-way light switch (plate switch)",
                "Batten holder or ceiling rose + bayonet lamp + ES lamp (60W equivalent LED)",
                "Cable strippers, side cutters, flat and Phillips screwdrivers (electrician's type with insulated handles)",
                "Multimeter (set to continuity, resistance, and AC voltage modes)",
                "Insulation tape, cable clips, junction box (optional)",
            ],
            "steps": [
                "1. THEORY (Day 1): Draw the circuit diagram. Label Live (L), Neutral (N), Earth (E), Switch Wire (SL). Explain how current flows from supply → switch → lamp → return.",
                "2. COMPONENT ID (Day 1): Lay out all components. Students identify each one, describe its function, and explain where it fits in the circuit.",
                "3. CABLE PREPARATION (Day 2): Practise stripping outer sheath (100 mm) without damaging inner insulation. Strip 10 mm of insulation from each core. Identify cores by colour.",
                "4. WIRING — SUPPLY TO SWITCH (Day 2): Run cable from MCB to switch. Terminate Live (brown) to switch terminal 'COM'. Run Neutral (blue) through to ceiling rose. Earth to earth terminal.",
                "5. WIRING — SWITCH TO LAMP (Day 3): Run cable from switch terminal 'L1' to ceiling rose/lamp holder Live terminal. This is the 'switch wire' — sleeve the blue core with brown sleeving to indicate it carries switched live.",
                "6. WIRING — LAMP (Day 3): Terminate Neutral at lamp holder. Connect Earth to metal parts of lamp holder (if applicable). Ensure no bare copper is exposed outside terminals.",
                "7. VISUAL INSPECTION (Day 4): Check all connections are tight. No bare copper visible. Correct polarity. Cable secured with clips. Earth sleeved correctly.",
                "8. TESTING (Day 4): Using multimeter: (a) Continuity test — check circuit path with switch ON, (b) Insulation resistance test — check no shorts between L-N, L-E, N-E with switch OFF, (c) Polarity test — verify brown=Live, blue=Neutral at lamp holder.",
                "9. ENERGISE & TEST (Day 4): Under instructor supervision, connect to 12V DC supply (NOT mains). Verify lamp operates when switch is toggled. De-energise immediately after test.",
            ],
            "safety_notes": [
                "NEVER work on a live circuit. Always isolate the supply and verify it is dead before touching any wiring.",
                "Use ONLY insulated tools rated for electrical work (indicated by VDE or GS markings on handles).",
                "Practice boards use 12V DC supply — this is safe. NEVER connect a practice board to mains (230V AC) without instructor supervision.",
                "Insulation resistance between any two conductors must be > 1 MΩ before energising.",
                "Report any exposed copper, loose connections, or damaged insulation to the instructor before testing.",
                "In a real installation, all electrical work in Ghana must comply with the Energy Commission's Wiring Regulations and be carried out by a licensed electrician.",
            ],
            "assessment": {
                "Circuit Diagram (15)": "Correct symbols, clear layout, all components labelled, current flow path indicated",
                "Cable Preparation (15)": "Clean stripping, correct lengths exposed, no nicks in inner insulation",
                "Wiring Quality (25)": "Correct connections, tight terminals, proper polarity, neat cable runs",
                "Testing (20)": "Continuity confirmed, insulation resistance > 1 MΩ, polarity correct at all points",
                "Safety Compliance (15)": "Used insulated tools, verified dead before touching, reported issues properly",
                "Neatness & Professional Standard (10)": "Cables clipped neatly, no excess cable showing, professional appearance",
            },
            "extension": [
                "Wire a TWO-WAY switching circuit (two switches controlling one light — used for staircases and hallways).",
                "Research: What is the colour coding for electrical cables in Ghana vs. the UK vs. the USA?",
                "Calculate: If a household has 10 LED bulbs at 9W each, running 5 hours/day, what is the monthly electricity cost at GHS 1.20 per kWh?",
            ],
        },
        "answer_key": (
            "Circuit flow: Supply → MCB (protection) → Switch COM terminal → [when ON] → Switch L1 → Lamp (Live) → Lamp (Neutral) → Return to supply.\n\n"
            "Cable colour code (Ghana/BS 7671):\n"
            "- Live: Brown\n"
            "- Neutral: Blue\n"
            "- Earth: Green/Yellow stripes\n"
            "- Switch wire (blue used as live): Must be sleeved with brown sleeving\n\n"
            "Testing values:\n"
            "- Continuity: < 1 Ω (near zero) when switch is ON\n"
            "- Insulation resistance: > 1 MΩ between L-N, L-E, N-E with switch OFF\n"
            "- Polarity: Brown core must connect to the centre pin of bayonet holder (safety requirement)\n\n"
            "Extension calculation:\n"
            "10 bulbs × 9W = 90W total\n"
            "90W × 5 hours/day = 450 Wh = 0.45 kWh/day\n"
            "0.45 kWh × 30 days = 13.5 kWh/month\n"
            "13.5 × GHS 1.20 = GHS 16.20/month"
        ),
    },

    # ── 7. Project Plan — Masonry / Building Construction ─────────────────
    {
        "title": "Build a Single-Skin Block Wall (1m × 1m)",
        "project_type": "project_plan",
        "level": "b9",
        "strand": "materials",
        "topic": "Basic masonry — setting out, mixing mortar, laying blocks",
        "description": (
            "Students construct a 1-metre high × 1-metre wide single-skin practice wall using "
            "standard 150 mm sandcrete blocks and cement-sand mortar. This introductory project "
            "teaches the fundamental masonry skills: setting out, mortar mixing, block laying, "
            "levelling, plumbing, and pointing."
        ),
        "content": {
            "objectives": [
                "Set out a straight, level foundation line using a string line and spirit level.",
                "Mix mortar to the correct ratio (1 cement : 4 sand) achieving workable consistency.",
                "Lay 5 courses of blockwork achieving level courses and plumb (vertical) faces.",
                "Maintain consistent mortar joints (10-12 mm thickness).",
                "Point (finish) the mortar joints neatly using a pointing trowel or jointer.",
            ],
            "materials": [
                "Sandcrete blocks: ~20 standard blocks (450 mm × 225 mm × 150 mm)",
                "Portland cement: approximately 10 kg (¼ bag)",
                "Sharp (coarse) sand: approximately 40 kg",
                "Clean water for mixing mortar",
                "Bricklaying/block trowel, pointing trowel",
                "Spirit level (900 mm), plumb bob, builder's line and pins",
                "Mixing board or platform (not bare ground), shovel, bucket, watering can",
                "String line, corner blocks, tape measure (5 m)",
            ],
            "steps": [
                "1. SITE PREPARATION (Day 1): Clear and level the work area. Set up mixing station nearby. Dampen blocks the day before (dry blocks absorb too much moisture from mortar).",
                "2. SETTING OUT (Day 1): Mark the wall position using string line. Check it's straight using a long spirit level. Mark the first block position.",
                "3. MORTAR MIXING (Day 1): Mix 1:4 (cement:sand) on the mixing board. Add water gradually — mortar should hold its shape when cut with a trowel but not be crumbly.",
                "4. FIRST COURSE (Day 2): Spread a mortar bed (~15 mm thick, slightly thicker than joints to allow for settlement). Lay first block. Check level across the top and plumb on the face. Butter the end of the next block and push into place. Maintain 10 mm perpend (vertical) joints.",
                "5. BUILD CORNERS FIRST (Day 2): Lay corner/end blocks first, using the spirit level. Stretch the string line between corners as a guide for the course.",
                "6. SUBSEQUENT COURSES (Day 3-4): Apply mortar bed on top of previous course. Stagger joints (half-bond pattern — each block overlaps the one below by half). Check level and plumb every 2-3 blocks.",
                "7. POINTING (Day 5): When mortar is 'thumb-print hard' (firm but not fully set), rake joints to 5 mm depth and finish with a concave or flush profile using a jointer or pointing trowel.",
                "8. CURING (Day 5+): Keep the wall damp for 3-7 days by covering with damp sacking or light water spraying. This prevents rapid drying and cracking.",
            ],
            "safety_notes": [
                "Cement is caustic — wear gloves when mixing mortar. Wash hands immediately if cement contacts skin.",
                "Blocks are heavy (~15 kg each). Use proper lifting technique: bend at the knees, keep back straight.",
                "Keep the work area clean. Mortar on the ground is a slip hazard.",
                "Wear safety boots — dropped blocks can cause serious foot injuries.",
                "Do not stand on an incomplete wall for height. Use a proper scaffold or step for upper courses.",
            ],
            "assessment": {
                "Setting Out (10)": "Straight foundation line, level base, accurate positioning",
                "Mortar Quality (15)": "Correct mix ratio, workable consistency, no dry lumps",
                "Block Laying (25)": "Level courses (within 3 mm over 1 m), plumb faces, consistent 10-12 mm joints",
                "Bond Pattern (15)": "Correct half-bond. No continuous vertical joints (which cause structural weakness).",
                "Pointing (15)": "Neat, consistent joint finish. No mortar smears on block faces.",
                "Safety & Housekeeping (20)": "PPE worn, correct lifting, clean work area, tools cleaned after use",
            },
            "extension": [
                "Build a wall with a 90° corner (return). This requires cutting blocks and maintaining bond at the corner.",
                "Research: What is the difference between sandcrete blocks and burnt bricks? Which is more common in Ghana and why?",
                "Calculation: How many blocks and bags of cement are needed for a 3 m × 2.4 m wall? (Standard block rate ≈ 10 blocks per m²)",
            ],
        },
        "answer_key": (
            "Block calculation for practice wall:\n"
            "- Wall area: 1.0 m × 1.0 m = 1.0 m²\n"
            "- Blocks per m² (150 mm blocks with 10 mm joints): ≈ 10\n"
            "- Number of courses: 1000 mm ÷ (225 mm + 10 mm) ≈ 4.3 → need 5 courses\n"
            "- Blocks per course: 1000 mm ÷ (450 mm + 10 mm) ≈ 2.2 → need 2-3 blocks per course\n"
            "- Total: ~15-20 blocks (allowing for half-blocks and breakage)\n\n"
            "Mortar ratio: 1:4 (cement:sand)\n"
            "- For 1 m² of blockwork, approximately 0.02 m³ of mortar is needed.\n"
            "- That's about 4 kg cement + 16 kg sand per m².\n\n"
            "Half-bond pattern: Each course is offset by half a block (225 mm). "
            "This distributes loads evenly and prevents continuous vertical cracks (which would make the wall structurally weak)."
        ),
    },

    # ── 8. Safety Quiz — Food Hygiene / Catering ─────────────────────────
    {
        "title": "Food Safety & Hygiene Quiz — Catering Workshop",
        "project_type": "safety_quiz",
        "level": "b8",
        "strand": "health_safety",
        "topic": "Food handling safety, personal hygiene, and kitchen sanitation",
        "description": (
            "A comprehensive food safety assessment covering personal hygiene, food storage, "
            "cross-contamination prevention, temperature control (the danger zone), and kitchen "
            "cleaning protocols. Must be passed before students can participate in practical cooking."
        ),
        "content": {
            "objectives": [
                "Explain why personal hygiene is critical in food preparation.",
                "Describe the 'Danger Zone' temperature range and why it matters.",
                "Identify 5 common causes of food poisoning and how to prevent each.",
                "Demonstrate correct handwashing technique (WHO 6-step method).",
                "List the correct order for kitchen cleaning: clean, rinse, sanitise.",
            ],
            "materials": [
                "Food safety posters (handwashing, danger zone, cross-contamination)",
                "Thermometer (digital probe type) for demonstrating temperature checks",
                "Handwashing station with soap, running water, paper towels",
                "Colour-coded chopping board chart (red=raw meat, blue=fish, green=salad/fruit, yellow=cooked meat, white=dairy/bread, brown=vegetables)",
            ],
            "steps": [
                "1. PERSONAL HYGIENE (15 min): Demonstrate and practise the WHO 6-step handwashing technique. Discuss: When must you wash hands? (Before cooking, after toilet, after handling raw meat, after sneezing, after handling waste.)",
                "2. DANGER ZONE (15 min): Teach the danger zone: 5°C to 60°C — bacteria multiply rapidly. Food should be stored below 5°C (fridge) or cooked above 75°C (centre temperature). Display poster.",
                "3. CROSS-CONTAMINATION (15 min): Explain how bacteria transfer between foods. Demonstrate colour-coded chopping boards. Emphasise: raw meat must NEVER touch ready-to-eat food.",
                "4. FOOD STORAGE (15 min): Teach the fridge rule: cooked food on TOP shelves, raw meat on BOTTOM shelves (prevents dripping). Check 'use by' dates. FIFO principle: First In, First Out.",
                "5. COMMON FOOD PATHOGENS (15 min): Salmonella (undercooked poultry), E. coli (raw/undercooked beef), Staphylococcus (handler's skin infections), Campylobacter (raw chicken), Listeria (unpasteurised dairy).",
                "6. WRITTEN QUIZ (30 min): 25 True/False and multiple-choice questions. Pass mark: 80% (20/25).",
            ],
            "safety_notes": [
                "This assessment is mandatory before practical kitchen work begins.",
                "Students who fail must resit before being allowed to handle food.",
                "Emphasise: food safety is everyone's responsibility, not just cooks.",
                "Refer to Ghana's Food and Drugs Authority (FDA) guidelines for commercial food safety.",
            ],
            "assessment": {
                "Personal Hygiene Knowledge (20)": "Correct handwashing technique, knows 5+ situations requiring hand hygiene",
                "Temperature Control (20)": "Accurately states danger zone, correct fridge/cooking temperatures",
                "Cross-Contamination (20)": "Understands bacteria transfer, colour-coded board system, raw/cooked separation",
                "Food Storage (20)": "Correct fridge stacking order, understands FIFO, checks use-by dates",
                "Written Quiz Score (20)": "Minimum 20/25 (80%) to pass",
            },
            "extension": [
                "Visit a local chop bar or restaurant. Observe food handling practices. Write a safety report with recommendations.",
                "Research: What foodborne disease outbreaks have occurred in Ghana recently? What were the causes?",
                "Create a food safety training poster in TWO languages (English + a local Ghanaian language).",
            ],
        },
        "answer_key": (
            "Key facts:\n"
            "- Danger Zone: 5°C – 60°C. Bacteria double every 20 minutes in this range.\n"
            "- Safe fridge temperature: 0-5°C\n"
            "- Safe cooking centre temperature: 75°C or above\n"
            "- Handwashing duration: minimum 20 seconds with soap\n\n"
            "Colour-coded chopping boards:\n"
            "- Red: raw meat\n"
            "- Blue: raw fish\n"
            "- Green: salad and fruit (ready-to-eat)\n"
            "- Yellow: cooked meat\n"
            "- White: dairy and bread\n"
            "- Brown: vegetables\n\n"
            "Fridge stacking (top to bottom):\n"
            "1. Ready-to-eat food (top)\n"
            "2. Dairy products\n"
            "3. Cooked meat\n"
            "4. Raw vegetables\n"
            "5. Raw meat and fish (bottom) — prevents dripping onto other food\n\n"
            "WHO 6-step handwashing:\n"
            "1. Palm to palm\n"
            "2. Right palm over left dorsum (and vice versa)\n"
            "3. Palm to palm, fingers interlaced\n"
            "4. Backs of fingers to opposing palms\n"
            "5. Rotational rubbing of thumbs\n"
            "6. Rotational rubbing of fingertips in palm"
        ),
    },

    # ── 9. Innovation Challenge — Renewable Energy ────────────────────────
    {
        "title": "Solar Phone Charger — Design & Build Challenge",
        "project_type": "innovation",
        "level": "shs1",
        "strand": "innovation",
        "topic": "Solar energy application — building a portable solar phone charger",
        "description": (
            "Ghana receives an average of 4-6 hours of peak sunshine per day, making solar energy "
            "a viable alternative power source. In this innovation challenge, students design and "
            "build a portable solar phone charger using affordable, locally available components. "
            "The charger must be able to charge a standard mobile phone from 0% to at least 20% "
            "in direct sunlight."
        ),
        "content": {
            "objectives": [
                "Explain how photovoltaic (PV) cells convert sunlight into electricity.",
                "Calculate the power output needed to charge a mobile phone (5V, 1A = 5W minimum).",
                "Select and assemble components: solar panel, USB voltage regulator, diode, and wiring.",
                "Test the charger's output using a multimeter (voltage and current).",
                "Design a protective casing that makes the charger portable and weather-resistant.",
            ],
            "materials": [
                "Small solar panel: 6V, 2W (or 6V, 3.5W for faster charging) — available at electronics shops in Accra/Kumasi",
                "USB voltage regulator module (buck converter 5V output) — approximately GHS 10",
                "1N5817 Schottky diode (prevents reverse current flow)",
                "USB Type-A female connector (for connecting phone cable)",
                "Hookup wire (red and black, 22 AWG), solder and soldering iron",
                "Multimeter for testing voltage and current output",
                "Protective casing materials: small plastic box, hot glue, zip ties",
                "USB cable for testing with actual phone",
            ],
            "steps": [
                "1. THEORY (Day 1): Learn how PV cells work. Understand: Voltage (V) = electrical 'pressure', Current (A) = flow of electricity, Power (W) = V × A. A phone needs 5V, 1-2A.",
                "2. COMPONENT CHECK (Day 1): Test the solar panel output with multimeter in sunlight. Record open-circuit voltage (should be ~6-7V) and short-circuit current.",
                "3. CIRCUIT DESIGN (Day 2): Draw the circuit: Solar panel (+) → Schottky diode (anode to panel, cathode to regulator) → USB voltage regulator (input) → USB regulator (output 5V) → USB female connector → Phone.",
                "4. SOLDERING (Day 2-3): Solder the diode to the solar panel positive lead. Solder input wires to the voltage regulator. Solder output wires to the USB connector. Observe polarity carefully.",
                "5. TESTING (Day 3): Connect multimeter to USB output. In sunlight, verify: voltage = 4.9-5.2V, current = 0.3-1.0A (depending on panel size and sun intensity). If voltage is wrong, check regulator and connections.",
                "6. PHONE TEST (Day 4): Connect a phone via USB cable. Verify charging indicator appears. Time how long it takes to charge from a known starting percentage.",
                "7. CASING (Day 4-5): Design and build a protective case. Consider: angling the panel for maximum sun exposure, protecting the electronics from rain, making it portable.",
                "8. PRESENTATION (Day 5): Present your charger with: circuit diagram, test measurements, charging time data, cost breakdown, and suggestions for improvement.",
            ],
            "safety_notes": [
                "Soldering iron is extremely hot (300°C+). Never touch the tip. Place on a proper stand when not in use.",
                "Solder in a well-ventilated area — solder fume can irritate lungs. Use a fume extractor or fan.",
                "Wear safety goggles when soldering — solder can spit.",
                "The Schottky diode is essential — without it, the phone battery could discharge back through the solar panel in shade.",
                "Never short-circuit the solar panel leads — this can damage the panel.",
                "Keep water away from electronics during testing.",
            ],
            "assessment": {
                "Understanding (15)": "Can explain PV operation, V/I/P relationship, and why each component is needed",
                "Circuit Assembly (25)": "Correct component placement, clean solder joints, proper polarity throughout",
                "Testing & Data (20)": "Accurate multimeter readings, records open-circuit and loaded voltage/current, identifies issues",
                "Phone Charging (20)": "Charger successfully provides 5V to phone, charging indicator appears, reports charge rate",
                "Innovation & Design (10)": "Creative casing, practical portability features, weather protection",
                "Cost Analysis (10)": "Complete bill of materials with prices, total cost calculated, comparison to commercial chargers",
            },
            "extension": [
                "Add a small lithium battery (power bank) so the charger stores energy for use after sunset.",
                "Calculate: How many panels would you need to power a 12V LED light for 4 hours per evening?",
                "Research: What is the Energy Commission of Ghana doing to promote solar energy? What incentives exist?",
                "Business Plan: Design a solar charger product for market stall vendors who need phone power all day.",
            ],
        },
        "answer_key": (
            "Power calculations:\n"
            "- Phone charging requirement: 5V × 1A = 5W minimum\n"
            "- 6V, 2W panel provides ~0.33A at 6V → after voltage regulation to 5V, gives ~0.35A → slow but works\n"
            "- 6V, 3.5W panel provides ~0.58A at 6V → gives ~0.6A at 5V → moderate charging speed\n"
            "- For fast charging (1A), need at minimum a 6V, 6W panel\n\n"
            "Component costs (Accra market prices, approx.):\n"
            "- 6V 2W solar panel: GHS 30-50\n"
            "- USB voltage regulator: GHS 10-15\n"
            "- Schottky diode: GHS 2\n"
            "- USB connector: GHS 5\n"
            "- Wire, solder, casing: GHS 15\n"
            "- TOTAL: approximately GHS 62-87\n"
            "- Commercial solar charger (5W): GHS 120-200\n\n"
            "Schottky diode purpose: Has a low forward voltage drop (~0.3V vs 0.7V for standard diode) "
            "and blocks reverse current, preventing phone battery from discharging through the panel when there's no sunlight."
        ),
    },

    # ── 10. Tool ID — Dressmaking / Textiles ──────────────────────────────
    {
        "title": "Sewing Tools & Equipment — Identification Quiz",
        "project_type": "tool_id",
        "level": "b7",
        "strand": "tools",
        "topic": "Identifying and describing the use of common sewing tools and equipment",
        "description": (
            "Students identify, name, and describe the function of 20 common sewing/dressmaking "
            "tools and equipment items. This foundational knowledge is essential before students "
            "begin any practical sewing projects."
        ),
        "content": {
            "objectives": [
                "Correctly identify 20 common sewing tools from sight.",
                "Describe the specific function of each tool in garment construction.",
                "Classify tools into categories: measuring, cutting, marking, sewing, pressing.",
                "Demonstrate correct handling and care of 5 key tools.",
                "Explain 3 safety rules specific to sewing tools.",
            ],
            "materials": [
                "Measuring: tape measure (150 cm), metre rule, set square, French curve, hip curve",
                "Cutting: fabric scissors (bent-handle), paper scissors, pinking shears, seam ripper, rotary cutter",
                "Marking: tailor's chalk, tracing wheel & carbon paper, pins, pin cushion",
                "Sewing: hand needles (assorted), machine needles, thimble, bobbin, sewing machine (labelled diagram)",
                "Pressing: iron, ironing board, pressing cloth, tailor's ham, sleeve board",
                "Identification worksheet with numbered photographs",
            ],
            "steps": [
                "1. DISPLAY (20 min): Teacher sets up 20 numbered tools on a display table. Students walk around and write the name of each tool on their worksheet.",
                "2. FUNCTION MATCHING (15 min): Match each tool name to its description card. Example: 'Pinking shears' → 'Scissors with zigzag blade that cuts fabric edges to reduce fraying.'",
                "3. CLASSIFICATION (10 min): Sort all 20 tools into 5 categories: Measuring, Cutting, Marking, Sewing, Pressing.",
                "4. DEMONSTRATION (20 min): Teacher demonstrates correct use of: tape measure (body measurement), fabric scissors (cutting fabric on table), tailor's chalk (marking seam lines), thimble (push-needle technique), iron (pressing open a seam).",
                "5. STUDENT PRACTICE (20 min): Students practise using 5 tools on scrap fabric: measure a line, cut along it, mark a seam allowance, hand-stitch a running stitch, press the seam.",
                "6. QUIZ (20 min): 20 questions — name the tool from its photo and describe one use.",
            ],
            "safety_notes": [
                "Never put pins in your mouth — use a pin cushion at all times.",
                "Pass scissors handle-first when giving to another person.",
                "Keep fabric scissors sharp and ONLY use them on fabric (paper dulls the blade quickly).",
                "The iron is extremely hot — never leave it face-down on fabric. Always unplug when finished.",
                "Store needles in a needle case, not loose on the table.",
            ],
            "assessment": {
                "Visual Identification (40)": "Correctly names 16+ out of 20 tools",
                "Function Description (30)": "Accurately describes the use of 12+ tools",
                "Classification (15)": "Correctly sorts 16+ tools into the right category",
                "Practical Handling (15)": "Demonstrates correct and safe use of 5 key tools",
            },
            "extension": [
                "Create a labelled poster of all 20 tools for the textile room wall.",
                "Compare: What tools does a tailor use that are NOT in the school toolkit? Visit a local tailor to find out.",
                "History: Research the history of the sewing machine. Who invented it and when did it arrive in Ghana?",
            ],
        },
        "answer_key": (
            "Key tool descriptions:\n"
            "- Tape measure: Flexible 150 cm ribbon for taking body measurements. Check it hasn't stretched over time.\n"
            "- Fabric scissors (bent-handle/dressmaking shears): Angled handle allows fabric to lie flat on table while cutting. 20-25 cm blade.\n"
            "- Pinking shears: Zigzag blade cuts fabric edges to reduce fraying. Not used for main cutting.\n"
            "- Seam ripper: Small blade with hook for removing stitches without cutting fabric.\n"
            "- Tailor's chalk: Marks fabric temporarily for cutting lines, darts, and seam allowances. Brushes off or vanishes with heat.\n"
            "- Tracing wheel & carbon paper: Transfers pattern markings to fabric using pressure.\n"
            "- Thimble: Worn on middle finger to push needle through thick fabric. Prevents finger injury.\n"
            "- Bobbin: Small spool that holds the lower thread in a sewing machine.\n"
            "- French curve: Curved ruler for drawing smooth necklines, armholes, and hip curves on patterns.\n"
            "- Tailor's ham: Firm, rounded cushion for pressing curved seams (darts, princess seams, sleeves).\n\n"
            "Classification:\n"
            "Measuring: tape measure, metre rule, set square, French curve, hip curve\n"
            "Cutting: fabric scissors, paper scissors, pinking shears, seam ripper, rotary cutter\n"
            "Marking: tailor's chalk, tracing wheel, pins, pin cushion\n"
            "Sewing: hand needles, machine needles, thimble, bobbin, sewing machine\n"
            "Pressing: iron, ironing board, pressing cloth, tailor's ham, sleeve board"
        ),
    },
]

created = 0
for p in PROJECTS:
    obj, was_created = TVETProject.objects.get_or_create(
        profile=profile,
        title=p["title"],
        defaults=p,
    )
    if was_created:
        created += 1
        print(f"  + {obj.title}")
    else:
        print(f"  = {obj.title} (exists)")

total = TVETProject.objects.filter(profile=profile).count()
print(f"\nCreated {created} new projects. Total for {profile}: {total}")
