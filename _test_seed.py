"""Quick validation of seed_content.py imports and data."""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from individual_users.seed_content import (
    _FREE_ADDONS, _COMPUTHINK_SAMPLES, _LITERACY_SAMPLES,
    _CITIZEN_ED_SAMPLES, _TVET_SAMPLES, _LETTER_SAMPLES,
    _REPORT_CARD_SET, _PAPER_MARKER_SAMPLE, _TOOL_SEEDERS,
    seed_tool_content, seed_starter_content,
)

print(f"FREE_ADDONS: {len(_FREE_ADDONS)} tools")
print(f"TOOL_SEEDERS: {len(_TOOL_SEEDERS)} seeders")
print(f"CompuThink samples: {len(_COMPUTHINK_SAMPLES)}")
print(f"Literacy samples: {len(_LITERACY_SAMPLES)}")
print(f"CitizenEd samples: {len(_CITIZEN_ED_SAMPLES)}")
print(f"TVET samples: {len(_TVET_SAMPLES)}")
print(f"Letter samples: {len(_LETTER_SAMPLES)}")
print(f"Report card entries: {len(_REPORT_CARD_SET['entries'])}")
print(f"Paper marker students: {len(_PAPER_MARKER_SAMPLE['students'])}")
print("All imports and data validated OK!")
