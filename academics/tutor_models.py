"""
Track AI Tutor usage and sessions
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import qrcode
from datetime import datetime
from reportlab.lib.pagesizes import letter, A6
from reportlab.lib.units import mm, inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor


class TutorSession(models.Model):
    """Track AI tutor chat sessions"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='tutor_sessions')
    subject = models.ForeignKey('academics.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    message_count = models.IntegerField(default=0)
    topics_discussed = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.started_at.date()}"


class TutorMessage(models.Model):
    """Individual messages in tutor sessions"""
    session = models.ForeignKey(TutorSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=[('user', 'Student'), ('assistant', 'AI Tutor')])
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class PracticeQuestionSet(models.Model):
    """Generated practice question sets"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='practice_sets')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE)
    topic = models.CharField(max_length=200)
    difficulty = models.CharField(
        max_length=20, 
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')],
        default='medium'
    )
    
    questions = models.JSONField(help_text="AI-generated questions and answers")
    
    generated_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True, help_text="Percentage score")
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.subject.name}: {self.topic}"


# ID Card Generation Functions
# ==============================
# Three template styles: classic, modern, elegant
# Each generates both student and teacher cards.

def _get_school_info():
    """Get school info for ID card branding."""
    try:
        from academics.models import SchoolInfo
        info = SchoolInfo.objects.first()
        if info:
            return {
                'name': info.name,
                'address': info.address,
                'phone': info.phone,
                'email': info.email,
                'motto': info.motto,
                'template': info.id_card_template,
                'logo': info.logo if info.logo else None,
            }
    except Exception:
        pass
    return {
        'name': 'School Name',
        'address': 'School Address',
        'phone': 'Phone',
        'email': 'info@school.edu',
        'motto': 'Education for All',
        'template': 'classic',
        'logo': None,
    }


def _load_fonts():
    """Load fonts with graceful fallback."""
    fonts = {}
    try:
        fonts['title'] = ImageFont.truetype("arial.ttf", 26)
        fonts['name'] = ImageFont.truetype("arialbd.ttf", 22)
        fonts['label'] = ImageFont.truetype("arial.ttf", 13)
        fonts['value'] = ImageFont.truetype("arialbd.ttf", 15)
        fonts['small'] = ImageFont.truetype("arial.ttf", 11)
        fonts['header'] = ImageFont.truetype("arialbd.ttf", 28)
        fonts['motto'] = ImageFont.truetype("ariali.ttf", 12)
    except Exception:
        default = ImageFont.load_default()
        fonts = {k: default for k in ['title', 'name', 'label', 'value', 'small', 'header', 'motto']}
    return fonts


def _make_qr(data, size=110):
    """Generate QR code image."""
    qr = qrcode.QRCode(version=1, box_size=5, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    return qr_img.resize((size, size), Image.Resampling.LANCZOS)


def _paste_profile(card, user, x, y, size, border_color=(255, 255, 255), border_width=4):
    """Paste profile picture or draw placeholder."""
    draw = ImageDraw.Draw(card)
    if user.profile_picture:
        try:
            profile_img = Image.open(user.profile_picture.path).convert('RGB')
            profile_img = profile_img.resize((size, size), Image.Resampling.LANCZOS)
            # Create circular mask
            mask = Image.new('L', (size, size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([0, 0, size - 1, size - 1], fill=255)
            card.paste(profile_img, (x, y), mask)
            draw.ellipse([x, y, x + size, y + size], outline=border_color, width=border_width)
            return
        except Exception:
            pass
    # Placeholder
    draw.ellipse([x, y, x + size, y + size], fill=(220, 230, 240), outline=border_color, width=border_width)
    initials = f"{user.first_name[:1]}{user.last_name[:1]}".upper()
    try:
        init_font = ImageFont.truetype("arialbd.ttf", size // 3)
    except Exception:
        init_font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), initials, font=init_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x + (size - tw) // 2, y + (size - th) // 2 - 4), initials, fill=(100, 116, 139), font=init_font)


def _draw_rounded_rect(draw, coords, radius, fill=None, outline=None, width=1):
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = coords
    if fill:
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
        draw.pieslice([x1, y1, x1 + 2 * radius, y1 + 2 * radius], 180, 270, fill=fill)
        draw.pieslice([x2 - 2 * radius, y1, x2, y1 + 2 * radius], 270, 360, fill=fill)
        draw.pieslice([x1, y2 - 2 * radius, x1 + 2 * radius, y2], 90, 180, fill=fill)
        draw.pieslice([x2 - 2 * radius, y2 - 2 * radius, x2, y2], 0, 90, fill=fill)
    if outline:
        draw.arc([x1, y1, x1 + 2 * radius, y1 + 2 * radius], 180, 270, fill=outline, width=width)
        draw.arc([x2 - 2 * radius, y1, x2, y1 + 2 * radius], 270, 360, fill=outline, width=width)
        draw.arc([x1, y2 - 2 * radius, x1 + 2 * radius, y2], 90, 180, fill=outline, width=width)
        draw.arc([x2 - 2 * radius, y2 - 2 * radius, x2, y2], 0, 90, fill=outline, width=width)
        draw.line([x1 + radius, y1, x2 - radius, y1], fill=outline, width=width)
        draw.line([x1 + radius, y2, x2 - radius, y2], fill=outline, width=width)
        draw.line([x1, y1 + radius, x1, y2 - radius], fill=outline, width=width)
        draw.line([x2, y1 + radius, x2, y2 - radius], fill=outline, width=width)


# ==========================================
# TEMPLATE 1: CLASSIC (Orange accent)
# ==========================================
def _generate_classic_card(person, card_type='student'):
    """Classic template — Orange accent sidebar, clean professional layout."""
    W, H = 650, 1000  # Portrait orientation
    card = Image.new('RGB', (W, H), color='#FFFFFF')
    draw = ImageDraw.Draw(card)
    fonts = _load_fonts()
    school = _get_school_info()

    # Colors
    accent = (243, 146, 0)       # Orange
    accent_dark = (220, 120, 0)
    dark = (40, 40, 40)
    muted = (120, 130, 140)
    light_bg = (250, 248, 245)
    white = (255, 255, 255)

    # === TOP ACCENT BAND ===
    # Diagonal orange shape (left side)
    triangle_points = [(0, 0), (200, 0), (0, 280)]
    draw.polygon(triangle_points, fill=accent)
    # Small triangle accent
    draw.polygon([(0, 280), (150, 0), (200, 0), (0, 340)], fill=accent_dark)

    # School name area (top right)
    draw.text((220, 40), school['name'][:28].upper(), fill=dark, font=fonts['header'])
    draw.text((220, 78), school['motto'][:45], fill=muted, font=fonts['motto'])

    # Top accent line
    draw.rectangle([(220, 105), (W - 40, 107)], fill=accent)

    # === PROFILE PHOTO ===
    photo_size = 150
    photo_x = (W - photo_size) // 2
    photo_y = 140
    # Circle border
    draw.ellipse([photo_x - 5, photo_y - 5, photo_x + photo_size + 5, photo_y + photo_size + 5], fill=accent)
    _paste_profile(card, person.user, photo_x, photo_y, photo_size, border_color=accent, border_width=4)

    # === CARD TYPE LABEL ===
    type_label = "STUDENT ID CARD" if card_type == 'student' else "TEACHER ID CARD"
    bbox = draw.textbbox((0, 0), type_label, font=fonts['label'])
    lw = bbox[2] - bbox[0]
    draw.text(((W - lw) // 2, photo_y + photo_size + 20), type_label, fill=accent, font=fonts['label'])

    # === INFO SECTION ===
    info_y = photo_y + photo_size + 55
    left_margin = 60
    label_x = left_margin
    value_x = left_margin + 165

    if card_type == 'student':
        fields = [
            ("Reg No", person.admission_number),
            ("Student ID", f"STU-{person.id:06d}"),
            ("Student Name", person.user.get_full_name()[:30]),
            ("Class", person.current_class.name if person.current_class else "N/A"),
            ("Blood Group", person.blood_group if person.blood_group else "N/A"),
            ("Emergency", person.emergency_contact),
        ]
    else:
        subjects = ", ".join([s.name for s in person.subjects.all()[:3]])
        fields = [
            ("Employee ID", person.employee_id),
            ("Teacher ID", f"TCH-{person.id:06d}"),
            ("Name", person.user.get_full_name()[:30]),
            ("Qualification", person.qualification[:30] if person.qualification else "N/A"),
            ("Subjects", subjects[:30] if subjects else "N/A"),
            ("Phone", person.user.phone if person.user.phone else "N/A"),
        ]

    for i, (label, value) in enumerate(fields):
        y = info_y + i * 42
        # Alternate row bg
        if i % 2 == 0:
            draw.rectangle([(left_margin - 10, y - 5), (W - left_margin + 10, y + 32)], fill=light_bg)
        draw.text((label_x, y + 2), label, fill=muted, font=fonts['label'])
        draw.text((value_x, y), f":  {value}", fill=dark, font=fonts['value'])

    # === BOTTOM BAR ===
    bottom_y = H - 120
    draw.rectangle([(0, bottom_y), (W, H)], fill=accent)
    draw.text((30, bottom_y + 15), school['address'][:50], fill=white, font=fonts['small'])
    draw.text((30, bottom_y + 35), f"Phone: {school['phone']}", fill=white, font=fonts['small'])

    # === QR CODE (bottom right) ===
    qr_data = f"STU-{person.id:06d}|{person.user.email}" if card_type == 'student' else f"TCH-{person.id:06d}|{person.user.email}"
    qr_img = _make_qr(qr_data, 80)
    qr_x = W - 110
    qr_y = bottom_y - 100
    # White bg behind QR
    draw.rectangle([qr_x - 5, qr_y - 5, qr_x + 85, qr_y + 85], fill=white)
    card.paste(qr_img, (qr_x, qr_y))

    # Validity
    draw.text((30, bottom_y - 40), f"Issued: {datetime.now().strftime('%d/%m/%Y')}", fill=muted, font=fonts['small'])
    draw.text((30, bottom_y - 22), "Valid: 31/08/2027", fill=muted, font=fonts['small'])

    return card


# ==========================================
# TEMPLATE 2: MODERN (Gradient / Vibrant)
# ==========================================
def _generate_modern_card(person, card_type='student'):
    """Modern template — Gradient header, vibrant purple/magenta, wavy shapes."""
    W, H = 650, 1000
    card = Image.new('RGB', (W, H), color='#FFFFFF')
    draw = ImageDraw.Draw(card)
    fonts = _load_fonts()
    school = _get_school_info()

    # Colors
    primary = (130, 40, 160)      # Purple
    secondary = (200, 50, 130)    # Magenta
    accent = (180, 45, 145)       # Mid blend
    dark = (35, 35, 50)
    muted = (110, 115, 130)
    white = (255, 255, 255)
    light_purple = (245, 238, 252)

    # === GRADIENT HEADER ===
    header_h = 200
    for y in range(header_h):
        ratio = y / header_h
        r = int(primary[0] + (secondary[0] - primary[0]) * ratio)
        g = int(primary[1] + (secondary[1] - primary[1]) * ratio)
        b = int(primary[2] + (secondary[2] - primary[2]) * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Decorative diagonal stripe
    draw.polygon([(0, 160), (W, 120), (W, 200), (0, 200)], fill=white)

    # Wavy bottom of header
    for x in range(W):
        import math
        wave_y = int(170 + 15 * math.sin(x / 40))
        draw.line([(x, wave_y), (x, 200)], fill=white)

    # School name in header
    bbox = draw.textbbox((0, 0), school['name'][:25].upper(), font=fonts['header'])
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, 30), school['name'][:25].upper(), fill=white, font=fonts['header'])

    # Motto
    bbox2 = draw.textbbox((0, 0), school['motto'][:40], font=fonts['motto'])
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((W - tw2) // 2, 68), school['motto'][:40], fill=(255, 220, 240), font=fonts['motto'])

    # Card type badge
    type_label = "STUDENT ID" if card_type == 'student' else "TEACHER ID"
    bbox3 = draw.textbbox((0, 0), type_label, font=fonts['value'])
    tw3 = bbox3[2] - bbox3[0]
    badge_x = (W - tw3 - 30) // 2
    _draw_rounded_rect(draw, [badge_x, 95, badge_x + tw3 + 30, 120], 10, fill=white)
    draw.text((badge_x + 15, 98), type_label, fill=primary, font=fonts['value'])

    # === PROFILE PHOTO ===
    photo_size = 140
    photo_x = (W - photo_size) // 2
    photo_y = 210
    # Decorative ring
    draw.ellipse([photo_x - 8, photo_y - 8, photo_x + photo_size + 8, photo_y + photo_size + 8], fill=accent)
    draw.ellipse([photo_x - 4, photo_y - 4, photo_x + photo_size + 4, photo_y + photo_size + 4], fill=white)
    _paste_profile(card, person.user, photo_x, photo_y, photo_size, border_color=white, border_width=3)

    # Name below photo
    name = person.user.get_full_name()[:28]
    bbox_n = draw.textbbox((0, 0), name, font=fonts['name'])
    nw = bbox_n[2] - bbox_n[0]
    draw.text(((W - nw) // 2, photo_y + photo_size + 15), name, fill=dark, font=fonts['name'])

    # ID below name
    id_str = f"STU-{person.id:06d}" if card_type == 'student' else f"TCH-{person.id:06d}"
    bbox_id = draw.textbbox((0, 0), id_str, font=fonts['label'])
    iw = bbox_id[2] - bbox_id[0]
    draw.text(((W - iw) // 2, photo_y + photo_size + 45), id_str, fill=accent, font=fonts['label'])

    # === INFO SECTION ===
    info_y = photo_y + photo_size + 80
    left_margin = 50

    if card_type == 'student':
        fields = [
            ("Reg No", person.admission_number),
            ("Class", person.current_class.name if person.current_class else "N/A"),
            ("Blood Group", person.blood_group if person.blood_group else "N/A"),
            ("Emergency", person.emergency_contact),
            ("Email", person.user.email[:30] if person.user.email else "N/A"),
        ]
    else:
        subjects = ", ".join([s.name for s in person.subjects.all()[:3]])
        fields = [
            ("Employee ID", person.employee_id),
            ("Qualification", person.qualification[:28] if person.qualification else "N/A"),
            ("Subjects", subjects[:28] if subjects else "N/A"),
            ("Phone", person.user.phone if person.user.phone else "N/A"),
            ("Email", person.user.email[:30] if person.user.email else "N/A"),
        ]

    for i, (label, value) in enumerate(fields):
        y = info_y + i * 40
        # Pill background
        _draw_rounded_rect(draw, [left_margin - 5, y - 3, W - left_margin + 5, y + 30], 8, fill=light_purple)
        # Colored dot
        draw.ellipse([left_margin + 5, y + 8, left_margin + 15, y + 18], fill=accent)
        draw.text((left_margin + 25, y + 2), f"{label}:", fill=muted, font=fonts['label'])
        draw.text((left_margin + 155, y), value, fill=dark, font=fonts['value'])

    # === BOTTOM SECTION ===
    bottom_y = H - 160
    # Wavy top separator
    for x in range(W):
        import math
        wave_y = int(bottom_y + 10 * math.sin(x / 50))
        draw.line([(x, wave_y), (x, bottom_y + 15)], fill=light_purple)

    # Validity
    draw.text((left_margin, bottom_y + 25), f"Joined: {datetime.now().strftime('%d/%m/%Y')}", fill=muted, font=fonts['small'])
    draw.text((left_margin, bottom_y + 45), "Expires: 31/08/2027", fill=accent, font=fonts['small'])

    # QR code
    qr_data = f"STU-{person.id:06d}|{person.user.email}" if card_type == 'student' else f"TCH-{person.id:06d}|{person.user.email}"
    qr_img = _make_qr(qr_data, 90)
    qr_x = W - 140
    qr_y = bottom_y + 20
    card.paste(qr_img, (qr_x, qr_y))

    # Bottom gradient bar
    bar_y = H - 50
    for y_pos in range(bar_y, H):
        ratio = (y_pos - bar_y) / (H - bar_y)
        r = int(primary[0] + (secondary[0] - primary[0]) * ratio)
        g = int(primary[1] + (secondary[1] - primary[1]) * ratio)
        b = int(primary[2] + (secondary[2] - primary[2]) * ratio)
        draw.line([(0, y_pos), (W, y_pos)], fill=(r, g, b))

    draw.text((20, H - 38), school['phone'], fill=white, font=fonts['small'])
    draw.text((W // 2 - 40, H - 38), school['email'][:25], fill=white, font=fonts['small'])

    return card


# ==========================================
# TEMPLATE 3: ELEGANT (Navy & Gold)
# ==========================================
def _generate_elegant_card(person, card_type='student'):
    """Elegant template — Navy & gold, horizontal professional layout."""
    W, H = 920, 580  # Landscape orientation
    card = Image.new('RGB', (W, H), color='#FFFFFF')
    draw = ImageDraw.Draw(card)
    fonts = _load_fonts()
    school = _get_school_info()

    # Colors
    navy = (15, 30, 65)
    gold = (200, 165, 60)
    gold_light = (255, 230, 150)
    dark = (25, 30, 45)
    muted = (100, 110, 125)
    white = (255, 255, 255)
    cream = (252, 250, 245)

    # === NAVY HEADER BAR ===
    draw.rectangle([(0, 0), (W, 130)], fill=navy)
    # Gold accent line
    draw.rectangle([(0, 130), (W, 136)], fill=gold)

    # School name
    draw.text((30, 25), school['name'][:30].upper(), fill=white, font=fonts['header'])
    draw.text((30, 65), school['motto'][:45], fill=gold_light, font=fonts['motto'])

    # Card type label (right side)
    type_label = "STUDENT IDENTIFICATION" if card_type == 'student' else "STAFF IDENTIFICATION"
    bbox = draw.textbbox((0, 0), type_label, font=fonts['label'])
    tw = bbox[2] - bbox[0]
    draw.text((W - tw - 30, 25), type_label, fill=gold, font=fonts['label'])

    # Address in header
    draw.text((W - 300, 65), school['address'][:35], fill=(180, 190, 210), font=fonts['small'])

    # === LEFT SIDE: PROFILE ===
    photo_size = 160
    photo_x = 40
    photo_y = 170
    # Gold frame
    draw.rectangle([photo_x - 4, photo_y - 4, photo_x + photo_size + 4, photo_y + photo_size + 4], fill=gold)
    draw.rectangle([photo_x - 2, photo_y - 2, photo_x + photo_size + 2, photo_y + photo_size + 2], fill=white)
    # Square profile (not circular for elegant style)
    if person.user.profile_picture:
        try:
            profile_img = Image.open(person.user.profile_picture.path).convert('RGB')
            profile_img = profile_img.resize((photo_size, photo_size), Image.Resampling.LANCZOS)
            card.paste(profile_img, (photo_x, photo_y))
        except Exception:
            draw.rectangle([photo_x, photo_y, photo_x + photo_size, photo_y + photo_size], fill=cream)
            initials = f"{person.user.first_name[:1]}{person.user.last_name[:1]}".upper()
            try:
                init_font = ImageFont.truetype("arialbd.ttf", 48)
            except Exception:
                init_font = ImageFont.load_default()
            bbox_i = draw.textbbox((0, 0), initials, font=init_font)
            iw, ih = bbox_i[2] - bbox_i[0], bbox_i[3] - bbox_i[1]
            draw.text((photo_x + (photo_size - iw) // 2, photo_y + (photo_size - ih) // 2 - 5), initials, fill=navy, font=init_font)
    else:
        draw.rectangle([photo_x, photo_y, photo_x + photo_size, photo_y + photo_size], fill=cream)
        initials = f"{person.user.first_name[:1]}{person.user.last_name[:1]}".upper()
        try:
            init_font = ImageFont.truetype("arialbd.ttf", 48)
        except Exception:
            init_font = ImageFont.load_default()
        bbox_i = draw.textbbox((0, 0), initials, font=init_font)
        iw, ih = bbox_i[2] - bbox_i[0], bbox_i[3] - bbox_i[1]
        draw.text((photo_x + (photo_size - iw) // 2, photo_y + (photo_size - ih) // 2 - 5), initials, fill=navy, font=init_font)

    # Name below photo
    name = person.user.get_full_name()[:25].upper()
    bbox_n = draw.textbbox((0, 0), name, font=fonts['name'])
    nw = bbox_n[2] - bbox_n[0]
    name_x = photo_x + (photo_size - nw) // 2
    draw.text((max(10, name_x), photo_y + photo_size + 18), name, fill=navy, font=fonts['name'])

    # Role under name
    role = person.current_class.name if card_type == 'student' and person.current_class else (person.qualification[:20] if card_type == 'teacher' and person.qualification else '')
    if role:
        bbox_r = draw.textbbox((0, 0), role, font=fonts['label'])
        rw = bbox_r[2] - bbox_r[0]
        role_x = photo_x + (photo_size - rw) // 2
        draw.text((max(10, role_x), photo_y + photo_size + 48), role, fill=gold, font=fonts['label'])

    # === RIGHT SIDE: INFO ===
    info_x = photo_x + photo_size + 50
    info_y = 160

    if card_type == 'student':
        fields = [
            ("ID NO", f"STU-{person.id:06d}"),
            ("REG NO", person.admission_number),
            ("CLASS", person.current_class.name if person.current_class else "N/A"),
            ("BLOOD", person.blood_group if person.blood_group else "N/A"),
            ("PHONE", person.emergency_contact),
        ]
    else:
        subjects = ", ".join([s.name for s in person.subjects.all()[:2]])
        fields = [
            ("ID NO", f"TCH-{person.id:06d}"),
            ("EMP ID", person.employee_id),
            ("SUBJECTS", subjects[:25] if subjects else "N/A"),
            ("PHONE", person.user.phone if person.user.phone else "N/A"),
            ("EMAIL", person.user.email[:25] if person.user.email else "N/A"),
        ]

    for i, (label, value) in enumerate(fields):
        y = info_y + i * 48
        draw.text((info_x, y), label, fill=muted, font=fonts['label'])
        # Gold colon separator
        draw.text((info_x + 95, y), ":", fill=gold, font=fonts['label'])
        draw.text((info_x + 115, y - 1), value, fill=dark, font=fonts['value'])
        # Subtle underline
        draw.line([(info_x, y + 28), (info_x + 350, y + 28)], fill=(230, 230, 230), width=1)

    # === QR & VALIDITY (bottom right) ===
    qr_data = f"STU-{person.id:06d}|{person.user.email}" if card_type == 'student' else f"TCH-{person.id:06d}|{person.user.email}"
    qr_img = _make_qr(qr_data, 100)
    qr_x = W - 135
    qr_y = 170

    # Gold border around QR
    draw.rectangle([qr_x - 4, qr_y - 4, qr_x + 104, qr_y + 104], fill=gold)
    draw.rectangle([qr_x - 2, qr_y - 2, qr_x + 102, qr_y + 102], fill=white)
    card.paste(qr_img, (qr_x, qr_y))

    # Validity below QR
    draw.text((qr_x - 10, qr_y + 115), f"Issued: {datetime.now().strftime('%d/%m/%Y')}", fill=muted, font=fonts['small'])
    draw.text((qr_x - 10, qr_y + 135), "Valid: 31/08/2027", fill=muted, font=fonts['small'])

    # === BOTTOM BAR ===
    draw.rectangle([(0, H - 40), (W, H)], fill=navy)
    draw.rectangle([(0, H - 43), (W, H - 40)], fill=gold)
    draw.text((30, H - 32), f"{school['phone']}  |  {school['email'][:30]}  |  {school['address'][:35]}", fill=(180, 190, 210), font=fonts['small'])

    # Border
    draw.rectangle([(0, 0), (W - 1, H - 1)], outline=navy, width=2)

    return card


# ==========================================
# PUBLIC API — called by views
# ==========================================
def generate_student_id_card(student, template=None):
    """
    Generate student ID card using the school's selected template.

    Args:
        student: Student object
        template: Override template name ('classic', 'modern', 'elegant')

    Returns:
        PIL Image object
    """
    if template is None:
        school = _get_school_info()
        template = school.get('template', 'classic')

    generators = {
        'classic': _generate_classic_card,
        'modern': _generate_modern_card,
        'elegant': _generate_elegant_card,
    }
    gen = generators.get(template, _generate_classic_card)
    return gen(student, card_type='student')


def generate_teacher_id_card(teacher, template=None):
    """
    Generate teacher ID card using the school's selected template.

    Args:
        teacher: Teacher object
        template: Override template name ('classic', 'modern', 'elegant')

    Returns:
        PIL Image object
    """
    if template is None:
        school = _get_school_info()
        template = school.get('template', 'classic')

    generators = {
        'classic': _generate_classic_card,
        'modern': _generate_modern_card,
        'elegant': _generate_elegant_card,
    }
    gen = generators.get(template, _generate_classic_card)
    return gen(teacher, card_type='teacher')


# PDF Export Functions
def export_id_card_to_pdf(card_image):
    """
    Convert PIL Image to PDF for printing.
    Auto-detects orientation from image dimensions.

    Args:
        card_image: PIL Image object

    Returns:
        BytesIO object containing PDF
    """
    from reportlab.pdfgen.canvas import Canvas, ImageReader
    from reportlab.lib.units import mm

    pdf_buffer = BytesIO()
    w, h = card_image.size

    if w > h:
        # Landscape (elegant template) — credit card proportions
        page_w, page_h = 148 * mm, 105 * mm
    else:
        # Portrait (classic / modern templates)
        page_w, page_h = 105 * mm, 148 * mm

    c = Canvas(pdf_buffer, pagesize=(page_w, page_h))
    c.drawImage(
        ImageReader(card_image),
        0, 0,
        width=page_w,
        height=page_h,
        preserveAspectRatio=True,
    )
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer


def export_multiple_id_cards_to_pdf(card_list):
    """
    Export multiple ID cards to a single A4 PDF document.
    Auto-detects orientation from the first card.

    Args:
        card_list: List of (name, PIL_Image) tuples

    Returns:
        BytesIO object containing multi-page PDF
    """
    from reportlab.pdfgen.canvas import Canvas, ImageReader
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm

    if not card_list:
        return BytesIO()

    pdf_buffer = BytesIO()
    c = Canvas(pdf_buffer, pagesize=A4)
    a4_w, a4_h = A4  # 210mm x 297mm in points

    # Detect orientation from first card
    first_img = card_list[0][1]
    landscape = first_img.size[0] > first_img.size[1]

    if landscape:
        # Landscape cards: 2 rows x 1 col = 2 per page
        card_width = 190 * mm
        card_height = 120 * mm
        margin_x = 10 * mm
        margin_y = 10 * mm
        cards_per_page = 2
        cards_per_row = 1
    else:
        # Portrait cards: 2 cols x 3 rows = 6 per page
        card_width = 95 * mm
        card_height = 90 * mm
        margin_x = 5 * mm
        margin_y = 5 * mm
        cards_per_page = 6
        cards_per_row = 2

    for idx, (name, card_img) in enumerate(card_list):
        if idx > 0 and idx % cards_per_page == 0:
            c.showPage()

        pos = idx % cards_per_page
        row = pos // cards_per_row
        col = pos % cards_per_row

        x = margin_x + col * (card_width + margin_x)
        y = a4_h - margin_y - (row + 1) * (card_height + margin_y)

        try:
            c.drawImage(
                ImageReader(card_img),
                x, y,
                width=card_width,
                height=card_height,
                preserveAspectRatio=True,
            )
        except Exception:
            pass

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer
