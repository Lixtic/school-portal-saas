"""Seed Citizen Education with sample activities across all 7 types."""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from individual_users.models import IndividualProfile, CitizenEdActivity

profile = IndividualProfile.objects.get(id=2)
print(f"Seeding citizen education activities for: {profile}")

ACTIVITIES = [
    # ── 1. Case Study ─────────────────────────────────────────────────────
    {
        "title": "The Akosombo Dam — Development vs. Displacement",
        "activity_type": "case_study",
        "level": "b9",
        "strand": "economics",
        "topic": "Development projects and their impact on communities",
        "scenario_text": (
            "In 1965, the Akosombo Dam was completed on the Volta River in the Eastern Region of Ghana. "
            "The dam created Lake Volta — the largest man-made lake in the world by surface area — and "
            "generates hydroelectric power that supplies most of Ghana's electricity and exports to "
            "neighbouring countries.\n\n"
            "However, the dam's construction came at a significant human cost. Over 80,000 people from "
            "more than 700 villages were displaced and relocated to resettlement towns. Many lost their "
            "ancestral farmlands, fishing grounds, and sacred sites. The resettlement towns often lacked "
            "adequate infrastructure, and promises of compensation were not fully kept.\n\n"
            "Today, the dam provides approximately 1,020 megawatts of electricity, supports aluminium "
            "smelting at the Valco plant in Tema, and enables fishing and transportation on Lake Volta. "
            "Yet communities around the lake continue to face challenges including waterborne diseases "
            "(especially schistosomiasis), loss of biodiversity, and periodic flooding when the dam "
            "spillway is opened."
        ),
        "content": {
            "questions": [
                "List THREE benefits the Akosombo Dam has provided to Ghana's economy.",
                "Describe TWO negative effects the dam had on the displaced communities.",
                "Do you think the government made the right decision to build the dam? Justify your answer with at least two reasons.",
                "If a similar project were proposed today, what steps should the government take to protect affected communities?",
                "Research: What is the Bui Dam? How did the government learn from the Akosombo experience?",
            ],
            "key_points": [
                "Development projects can bring national benefits but local hardships.",
                "Displacement disrupts livelihoods, cultural ties, and community bonds.",
                "Governments must balance economic growth with social justice.",
                "Environmental Impact Assessments (EIAs) are now required by law in Ghana.",
                "The 1992 Constitution (Article 20) protects citizens against arbitrary seizure of property.",
            ],
            "tasks": [
                "Group Task: Divide into 'Government Officials' and 'Affected Villagers' — role-play a community meeting about the dam.",
                "Individual Task: Write a 200-word letter from a displaced farmer to the President in 1965, explaining how the relocation affected your family.",
                "Research Task: Compare the Akosombo Dam to the Three Gorges Dam in China. What similarities and differences exist?",
            ],
            "resources": [
                "Ghana National Archives — Volta River Authority documents",
                "Environmental Protection Agency (EPA) Ghana — EIA guidelines",
                "Article 20, 1992 Constitution of the Republic of Ghana",
            ],
        },
        "answer_guide": (
            "Q1: Benefits include hydroelectric power generation (1,020 MW), lake fishing industry, "
            "inland water transportation, electricity export to Togo/Benin, and support for Valco aluminium smelting.\n\n"
            "Q2: Negative effects include displacement of 80,000+ people from ancestral lands, "
            "spread of waterborne diseases (schistosomiasis), loss of sacred/cultural sites, "
            "inadequate resettlement infrastructure, and unfulfilled compensation promises.\n\n"
            "Q3: Accept either position if well-argued. FOR: national development, electricity access, "
            "economic growth. AGAINST: violation of human rights, cultural destruction, broken promises.\n\n"
            "Q4: Modern steps should include: Environmental Impact Assessment, Free Prior and Informed "
            "Consent (FPIC), fair compensation at market value, adequate resettlement planning, "
            "ongoing monitoring, and community benefit-sharing agreements."
        ),
    },

    # ── 2. Debate / Discussion Prompt ─────────────────────────────────────
    {
        "title": "Should Traditional Chiefs Have Political Power?",
        "activity_type": "debate",
        "level": "shs1",
        "strand": "governance",
        "topic": "Chieftaincy and modern governance",
        "scenario_text": (
            "Ghana's 1992 Constitution recognises the institution of chieftaincy alongside democratic "
            "governance. Article 270 guarantees the institution, while Article 276 prohibits chiefs from "
            "taking part in active party politics. The National House of Chiefs and Regional Houses of "
            "Chiefs serve as advisory bodies.\n\n"
            "Some argue that chiefs should have more formal political power because they are closer to "
            "their communities, command respect, and understand local needs better than elected politicians. "
            "Others contend that hereditary leadership contradicts democratic principles and that giving "
            "chiefs political power would concentrate authority in unelected hands.\n\n"
            "In 2023, the Asantehene, Otumfuo Osei Tutu II, mediated a long-standing chieftaincy dispute "
            "in the Dagbon Kingdom, demonstrating the institution's capacity for conflict resolution. "
            "Meanwhile, some chieftaincy disputes themselves have led to violence, as rival factions "
            "contest succession."
        ),
        "content": {
            "questions": [
                "What role does the 1992 Constitution assign to chiefs in Ghana's governance?",
                "Why does Article 276 prohibit chiefs from active party politics? What problems could arise if this rule were removed?",
                "Prepare THREE arguments FOR giving chiefs more political power.",
                "Prepare THREE arguments AGAINST giving chiefs more political power.",
                "Should the National House of Chiefs have the power to veto laws that affect traditional lands? Explain your position.",
            ],
            "key_points": [
                "Chieftaincy is a pre-colonial institution that predates modern democracy in Ghana.",
                "Article 270: 'The institution of chieftaincy, together with its traditional councils... is hereby guaranteed.'",
                "Article 276: 'A chief shall not take part in active party politics.'",
                "Chiefs serve as custodians of land, culture, and community identity.",
                "The Dagbon crisis (2002-2019) shows both the strengths and vulnerabilities of chieftaincy.",
            ],
            "tasks": [
                "Debate: Two teams — 'Chiefs Should Have More Power' vs. 'Current System is Best'. Use Articles 270-277 as evidence.",
                "Essay: In 300 words, argue whether Ghana's dual system (chiefs + elected officials) strengthens or weakens governance.",
                "Interview: Ask an elder in your community about the role of your local chief. Report findings to the class.",
            ],
        },
        "answer_guide": (
            "FOR more power: Chiefs are closer to communities, have historical legitimacy, "
            "effective at dispute resolution, custodians of land and culture, provide continuity.\n\n"
            "AGAINST more power: Hereditary leadership is undemocratic, risk of abuse (chiefs can't be voted out), "
            "gender inequality in succession, chieftaincy disputes can cause violence, "
            "potential conflict with elected representatives.\n\n"
            "Current constitutional balance: Chiefs advise but don't legislate, can't join parties, "
            "maintain cultural authority without democratic accountability issues."
        ),
    },

    # ── 3. Citizenship Scenario ───────────────────────────────────────────
    {
        "title": "Reporting Corruption — What Would You Do?",
        "activity_type": "scenario",
        "level": "b8",
        "strand": "citizenship",
        "topic": "Anti-corruption and civic responsibility",
        "scenario_text": (
            "You are a Form 2 student at a public school. Your school was supposed to receive 200 new "
            "desks from the District Assembly, but only 120 arrived. Your class teacher privately tells "
            "you that a school official kept 80 desks and is selling them in the market.\n\n"
            "You see the school official at the market the next Saturday, and he has the desks with the "
            "school's stamp still visible. He notices you looking and says, 'Mind your own business — "
            "you're just a child.'\n\n"
            "You know that the Commission on Human Rights and Administrative Justice (CHRAJ) handles "
            "corruption complaints, and there's also a corruption hotline. Your parents warn you that "
            "reporting powerful people can have consequences."
        ),
        "content": {
            "questions": [
                "Is what the school official did illegal? Which law does it violate?",
                "List THREE possible actions you could take in this situation.",
                "What are the RISKS of reporting the corruption? What are the risks of staying silent?",
                "Role Play: In pairs, act out a phone call to the CHRAJ hotline reporting this incident. What information would they need?",
                "Ghana's motto is 'Freedom and Justice.' How does this scenario test those values?",
            ],
            "key_points": [
                "Corruption is defined as the abuse of public office for private gain.",
                "The Public Procurement Act (Act 663) governs how government purchases are handled.",
                "CHRAJ (Article 218, 1992 Constitution) investigates corruption and human rights abuses.",
                "The Whistleblower Act (Act 720, 2006) protects people who report corruption.",
                "Every citizen has a civic duty to report wrongdoing, regardless of age.",
            ],
            "tasks": [
                "Write a formal complaint letter to CHRAJ describing the missing desks incident.",
                "Create a poster for your school notice board about the Whistleblower Act and how students can report corruption safely.",
                "Class Discussion: Why do you think corruption persists in some institutions? What can young people do?",
            ],
        },
        "answer_guide": (
            "Yes, the official committed theft of public property (Criminal Offences Act, 1960) "
            "and likely violated the Public Procurement Act.\n\n"
            "Possible actions: Report to CHRAJ, inform the school board/PTA, tell a trusted adult, "
            "report anonymously via corruption hotline, inform the District Education Office.\n\n"
            "Risks of reporting: retaliation, social pressure, mistrust from authority figures.\n"
            "Risks of silence: theft continues, students suffer (fewer desks), normalises corruption.\n\n"
            "The Whistleblower Act (720) provides legal protection and potential financial reward "
            "for those who report corruption in good faith."
        ),
    },

    # ── 4. Map / Geography Activity ───────────────────────────────────────
    {
        "title": "Ghana's Regions & Resources — Mapping Activity",
        "activity_type": "map_activity",
        "level": "b7",
        "strand": "environment",
        "topic": "Regional distribution of natural resources",
        "scenario_text": (
            "Ghana is rich in natural resources distributed unevenly across its 16 administrative regions. "
            "Gold is concentrated in the Western, Ashanti, and Eastern Regions. Cocoa thrives in the "
            "forest zones of Western North, Ashanti, and Eastern Regions. Oil and gas are extracted "
            "offshore in the Western Region (Jubilee and TEN fields). Bauxite deposits exist in the "
            "Ashanti Region (Nyinahin) and Western Region (Awaso). Timber comes from the high forest "
            "zones, while salt is produced in the Greater Accra (Songor Lagoon) and Volta Regions. "
            "The Volta Lake provides freshwater fish and hydroelectric power."
        ),
        "content": {
            "questions": [
                "On a blank map of Ghana, label all 16 regions and their capitals.",
                "Using symbols or colours, mark the location of: gold, cocoa, oil/gas, bauxite, timber, salt, and fish.",
                "Create a KEY/LEGEND explaining your symbols and colours.",
                "Which region(s) have the MOST natural resources? Which have the fewest?",
                "Explain how the uneven distribution of resources affects: (a) migration patterns, (b) regional inequality, (c) government revenue allocation.",
            ],
            "key_points": [
                "Ghana has 16 administrative regions since the 2019 referendum.",
                "The 'resource curse' theory: having natural resources doesn't always lead to development.",
                "The Minerals and Mining Act (Act 703, 2006) governs how minerals are extracted.",
                "Revenue from natural resources is shared through the Minerals Development Fund.",
                "Environmental degradation from mining ('galamsey') threatens water bodies and farmland.",
            ],
            "tasks": [
                "Draw and colour a Natural Resources Map of Ghana showing at least 5 resources across 10+ regions.",
                "Pie Chart: Create a pie chart showing what percentage of Ghana's export revenue comes from gold, cocoa, oil, and other sources.",
                "Research: What is the 'galamsey' problem? How does illegal mining affect communities in the Western and Ashanti Regions?",
            ],
            "resources": [
                "Ghana Statistical Service — Regional Economic Profiles",
                "Minerals Commission of Ghana — Mining sector data",
                "Cocoa Board (COCOBOD) — Annual reports",
            ],
        },
        "answer_guide": (
            "Regions with most resources: Western (gold, oil, bauxite, timber), Ashanti (gold, cocoa, bauxite), "
            "Eastern (gold, cocoa, diamonds). Regions with fewest exploited resources: Upper East, Upper West, "
            "North East — though these have agricultural resources (shea, livestock).\n\n"
            "Migration: People move south/west for mining and cocoa farming jobs, creating rural depopulation in the north.\n"
            "Inequality: Resource-rich regions have more economic activity but also more environmental damage.\n"
            "Revenue: The government redistributes mineral royalties through the Minerals Development Fund, "
            "but critics say the formula doesn't adequately compensate host communities."
        ),
    },

    # ── 5. Historical Timeline ────────────────────────────────────────────
    {
        "title": "Ghana's Journey to Independence — Timeline Activity",
        "activity_type": "timeline",
        "level": "b8",
        "strand": "governance",
        "topic": "Events leading to Ghana's independence in 1957",
        "scenario_text": (
            "Ghana became the first sub-Saharan African country to gain independence from colonial rule "
            "on 6th March 1957. The road to independence was long and involved many key events, "
            "organisations, and individuals. Understanding this timeline helps us appreciate the "
            "sacrifices made for our freedom."
        ),
        "content": {
            "questions": [
                "Arrange the following events in chronological order (earliest first): Formation of UGCC, 1948 Riots, Positive Action, Independence Day, Big Six arrest.",
                "Who were the 'Big Six' and why were they arrested?",
                "What was the difference between the UGCC's approach and the CPP's approach to independence?",
                "Why is 6th March celebrated as Independence Day and not another date?",
                "Write a paragraph explaining why Ghana's independence was significant for the rest of Africa.",
            ],
            "key_points": [
                "1874: Gold Coast becomes a British Crown Colony.",
                "1897: Aborigines' Rights Protection Society (ARPS) formed — first anti-colonial organisation.",
                "1947: United Gold Coast Convention (UGCC) founded by J.B. Danquah. Kwame Nkrumah invited as General Secretary.",
                "28 Feb 1948: Ex-servicemen's march/Christiansborg crossroads shooting → 1948 Accra Riots.",
                "March 1948: 'Big Six' (Nkrumah, Danquah, Obetsebi-Lamptey, Ofori-Atta, Akufo-Addo, Ako Adjei) arrested.",
                "1949: Nkrumah breaks from UGCC and forms the Convention People's Party (CPP). Slogan: 'Self-Government NOW!'",
                "January 1950: 'Positive Action' campaign — nationwide strikes and boycotts. Nkrumah imprisoned.",
                "1951: CPP wins general election. Nkrumah released from prison and becomes 'Leader of Government Business.'",
                "1954: CPP wins second election; full internal self-government granted.",
                "1956: UN-supervised plebiscite in British Togoland — votes to join Gold Coast.",
                "6 March 1957: Ghana becomes independent. Nkrumah declares: 'At long last, the battle has ended!'",
                "1960: Ghana becomes a Republic with Nkrumah as first President.",
            ],
            "tasks": [
                "Create a colourful illustrated timeline from 1874 to 1960 showing at least 10 key events. Use drawings, symbols, or images.",
                "Profile ONE of the Big Six — write a 150-word biography including their role in independence.",
                "Comparison: How was Ghana's path to independence similar to or different from that of Nigeria (1960) or Kenya (1963)?",
            ],
        },
        "answer_guide": (
            "Correct order: UGCC formation (1947), 1948 Riots (Feb 1948), Big Six arrest (March 1948), "
            "CPP formation (1949), Positive Action (Jan 1950), Independence Day (6 March 1957).\n\n"
            "Big Six: J.B. Danquah, Kwame Nkrumah, Emmanuel Obetsebi-Lamptey, Edward Akufo-Addo, "
            "William Ofori-Atta, Ebenezer Ako Adjei. Arrested after 1948 riots as suspected instigators.\n\n"
            "UGCC wanted gradual, constitutional self-government ('in the shortest possible time'). "
            "CPP demanded immediate self-government ('Self-Government NOW!') through mass action.\n\n"
            "Ghana's independence inspired Pan-African movements. Nkrumah's famous declaration: "
            "'The independence of Ghana is meaningless unless it is linked up with the total liberation "
            "of Africa' became a rallying cry for decolonisation across the continent."
        ),
    },

    # ── 6. Research Project ───────────────────────────────────────────────
    {
        "title": "Water, Sanitation & Hygiene (WASH) in Your Community",
        "activity_type": "research",
        "level": "b9",
        "strand": "environment",
        "topic": "Access to clean water and sanitation",
        "scenario_text": (
            "The United Nations Sustainable Development Goal 6 aims to 'ensure availability and "
            "sustainable management of water and sanitation for all' by 2030. In Ghana, while progress "
            "has been made, many communities — especially in rural areas — still lack access to clean "
            "water and improved sanitation facilities. Your task is to investigate the WASH situation "
            "in your own community."
        ),
        "content": {
            "questions": [
                "What are the main sources of water in your community? (borehole, pipe-borne, river, well, sachet water)",
                "Does your school have clean drinking water and functioning toilets? Describe their condition.",
                "Interview 5 community members: What is their biggest challenge related to water or sanitation?",
                "Research: What waterborne diseases are common in Ghana? How are they linked to poor sanitation?",
                "Create an action plan: What can your school/community do to improve WASH in the next 6 months?",
            ],
            "key_points": [
                "SDG 6: Clean Water and Sanitation — targets include universal access by 2030.",
                "Ghana Water Company Limited (GWCL) provides pipe-borne water; Community Water and Sanitation Agency (CWSA) serves rural areas.",
                "Common waterborne diseases: cholera, typhoid, diarrhoea, guinea worm (eradicated 2015), bilharzia.",
                "Open defecation remains a challenge in some regions despite the 'Toilet for All' campaign.",
                "Handwashing with soap prevents 40% of diarrhoeal diseases according to WHO.",
            ],
            "tasks": [
                "Field Survey: Visit 3 water sources in your community. Photograph them and rate their cleanliness (1-5).",
                "Data Collection: Create a simple questionnaire and survey 10 households about their water and sanitation access.",
                "Poster Campaign: Design an A3 poster promoting handwashing and proper waste disposal for your school or community.",
                "Report: Write a 2-page research report with your findings, data tables, and recommendations.",
            ],
            "resources": [
                "Ghana Statistical Service — WASH statistics",
                "Community Water and Sanitation Agency (CWSA) — Annual reports",
                "UNICEF Ghana — Water, Sanitation and Hygiene programme",
                "WHO/UNICEF Joint Monitoring Programme (washdata.org)",
            ],
            "rubric": {
                "Research Depth (10)": "Multiple sources consulted, primary data collected, facts verified",
                "Data Presentation (10)": "Clear tables/charts, interview quotes, photographs labelled",
                "Analysis (10)": "Identifies problems, explains causes, compares with national standards",
                "Recommendations (5)": "Practical, specific, achievable within 6 months",
                "Presentation (5)": "Well-organised, proper English, neat and clear formatting",
            },
        },
        "answer_guide": (
            "Expect findings to vary by community. Strong responses will include:\n"
            "- Primary data from interviews and field observation\n"
            "- Comparison of local situation to national SDG 6 targets\n"
            "- Specific, actionable recommendations (e.g., 'Install 2 handwashing stations at school entrances')\n"
            "- Evidence of critical thinking about root causes (funding gaps, maintenance failures, behavioural factors)\n\n"
            "National context: About 87% of Ghanaians have access to improved water sources, "
            "but only 21% have access to safely managed sanitation (WHO/UNICEF 2021)."
        ),
    },

    # ── 7. National Values Education ──────────────────────────────────────
    {
        "title": "The National Pledge & What It Means Today",
        "activity_type": "values",
        "level": "b7",
        "strand": "citizenship",
        "topic": "National identity, patriotism, and civic duty",
        "scenario_text": (
            "Every morning in Ghanaian schools, students recite:\n\n"
            "'I promise on my honour to be faithful and loyal to Ghana my motherland. "
            "I pledge myself to the service of Ghana with all my strength and with all my heart. "
            "I promise to hold in high esteem our heritage won for us through the blood and toil of "
            "our fathers; and I pledge myself in all things to uphold and defend the good name of Ghana. "
            "So help me God.'\n\n"
            "But how often do we stop to think about what each line actually means and how we can "
            "live by these words every day?"
        ),
        "content": {
            "questions": [
                "Write the National Pledge from memory. Check your accuracy — how many words did you get right?",
                "What does 'faithful and loyal to Ghana my motherland' mean in everyday life? Give TWO examples.",
                "The pledge mentions 'heritage won for us through the blood and toil of our fathers.' What specific sacrifices is this referring to?",
                "How can a student your age 'uphold and defend the good name of Ghana'?",
                "Do you think the National Pledge is still relevant today? Why or why not?",
            ],
            "key_points": [
                "The National Pledge was introduced to instil patriotism and civic consciousness in young Ghanaians.",
                "Key values: faithfulness, loyalty, service, respect for heritage, defending national honour.",
                "'Heritage won through blood and toil' refers to the independence struggle and sacrifices of the Big Six, veterans, and activists.",
                "Patriotism is not just about words — it includes paying taxes, obeying laws, voting, and contributing to community development.",
                "Ghana's national symbols include the Flag (red, gold, green + black star), Coat of Arms, and National Anthem.",
            ],
            "tasks": [
                "Break the pledge into individual phrases. For each phrase, write what it means AND give a real-life example of how you can live it.",
                "Design a poster showing 5 ways a student can be a patriotic citizen at school and in their community.",
                "Group Presentation: Each group takes one national symbol (flag, coat of arms, anthem) and explains its meaning and history to the class.",
                "Personal Pledge: Write your own personal pledge (5-7 lines) about what kind of citizen you want to be.",
            ],
        },
        "answer_guide": (
            "Faithful and loyal: Examples include speaking well of Ghana to visitors, participating in "
            "national events, not engaging in activities that damage Ghana's reputation, buying made-in-Ghana products.\n\n"
            "'Blood and toil of our fathers': 1948 Riots, Big Six detention, Positive Action campaign, "
            "the ex-servicemen who marched on Christiansborg Castle, centuries of resistance to colonialism.\n\n"
            "Students can uphold Ghana's name by: representing their school/country well in competitions, "
            "being honest, keeping their environment clean, respecting national symbols, standing up "
            "against corruption and injustice, and being good ambassadors abroad."
        ),
    },

    # ── 8. Case Study — Culture & Identity ────────────────────────────────
    {
        "title": "The Homowo Festival — Culture, Agriculture & Community",
        "activity_type": "case_study",
        "level": "b8",
        "strand": "culture",
        "topic": "Ghanaian festivals and their socio-economic significance",
        "scenario_text": (
            "The Homowo festival is celebrated annually by the Ga people of the Greater Accra Region. "
            "The name means 'hooting at hunger' (homo = hunger, wɔ = hoot at), and it commemorates a "
            "great famine that was eventually overcome through a bountiful harvest.\n\n"
            "Preparations begin in May with the planting of millet. During the 'quiet period' before "
            "the festival, drumming and noisemaking are traditionally banned in Ga communities. The "
            "festival itself takes place in August/September and features the sprinkling of 'kpokpoi' "
            "(a traditional dish of palm nut soup and corn meal) on the ground to honour ancestors, "
            "followed by feasting, drumming, and dancing.\n\n"
            "Homowo brings together Ga people from across Ghana and the diaspora, strengthens family "
            "bonds, and provides an economic boost to local businesses through tourism and celebration."
        ),
        "content": {
            "questions": [
                "What does the word 'Homowo' mean, and what event does the festival commemorate?",
                "Explain the significance of sprinkling kpokpoi during the festival.",
                "How does the festival contribute to: (a) cultural identity, (b) the local economy, (c) family unity?",
                "Compare Homowo to ONE other Ghanaian festival (e.g., Aboakyir, Bakatue, Damba, Adae Kese). What do they have in common?",
                "Some people argue that traditional festivals are outdated. Do you agree or disagree? Give reasons.",
            ],
            "key_points": [
                "Ghana has over 70 ethnic groups, each with unique festivals tied to history, agriculture, or religion.",
                "Festivals serve multiple functions: cultural preservation, conflict resolution, economic activity, and community bonding.",
                "The ban on drumming during the quiet period shows respect for the spiritual preparation before the harvest.",
                "Tourism revenue from festivals contributes to local development.",
                "The National Commission on Culture promotes and preserves Ghana's intangible cultural heritage.",
            ],
            "tasks": [
                "Research and Present: Choose a festival from a different region and present it to the class using visuals.",
                "Creative Writing: Write a diary entry as a Ga teenager experiencing Homowo for the first time.",
                "Comparison Table: Create a table comparing 4 Ghanaian festivals (name, ethnic group, region, time of year, main activity, significance).",
            ],
        },
        "answer_guide": (
            "Homowo means 'hooting at hunger' — commemorates the end of a devastating famine through "
            "a successful harvest.\n\n"
            "Sprinkling kpokpoi: Libation and offering to ancestors, asking for their blessings on the "
            "community and future harvests. Connects the living with the dead.\n\n"
            "Cultural identity: Reinforces Ga traditions, language, and customs. Economy: boosts "
            "hospitality, food vendors, transport, handicrafts. Family unity: dispersed family members "
            "return home, strengthening bonds.\n\n"
            "Common features across Ghanaian festivals: involve traditional food, ancestral reverence, "
            "community gathering, music/dance, and often have an agricultural connection."
        ),
    },

    # ── 9. Debate — Globalism ─────────────────────────────────────────────
    {
        "title": "Is Social Media Uniting or Dividing Ghana?",
        "activity_type": "debate",
        "level": "shs1",
        "strand": "globalism",
        "topic": "Impact of social media on Ghanaian society",
        "scenario_text": (
            "Ghana has over 11 million social media users as of 2024, with Facebook, WhatsApp, "
            "TikTok, X (formerly Twitter), and Instagram being the most popular platforms. Social "
            "media has enabled Ghanaians to connect globally, grow businesses, access information, "
            "and participate in democratic discourse.\n\n"
            "However, concerns have grown about the spread of misinformation, cyberbullying, ethnic "
            "tensions inflamed by online tribalism, privacy violations, and the impact on students' "
            "academic performance. During election periods, fake news on social media has been blamed "
            "for increasing political polarisation.\n\n"
            "The Cybersecurity Act (Act 1038, 2020) and the Electronic Communications Act provide "
            "some legal framework, but enforcement remains a challenge."
        ),
        "content": {
            "questions": [
                "List THREE positive impacts of social media on Ghanaian society.",
                "List THREE negative impacts of social media on Ghanaian society.",
                "What is 'misinformation' and how can you verify information before sharing it?",
                "Should the government regulate social media content? What are the arguments for and against?",
                "How can young Ghanaians use social media responsibly? Create a '5 Rules for Digital Citizenship' poster.",
            ],
            "key_points": [
                "Digital literacy includes the ability to find, evaluate, and communicate information online.",
                "The Cybersecurity Act (Act 1038, 2020) criminalises cyber fraud, identity theft, and online harassment.",
                "Freedom of expression (Article 21, 1992 Constitution) must be balanced with responsibility.",
                "Verified sources include official government websites (.gov.gh), established media houses, and peer-reviewed research.",
                "Online tribalism: using social media to denigrate other ethnic groups damages national unity.",
            ],
            "tasks": [
                "Debate: 'Social media does more harm than good for Ghanaian youth.' Two teams, 5 minutes each.",
                "Fact-Check Exercise: The teacher shares 5 social media posts. Students determine which are true, false, or misleading.",
                "Campaign: Create a short video or poster promoting responsible social media use for your school.",
            ],
        },
        "answer_guide": (
            "Positive: Business growth (online shops, mobile money integration), access to global information, "
            "democratic participation (#FixTheCountry movement), cultural promotion (Ghanaian content creators), "
            "emergency communication.\n\n"
            "Negative: Misinformation/fake news, cyberbullying, privacy breaches, academic distraction, "
            "online ethnic tensions, scams and fraud.\n\n"
            "Verification tips: Check the source, look for the date, read beyond headlines, "
            "cross-reference with trusted outlets (GNA, Daily Graphic), check if fact-checkers "
            "(Africa Check, PesaCheck) have reviewed the claim."
        ),
    },

    # ── 10. Scenario — Economics & Development ────────────────────────────
    {
        "title": "Starting a School Business — Financial Literacy",
        "activity_type": "scenario",
        "level": "b9",
        "strand": "economics",
        "topic": "Entrepreneurship, budgeting, and financial literacy",
        "scenario_text": (
            "Your school's Social Studies Club has been given GHS 500 as seed money to start a small "
            "business during the school term. The business must:\n"
            "• Be legal and school-appropriate\n"
            "• Generate profit within 6 weeks\n"
            "• Involve at least 5 club members\n"
            "• Benefit the school community in some way\n\n"
            "Popular options include: selling healthy snacks, a stationery shop, a printing/copying "
            "service, or an after-school tutoring programme. Your club must create a business plan, "
            "budget, and keep proper financial records."
        ),
        "content": {
            "questions": [
                "If your club sells meat pies for GHS 5 each and each pie costs GHS 3 to make, how many pies must you sell to recover your GHS 500 capital?",
                "What is the difference between REVENUE, PROFIT, and LOSS? Give an example of each using your school business.",
                "Why is it important to keep financial records? What could go wrong if you don't?",
                "List 3 risks your business might face and how you would manage each one.",
                "How would you divide the profit fairly among 5 members who contributed different amounts of time?",
            ],
            "key_points": [
                "Entrepreneurship: the ability to identify opportunities and create value through initiative.",
                "Budget = planned income minus planned expenses. Always plan for unexpected costs.",
                "Profit = Revenue (total sales) - Cost of Goods Sold - Operating Expenses.",
                "Record-keeping: Use a simple cashbook with columns for Date, Description, Income, Expense, Balance.",
                "Risk management: identify potential problems and plan solutions BEFORE they happen.",
                "Ghana's Small and Medium Enterprise (SME) sector employs over 80% of the workforce.",
            ],
            "tasks": [
                "Business Plan: Write a 1-page plan including: business name, product/service, target customers, pricing, startup costs, and projected profit.",
                "Budget Template: Create a budget spreadsheet for 6 weeks showing expected income and expenses per week.",
                "Role Assignment: Divide roles — Manager, Treasurer, Marketing, Production, Quality Control. Write a job description for each.",
                "Profit Sharing Agreement: Write a simple agreement that all members sign, stating how profits will be divided.",
            ],
        },
        "answer_guide": (
            "Pie calculation: Profit per pie = GHS 5 - GHS 3 = GHS 2. To recover GHS 500: 500 ÷ 2 = 250 pies.\n\n"
            "Revenue: total money received from sales (e.g., sold 100 pies × GHS 5 = GHS 500 revenue).\n"
            "Profit: revenue minus all costs (e.g., GHS 500 revenue - GHS 300 costs = GHS 200 profit).\n"
            "Loss: when costs exceed revenue (e.g., GHS 500 revenue - GHS 600 costs = GHS 100 loss).\n\n"
            "Profit division options: equal sharing, time-based (hours worked), role-based (higher responsibility = higher share), "
            "or hybrid. The key is that the agreement is transparent and agreed in advance."
        ),
    },
]

created = 0
for a in ACTIVITIES:
    obj, was_created = CitizenEdActivity.objects.get_or_create(
        profile=profile,
        title=a["title"],
        defaults=a,
    )
    if was_created:
        created += 1
        print(f"  + {obj.title}")
    else:
        print(f"  = {obj.title} (exists)")

total = CitizenEdActivity.objects.filter(profile=profile).count()
print(f"\nCreated {created} new activities. Total for {profile}: {total}")
