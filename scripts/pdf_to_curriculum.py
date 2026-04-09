#!/usr/bin/env python3
"""
Extract GES/NaCCA curriculum data from official PDF documents and convert
to the JSON seed format used by `import_curriculum`.

Each GES/NaCCA PDF contains B7, B8, and B9 curriculum for one subject.
This script splits by grade boundaries and outputs one JSON per grade.

Usage:
    # Preview text to check extraction quality
    python scripts/pdf_to_curriculum.py preview pdfs/MATHEMATICS.pdf --pages 32-35

    # Convert a single PDF → outputs 3 JSON files (b7_xxx, b8_xxx, b9_xxx)
    python scripts/pdf_to_curriculum.py convert pdfs/MATHEMATICS.pdf

    # Batch convert all PDFs in a folder
    python scripts/pdf_to_curriculum.py batch pdfs/ --output-dir curriculum/data/
"""
import argparse
import json
import os
import re
import sys
from collections import OrderedDict

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber is required. Install with: pip install pdfplumber")
    sys.exit(1)


# ─── Subject detection map ──────────────────────────────────────────────────

SUBJECT_MAP = [
    (r'MATHEMATICS',                  'Mathematics',                   'MATH'),
    (r'SCIENCE\b',                    'Science',                       'SCI'),
    (r'ENGLISH\s*(?:LANGUAGE)?',      'English Language',              'ENG'),
    (r'SOCIAL\s*STUDIES',             'Social Studies',                'SS'),
    (r'COMPUTING',                    'Computing',                     'ICT'),
    (r'ICT|INFORMATION.*COMMUNICATION', 'Computing',                  'ICT'),
    (r'FRENCH',                       'French',                        'FRE'),
    (r'GHANAIAN\s*LANGUAGE',          'Ghanaian Language',             'GHL'),
    (r'RELIGIOUS.*MORAL',             'Religious and Moral Education', 'RME'),
    (r'CREATIVE\s*ARTS',              'Creative Arts and Design',      'CAD'),
    (r'CAREER\s*TECH',               'Career Technology',             'CT'),
]

GRADE_INFO = {
    'B7': 'Basic 7 (JHS 1)',
    'B8': 'Basic 8 (JHS 2)',
    'B9': 'Basic 9 (JHS 3)',
}

# Matches content-standard codes:  B7.1.1.1  B8.2.3.1  B7 1.1.1  B 7.1.1.1
# (exactly 4 number groups — the separator after B# can be dot, space, or space+dot)
CS_CODE_RE = re.compile(r'(B\s?[789])[\s.]+(\d+)[\s.]+(\d+)[\s.]+(\d+)')
# Matches indicator codes:  B7.1.1.1.1  B7 1.1.1.1  B 7.1.1.1.3  (exactly 5 groups)
IND_CODE_RE = re.compile(r'(B\s?[789])[\s.]+(\d+)[\s.]+(\d+)[\s.]+(\d+)[\s.]+(\d+)')

# Core-competency abbreviation noise to strip
CC_NOISE_RE = re.compile(
    r'\b(?:Critical Thinking|Problem Solving|Communication and Collaboration|'
    r'Personal Development|Leadership|Creativity and Innovation|Digital Literacy|'
    r'Cultural Identity|Global Citizenship|'
    r'CP|CC|PL|CI|DL|CG)\b[,.\s()]*',
    re.IGNORECASE,
)

# ─── PDF helpers ─────────────────────────────────────────────────────────────

def _open_pdf(path):
    return pdfplumber.open(path)


def detect_subject(text):
    """Auto-detect subject name and code from PDF front-matter text."""
    for pattern, name, code in SUBJECT_MAP:
        if re.search(pattern, text, re.IGNORECASE):
            return name, code
    return None, ''


def find_grade_boundaries(pdf):
    """
    Scan every page and return {grade_code: (start_page_idx, end_page_idx)}.
    GES PDFs have near-empty pages with "BASIC 7", "Basic Year 8", etc.
    """
    n = len(pdf.pages)
    boundary_pages = {}  # grade_code -> 0-based page index

    for i, page in enumerate(pdf.pages):
        text = (page.extract_text() or '').strip()
        upper = text.upper()
        # Must be a short divider page (< 100 chars) or start of content section
        is_boundary = len(text) < 100
        if not is_boundary:
            # Also check first line only
            first_line = text.split('\n')[0].strip().upper()
            is_boundary = len(first_line) < 60 and any(
                g in first_line for g in ['BASIC 7', 'BASIC 8', 'BASIC 9',
                                          'BASIC YEAR 7', 'BASIC YEAR 8', 'BASIC YEAR 9']
            )

        if is_boundary:
            for gcode, patterns in [
                ('B7', ['BASIC 7', 'BASIC YEAR 7', 'JHS 1', 'JHS1']),
                ('B8', ['BASIC 8', 'BASIC YEAR 8', 'JHS 2', 'JHS2']),
                ('B9', ['BASIC 9', 'BASIC YEAR 9', 'JHS 3', 'JHS3']),
            ]:
                if any(p in upper for p in patterns):
                    if gcode not in boundary_pages:
                        boundary_pages[gcode] = i
                    break

    # Convert to ranges
    grade_ranges = {}
    codes_sorted = sorted(boundary_pages.keys())

    for idx, code in enumerate(codes_sorted):
        start = boundary_pages[code]
        if idx + 1 < len(codes_sorted):
            end = boundary_pages[codes_sorted[idx + 1]]
        else:
            end = n
        grade_ranges[code] = (start, end)

    return grade_ranges


def extract_pages_text(pdf, start, end):
    """Extract text from a range of pages (0-based, exclusive end)."""
    pages = []
    for i in range(start, end):
        text = pdf.pages[i].extract_text()
        if text:
            pages.append((i + 1, text))
    return pages


def extract_cs_from_tables(pdf, start, end, grade_code):
    """
    Use pdfplumber table extraction to get clean CS statements from column 0.
    The GES PDFs use a 3-column table: [Content Standard | Indicators | Core Competencies].
    Table extraction cleanly separates columns, giving us full CS statements
    without the noise from indicator/CC columns that text extraction mixes in.
    Returns dict: {cs_code: statement_text}
    """
    cs_statements = {}
    for i in range(start, end):
        page = pdf.pages[i]
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                if not row or not row[0]:
                    continue
                cell = row[0].replace('\n', ' ').strip()
                m = CS_CODE_RE.search(cell)
                if m:
                    gc = m.group(1).replace(' ', '')
                    if gc != grade_code:
                        continue
                    code = _normalise_code(m)
                    stmt = cell[m.end():].strip()
                    stmt = re.sub(r'^[\s:.]+', '', stmt)
                    stmt = _clean_statement(stmt)
                    if stmt and len(stmt) > len(cs_statements.get(code, '')):
                        cs_statements[code] = stmt
    return cs_statements


# ─── Core parser ─────────────────────────────────────────────────────────────

def _normalise_code(m):
    """Rebuild a code string from a regex match, removing internal spaces."""
    parts = [g.replace(' ', '') for g in m.groups()]
    return '.'.join(parts)


def _clean_statement(text):
    """Strip core-competency noise and normalise whitespace."""
    text = CC_NOISE_RE.sub(' ', text)
    # Strip PDF continuation artifacts
    text = re.sub(r'\(?\s*CONTINUED\s*\)?\s*:?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r"\bCONT['']D\b\s*:?\s*", '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove trailing punctuation artifacts
    text = re.sub(r'[\s,;:]+$', '', text)
    return text


def _extract_exemplars(lines):
    """
    Given a list of lines that belong to an indicator's exemplar section,
    return a list of cleaned exemplar strings.
    """
    exemplars = []
    current = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                exemplars.append(' '.join(current))
                current = []
            continue

        # Does this line start a new exemplar item?
        # Patterns: "E.g.1.", "E.g. 2.", "• ", "i. ", "1. ", "- "
        new_item = re.match(
            r'^(?:E\.g\.?\s*\d*\.?\s*|[•\-\*]\s*|(?:\d+|[ivx]+|[a-z])[\.\)]\s*)',
            stripped, re.IGNORECASE,
        )
        if new_item:
            if current:
                exemplars.append(' '.join(current))
                current = []
            rest = stripped[new_item.end():].strip()
            if rest:
                current.append(rest)
        else:
            current.append(stripped)

    if current:
        exemplars.append(' '.join(current))

    # Clean up and filter
    cleaned = []
    for e in exemplars:
        e = _clean_statement(e)
        if e and len(e) > 8:
            cleaned.append(e)
    return cleaned


def parse_grade_text(pages_text, grade_code):
    """
    Parse all text for a single grade section into our curriculum structure.
    Returns list of strand dicts.
    """
    strands = []
    current_strand = None
    current_sub_strand = None
    current_cs = None
    current_indicator = None

    # Collect all lines
    all_lines = []
    for _, text in pages_text:
        all_lines.extend(text.split('\n'))

    # State: once we see an indicator code, subsequent lines until the next
    # code or structural header are either statement continuation or exemplars.
    IN_NONE = 0
    IN_CS_STATEMENT = 1
    IN_IND_STATEMENT = 2
    IN_EXEMPLARS = 3
    state = IN_NONE
    buffer_lines = []

    def _flush_exemplars():
        nonlocal buffer_lines
        if current_indicator is not None and buffer_lines:
            current_indicator['exemplars'] = _extract_exemplars(buffer_lines)
        buffer_lines = []

    def _flush_ind_statement():
        nonlocal buffer_lines
        if current_indicator is not None and buffer_lines:
            stmt = ' '.join(l.strip() for l in buffer_lines if l.strip())
            current_indicator['statement'] = _clean_statement(stmt)
        buffer_lines = []

    def _flush_cs_statement():
        nonlocal buffer_lines
        if current_cs is not None and buffer_lines:
            stmt = ' '.join(l.strip() for l in buffer_lines if l.strip())
            current_cs['statement'] = _clean_statement(stmt)
        buffer_lines = []

    for line in all_lines:
        stripped = line.strip()
        if not stripped:
            continue

        upper = stripped.upper()

        # ── Skip known noise ──
        if upper.startswith('CONTENT STANDARD') or upper.startswith('INDICATORS AND'):
            continue
        if upper.startswith('© NACCA') or upper.startswith('CORE COMPETEN'):
            continue
        if re.match(r'^\d+$', stripped):  # page numbers
            continue

        # ── STRAND header ──
        strand_m = re.match(
            r'STRAND\s*\d*\s*[:\.]\s*(.+)', stripped, re.IGNORECASE
        )
        if strand_m:
            _flush_exemplars()
            name = strand_m.group(1).strip().rstrip(':').strip()
            name = re.sub(r'\s+', ' ', name)
            name = name.title() if name.isupper() else name
            # Avoid duplicate strand from table headers that repeat
            if not current_strand or current_strand['name'] != name:
                current_strand = {'name': name, 'sub_strands': []}
                strands.append(current_strand)
            current_sub_strand = None
            current_cs = None
            current_indicator = None
            state = IN_NONE
            continue

        # ── SUB-STRAND header ──
        ss_m = re.match(
            r'SUB[\s-]*STRAND\s*\d*\s*[:\.]\s*(.+)', stripped, re.IGNORECASE
        )
        if ss_m and current_strand is not None:
            _flush_exemplars()
            name = ss_m.group(1).strip().rstrip(':').strip()
            name = re.sub(r'\s+', ' ', name)
            name = name.title() if name.isupper() else name
            # Reuse existing sub-strand if name already present (PDF repeats across pages)
            existing = next((ss for ss in current_strand['sub_strands'] if ss['name'] == name), None)
            if existing:
                current_sub_strand = existing
            else:
                current_sub_strand = {'name': name, 'content_standards': []}
                current_strand['sub_strands'].append(current_sub_strand)
            current_cs = None
            current_indicator = None
            state = IN_NONE
            continue

        # ── Indicator code (check BEFORE content-standard, since ind is longer) ──
        ind_m = IND_CODE_RE.search(stripped)
        if ind_m:
            gc = ind_m.group(1).replace(' ', '')
            if gc != grade_code:
                continue  # belongs to different grade (noise from multi-grade text)

            # Flush previous
            if state == IN_EXEMPLARS:
                _flush_exemplars()
            elif state == IN_IND_STATEMENT:
                _flush_ind_statement()
            elif state == IN_CS_STATEMENT:
                _flush_cs_statement()

            code = _normalise_code(ind_m)
            # Ensure parent CS exists
            cs_code = '.'.join(code.split('.')[:4])

            # Check if there's a CS code BEFORE the indicator on the same line
            # (tabular PDFs: "B7.1.1.1 Recognise materials... B7.1.1.1.1 Classify...")
            cs_statement_from_line = ''
            prefix = stripped[:ind_m.start()]
            cs_prefix_m = CS_CODE_RE.search(prefix)
            if cs_prefix_m:
                cs_stmt_text = prefix[cs_prefix_m.end():].strip()
                cs_stmt_text = re.sub(r'^[\s:.]+', '', cs_stmt_text)
                cs_statement_from_line = _clean_statement(cs_stmt_text)

            if current_cs is None or current_cs['code'] != cs_code:
                if current_sub_strand is None:
                    if current_strand is None:
                        current_strand = {'name': 'Uncategorised', 'sub_strands': []}
                        strands.append(current_strand)
                    # Reuse existing 'General' sub-strand if present
                    existing_ss = next((ss for ss in current_strand['sub_strands'] if ss['name'] == 'General'), None)
                    if existing_ss:
                        current_sub_strand = existing_ss
                    else:
                        current_sub_strand = {'name': 'General', 'content_standards': []}
                        current_strand['sub_strands'].append(current_sub_strand)
                # Reuse existing CS if code already present (PDF repeats across pages)
                existing = next((c for c in current_sub_strand['content_standards'] if c['code'] == cs_code), None)
                if existing:
                    current_cs = existing
                else:
                    current_cs = {'code': cs_code, 'statement': '', 'indicators': []}
                    current_sub_strand['content_standards'].append(current_cs)

            # Apply CS statement extracted from tabular line (keep longest)
            if cs_statement_from_line and len(cs_statement_from_line) > len(current_cs.get('statement', '')):
                current_cs['statement'] = cs_statement_from_line

            current_indicator = {
                'code': code,
                'statement': '',
                'term': '',
                'suggested_weeks': 1,
                'exemplars': [],
            }
            current_cs['indicators'].append(current_indicator)

            # Text after the code on same line is start of statement
            rest = stripped[ind_m.end():].strip()
            rest = re.sub(r'^[\s:.]+', '', rest)
            if rest:
                buffer_lines = [rest]
            else:
                buffer_lines = []

            state = IN_IND_STATEMENT
            continue

        # ── Content-standard code (4-part) ──
        cs_m = CS_CODE_RE.search(stripped)
        # Make sure it's not actually an indicator (5-part)
        if cs_m and not IND_CODE_RE.search(stripped):
            gc = cs_m.group(1).replace(' ', '')
            if gc != grade_code:
                continue

            if state == IN_EXEMPLARS:
                _flush_exemplars()
            elif state == IN_IND_STATEMENT:
                _flush_ind_statement()
            elif state == IN_CS_STATEMENT:
                _flush_cs_statement()

            code = _normalise_code(cs_m)

            if current_sub_strand is None:
                if current_strand is None:
                    current_strand = {'name': 'Uncategorised', 'sub_strands': []}
                    strands.append(current_strand)
                # Reuse existing 'General' sub-strand if present
                existing_ss = next((ss for ss in current_strand['sub_strands'] if ss['name'] == 'General'), None)
                if existing_ss:
                    current_sub_strand = existing_ss
                else:
                    current_sub_strand = {'name': 'General', 'content_standards': []}
                    current_strand['sub_strands'].append(current_sub_strand)

            # Reuse existing CS if code already present (PDF repeats across pages)
            existing = next((c for c in current_sub_strand['content_standards'] if c['code'] == code), None)
            if existing:
                current_cs = existing
            else:
                current_cs = {'code': code, 'statement': '', 'indicators': []}
                current_sub_strand['content_standards'].append(current_cs)
            current_indicator = None

            rest = stripped[cs_m.end():].strip()
            rest = re.sub(r'^[\s:.]+', '', rest)
            buffer_lines = [rest] if rest else []
            state = IN_CS_STATEMENT
            continue

        # ── Exemplar header transition ──
        if re.match(r'^Exemplar\(?s?\)?[\s:]*$', stripped, re.IGNORECASE):
            if state == IN_IND_STATEMENT:
                _flush_ind_statement()
            state = IN_EXEMPLARS
            buffer_lines = []
            continue

        # ── "E.g." at start of line → exemplar item ──
        if re.match(r'^E\.g\.', stripped, re.IGNORECASE):
            if state == IN_IND_STATEMENT:
                _flush_ind_statement()
                state = IN_EXEMPLARS
                buffer_lines = []
            if state != IN_EXEMPLARS:
                state = IN_EXEMPLARS
                buffer_lines = []
            buffer_lines.append(stripped)
            continue

        # ── Bullet/numbered item while expecting exemplars ──
        if state == IN_EXEMPLARS:
            buffer_lines.append(stripped)
            continue
        # ── Continuation lines for statement ──
        if state in (IN_CS_STATEMENT, IN_IND_STATEMENT):
            # Heuristic: if it looks like a bullet or "E.g." → switch to exemplars
            if re.match(r'^[•\-\*]\s+', stripped) or re.match(r'^\d+[\.\)]\s+', stripped):
                if state == IN_IND_STATEMENT:
                    _flush_ind_statement()
                elif state == IN_CS_STATEMENT:
                    _flush_cs_statement()
                state = IN_EXEMPLARS
                buffer_lines = [stripped]
                continue
            buffer_lines.append(stripped)
            continue

    # Final flush
    if state == IN_EXEMPLARS:
        _flush_exemplars()
    elif state == IN_IND_STATEMENT:
        _flush_ind_statement()
    elif state == IN_CS_STATEMENT:
        _flush_cs_statement()

    return strands


def _dedup_strands(strands):
    """
    Post-process parsed strands to merge duplicates at every level:
    - Duplicate sub-strands (same name) within a strand
    - Duplicate content standards (same code) within a sub-strand
    - Duplicate indicators (same code) within a content standard
    """
    for strand in strands:
        # Dedup sub-strands by name
        seen_ss = {}
        unique_ss = []
        for ss in strand.get('sub_strands', []):
            if ss['name'] in seen_ss:
                # Merge content_standards into existing
                seen_ss[ss['name']]['content_standards'].extend(ss['content_standards'])
            else:
                seen_ss[ss['name']] = ss
                unique_ss.append(ss)
        strand['sub_strands'] = unique_ss

        for ss in strand['sub_strands']:
            # Dedup content standards by code
            seen_cs = {}
            unique_cs = []
            for cs in ss.get('content_standards', []):
                if cs['code'] in seen_cs:
                    seen_cs[cs['code']]['indicators'].extend(cs['indicators'])
                    # Keep longer statement
                    if len(cs.get('statement', '')) > len(seen_cs[cs['code']].get('statement', '')):
                        seen_cs[cs['code']]['statement'] = cs['statement']
                else:
                    seen_cs[cs['code']] = cs
                    unique_cs.append(cs)
            ss['content_standards'] = unique_cs

            for cs in ss['content_standards']:
                # Dedup indicators by code
                seen_ind = {}
                unique_ind = []
                for ind in cs.get('indicators', []):
                    if ind['code'] in seen_ind:
                        existing = seen_ind[ind['code']]
                        existing['exemplars'].extend(ind.get('exemplars', []))
                        if len(ind.get('statement', '')) > len(existing.get('statement', '')):
                            existing['statement'] = ind['statement']
                    else:
                        seen_ind[ind['code']] = ind
                        unique_ind.append(ind)
                cs['indicators'] = unique_ind

    return strands


# ─── Assign terms by position ───────────────────────────────────────────────

def assign_terms(strands):
    """
    GES/NaCCA doesn't always mark terms explicitly in the PDF.
    Divide indicators roughly into thirds and assign terms.
    """
    # Collect all indicators in order
    all_inds = []
    for strand in strands:
        for ss in strand.get('sub_strands', []):
            for cs in ss.get('content_standards', []):
                for ind in cs.get('indicators', []):
                    all_inds.append(ind)

    if not all_inds:
        return

    # Check if any already have terms set
    has_terms = sum(1 for ind in all_inds if ind.get('term'))
    if has_terms > len(all_inds) * 0.3:
        return  # Already has terms, don't override

    n = len(all_inds)
    third = n / 3
    for i, ind in enumerate(all_inds):
        if i < third:
            ind['term'] = 'first'
        elif i < 2 * third:
            ind['term'] = 'second'
        else:
            ind['term'] = 'third'


# ─── Output builders ────────────────────────────────────────────────────────

def build_json(subject, subject_code, grade_name, grade_code, strands):
    return OrderedDict([
        ('subject', subject),
        ('subject_code', subject_code),
        ('grades', [
            OrderedDict([
                ('name', grade_name),
                ('code', grade_code),
                ('strands', strands),
            ])
        ]),
    ])


def count_stats(data):
    stats = {'strands': 0, 'sub_strands': 0, 'content_standards': 0,
             'indicators': 0, 'exemplars': 0}
    for grade in data.get('grades', []):
        for strand in grade.get('strands', []):
            stats['strands'] += 1
            for ss in strand.get('sub_strands', []):
                stats['sub_strands'] += 1
                for cs in ss.get('content_standards', []):
                    stats['content_standards'] += 1
                    for ind in cs.get('indicators', []):
                        stats['indicators'] += 1
                        stats['exemplars'] += len(ind.get('exemplars', []))
    return stats


# ─── Convert one PDF → multiple JSON files ───────────────────────────────────

def convert_pdf(pdf_path, output_dir='curriculum/data/', force=False):
    """
    Convert one GES/NaCCA multi-grade PDF into separate JSON per grade.
    Returns list of (output_path, stats_dict) for each generated file.
    """
    results = []

    with _open_pdf(pdf_path) as pdf:
        # Detect subject from first few pages
        front_text = ''
        for i in range(min(5, len(pdf.pages))):
            front_text += (pdf.pages[i].extract_text() or '') + '\n'

        subject, subject_code = detect_subject(front_text)
        if not subject:
            print(f"  ⚠  Could not auto-detect subject from {pdf_path}")
            return results

        print(f"  Subject: {subject} ({subject_code})")

        # Find grade section boundaries
        grade_ranges = find_grade_boundaries(pdf)

        if not grade_ranges:
            # Fallback: treat whole PDF as one grade, try to detect which
            print(f"  ⚠  No grade boundaries found. Treating entire PDF as one unit.")
            grade_ranges = {'B7': (0, len(pdf.pages))}

        for grade_code in sorted(grade_ranges.keys()):
            start, end = grade_ranges[grade_code]
            grade_name = GRADE_INFO.get(grade_code, grade_code)
            print(f"  {grade_code}: pages {start+1}-{end} ...", end=' ', flush=True)

            pages_text = extract_pages_text(pdf, start, end)
            if not pages_text:
                print("(no text)")
                continue

            strands = parse_grade_text(pages_text, grade_code)
            strands = _dedup_strands(strands)

            # Enrich CS statements from table extraction (clean column separation)
            cs_from_tables = extract_cs_from_tables(pdf, start, end, grade_code)
            for strand in strands:
                for ss in strand.get('sub_strands', []):
                    for cs in ss.get('content_standards', []):
                        table_stmt = cs_from_tables.get(cs['code'], '')
                        if table_stmt:
                            # Always prefer table-extracted (clean column) over text-extracted
                            cs['statement'] = table_stmt

            assign_terms(strands)

            data = build_json(subject, subject_code, grade_name, grade_code, strands)
            stats = count_stats(data)

            # Build output filename
            code_lower = subject_code.lower() if subject_code else \
                re.sub(r'[^a-z]+', '_', subject.lower()).strip('_')
            out_name = f"{grade_code.lower()}_{code_lower}.json"
            out_path = os.path.join(output_dir, out_name)

            # Safety: don't overwrite if existing has more indicators
            if not force and os.path.exists(out_path):
                with open(out_path, encoding='utf-8') as f:
                    existing = json.load(f)
                existing_stats = count_stats(existing)
                if stats['indicators'] <= existing_stats['indicators']:
                    print(f"SKIP (existing has {existing_stats['indicators']} indicators, "
                          f"extracted {stats['indicators']})")
                    continue

            os.makedirs(output_dir, exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"{stats['indicators']} indicators, {stats['exemplars']} exemplars → {out_name}")
            results.append((out_path, stats))

    return results


# ─── CLI Commands ────────────────────────────────────────────────────────────

def cmd_preview(args):
    pages_range = args.pages
    with _open_pdf(args.pdf) as pdf:
        for i, page in enumerate(pdf.pages):
            if pages_range and i not in pages_range:
                continue
            text = page.extract_text()
            if text:
                print(f"\n{'='*60}\n  PAGE {i+1}\n{'='*60}")
                print(text)

        front = ''
        for i in range(min(5, len(pdf.pages))):
            front += (pdf.pages[i].extract_text() or '') + '\n'
        subject, code = detect_subject(front)
        grades = find_grade_boundaries(pdf)
        print(f"\n{'='*60}")
        print(f"  Subject:    {subject or '?'} ({code or '?'})")
        print(f"  Grades:     {', '.join(f'{g} @ page {s+1}' for g,(s,e) in sorted(grades.items()))}")
        print(f"  Total pages: {len(pdf.pages)}")
        print(f"{'='*60}")


def cmd_tables(args):
    pages_range = args.pages
    with _open_pdf(args.pdf) as pdf:
        for i, page in enumerate(pdf.pages):
            if pages_range and i not in pages_range:
                continue
            for j, table in enumerate(page.extract_tables()):
                print(f"\n{'='*60}\n  TABLE (Page {i+1}, #{j+1})\n{'='*60}")
                for row in table:
                    print('  |  '.join(
                        (str(c)[:60] if c else '(empty)') for c in row
                    ))


def cmd_convert(args):
    print(f"Converting {args.pdf}...")
    output_dir = args.output_dir or 'curriculum/data/'
    results = convert_pdf(args.pdf, output_dir=output_dir, force=args.force)

    total_ind = sum(s['indicators'] for _, s in results)
    total_ex = sum(s['exemplars'] for _, s in results)
    print(f"\nTotal: {len(results)} files, {total_ind} indicators, {total_ex} exemplars")

    if results:
        paths = ' '.join(p for p, _ in results)
        print(f"\nImport with:\n  python manage.py import_curriculum {paths}")


def cmd_batch(args):
    pdf_dir = args.pdf_dir
    output_dir = args.output_dir or 'curriculum/data/'

    pdf_files = sorted(
        f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')
    )
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDF files in {pdf_dir}/")
    print(f"Output: {output_dir}/\n")

    grand_total = 0
    all_paths = []
    for pdf_name in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_name)
        print(f"─── {pdf_name} ───")
        try:
            results = convert_pdf(pdf_path, output_dir=output_dir, force=args.force)
            for path, stats in results:
                grand_total += stats['indicators']
                all_paths.append(path)
        except Exception as e:
            print(f"  ✗ Error: {e}")
        print()

    print(f"{'='*60}")
    print(f"  DONE: {len(all_paths)} JSON files, {grand_total} total indicators")
    print(f"{'='*60}")

    if all_paths:
        print(f"\nImport all with:")
        print(f"  python manage.py import_curriculum {' '.join(all_paths)}")


# ─── Argument Parsing ────────────────────────────────────────────────────────

def parse_page_range(s):
    pages = set()
    for part in s.split(','):
        if '-' in part:
            start, end = part.split('-', 1)
            pages.update(range(int(start) - 1, int(end)))
        else:
            pages.add(int(part) - 1)
    return pages


def main():
    parser = argparse.ArgumentParser(
        description='Extract GES/NaCCA curriculum from PDF to JSON',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/pdf_to_curriculum.py preview pdfs/MATHEMATICS.pdf --pages 32-35
  python scripts/pdf_to_curriculum.py convert pdfs/MATHEMATICS.pdf
  python scripts/pdf_to_curriculum.py batch pdfs/ --output-dir curriculum/data/
        """,
    )
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('preview', help='Preview extracted text from PDF')
    p.add_argument('pdf')
    p.add_argument('--pages', type=parse_page_range, default=None)

    p = sub.add_parser('tables', help='Preview extracted tables from PDF')
    p.add_argument('pdf')
    p.add_argument('--pages', type=parse_page_range, default=None)

    p = sub.add_parser('convert', help='Convert one PDF to curriculum JSON (outputs per grade)')
    p.add_argument('pdf')
    p.add_argument('--output-dir', default='curriculum/data/')
    p.add_argument('--force', action='store_true', help='Overwrite existing files')

    p = sub.add_parser('batch', help='Batch convert all PDFs in a directory')
    p.add_argument('pdf_dir')
    p.add_argument('--output-dir', default='curriculum/data/')
    p.add_argument('--force', action='store_true', help='Overwrite existing files')

    args = parser.parse_args()
    {'preview': cmd_preview, 'tables': cmd_tables,
     'convert': cmd_convert, 'batch': cmd_batch}[args.command](args)


if __name__ == '__main__':
    main()
