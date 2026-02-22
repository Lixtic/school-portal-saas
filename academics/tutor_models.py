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
def generate_student_id_card(student):
    """
    Generate a professional student ID card as PIL Image.
    
    Args:
        student: Student object
        
    Returns:
        PIL Image object of ID card
    """
    # Card dimensions: 85.6 x 53.98mm (standard ID card size, 300 DPI)
    card_width = 920
    card_height = 580
    
    # Create card
    card = Image.new('RGB', (card_width, card_height), color='white')
    draw = ImageDraw.Draw(card)
    
    # Colors
    primary_color = (15, 118, 110)  # Teal
    text_color = (30, 41, 59)  # Dark slate
    light_bg = (240, 253, 250)  # Light teal
    
    # Background
    draw.rectangle([(0, 0), (card_width, card_height)], fill='white', outline=primary_color, width=3)
    
    # Header band
    draw.rectangle([(0, 0), (card_width, 120)], fill=primary_color)
    
    # Left side profile area
    profile_x, profile_y = 30, 150
    profile_size = 140
    
    # Profile placeholder circle
    draw.ellipse(
        [(profile_x, profile_y), (profile_x + profile_size, profile_y + profile_size)],
        fill=light_bg,
        outline=primary_color,
        width=2
    )
    
    # Try to use student profile image if available
    if student.user.profile_picture:
        try:
            profile_img = Image.open(student.user.profile_picture.path)
            profile_img = profile_img.resize((profile_size, profile_size), Image.Resampling.LANCZOS)
            card.paste(profile_img, (profile_x, profile_y))
        except:
            pass  # Fall back to placeholder
    
    # Text starting position (right of profile)
    text_x = profile_x + profile_size + 30
    text_y = 150
    
    # Try to load fonts (fallback to default if not available)
    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
        name_font = ImageFont.truetype("arial.ttf", 20)
        label_font = ImageFont.truetype("arial.ttf", 14)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except:
        title_font = name_font = label_font = small_font = ImageFont.load_default()
    
    # Header text
    draw.text((card_width // 2 - 80, 35), "STUDENT ID CARD", fill='white', font=title_font)
    school_name = getattr(student.user.request.tenant, 'name', 'School Name') if hasattr(student.user, 'request') else 'School Name'
    draw.text((card_width // 2 - 100, 70), school_name[:30], fill='white', font=small_font)
    
    # Student information
    draw.text((text_x, text_y), "NAME", fill=(100, 116, 139), font=label_font)
    draw.text((text_x, text_y + 25), student.user.get_full_name()[:35], fill=text_color, font=name_font)
    
    # ID Number
    draw.text((text_x, text_y + 70), "ID NUMBER", fill=(100, 116, 139), font=label_font)
    draw.text((text_x, text_y + 95), f"STU-{student.id:06d}", fill=text_color, font=name_font)
    
    # Class and Email
    email_y = text_y + 140
    draw.text((text_x, email_y), f"CLASS: {student.current_class.name if student.current_class else 'N/A'}", 
              fill=text_color, font=label_font)
    
    # Bottom section - validity
    validity_y = 420
    draw.line([(30, validity_y - 20), (card_width - 30, validity_y - 20)], fill=primary_color, width=2)
    
    draw.text((30, validity_y), "ISSUED", fill=(100, 116, 139), font=small_font)
    draw.text((30, validity_y + 20), datetime.now().strftime("%d/%m/%Y"), fill=text_color, font=label_font)
    
    draw.text((280, validity_y), "VALID UNTIL", fill=(100, 116, 139), font=small_font)
    draw.text((280, validity_y + 20), "31/12/2026", fill=text_color, font=label_font)
    
    # QR Code
    qr = qrcode.QRCode(version=1, box_size=5, border=1)
    qr.add_data(f"STU-{student.id:06d}|{student.user.email}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((100, 100))
    card.paste(qr_img, (card_width - 140, validity_y))
    
    return card


def generate_teacher_id_card(teacher):
    """
    Generate a professional teacher ID card as PIL Image.
    
    Args:
        teacher: Teacher object
        
    Returns:
        PIL Image object of ID card
    """
    # Card dimensions
    card_width = 920
    card_height = 580
    
    # Create card
    card = Image.new('RGB', (card_width, card_height), color='white')
    draw = ImageDraw.Draw(card)
    
    # Colors
    primary_color = (15, 78, 74)  # Dark teal
    accent_color = (15, 118, 110)  # Teal
    text_color = (30, 41, 59)  # Dark slate
    light_bg = (240, 253, 250)  # Light teal
    
    # Background
    draw.rectangle([(0, 0), (card_width, card_height)], fill='white', outline=primary_color, width=3)
    
    # Header band
    draw.rectangle([(0, 0), (card_width, 120)], fill=primary_color)
    
    # Left side profile area
    profile_x, profile_y = 30, 150
    profile_size = 140
    
    # Profile placeholder circle
    draw.ellipse(
        [(profile_x, profile_y), (profile_x + profile_size, profile_y + profile_size)],
        fill=light_bg,
        outline=accent_color,
        width=2
    )
    
    # Try to use teacher profile image if available
    if teacher.user.profile_picture:
        try:
            profile_img = Image.open(teacher.user.profile_picture.path)
            profile_img = profile_img.resize((profile_size, profile_size), Image.Resampling.LANCZOS)
            card.paste(profile_img, (profile_x, profile_y))
        except:
            pass
    
    # Text starting position
    text_x = profile_x + profile_size + 30
    text_y = 150
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
        name_font = ImageFont.truetype("arial.ttf", 20)
        label_font = ImageFont.truetype("arial.ttf", 14)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except:
        title_font = name_font = label_font = small_font = ImageFont.load_default()
    
    # Header text
    draw.text((card_width // 2 - 70, 35), "TEACHER ID CARD", fill='white', font=title_font)
    school_name = getattr(teacher.user.request.tenant, 'name', 'School Name') if hasattr(teacher.user, 'request') else 'School Name'
    draw.text((card_width // 2 - 100, 70), school_name[:30], fill='white', font=small_font)
    
    # Teacher information
    draw.text((text_x, text_y), "NAME", fill=(100, 116, 139), font=label_font)
    draw.text((text_x, text_y + 25), teacher.user.get_full_name()[:35], fill=text_color, font=name_font)
    
    # ID Number
    draw.text((text_x, text_y + 70), "ID NUMBER", fill=(100, 116, 139), font=label_font)
    draw.text((text_x, text_y + 95), f"TCH-{teacher.id:06d}", fill=text_color, font=name_font)
    
    # Qualification and subjects
    subjects = ", ".join([s.name for s in teacher.subjects.all()[:2]])
    draw.text((text_x, text_y + 140), f"SUBJECTS: {subjects if subjects else 'N/A'}", 
              fill=text_color, font=label_font)
    
    # Bottom section
    validity_y = 420
    draw.line([(30, validity_y - 20), (card_width - 30, validity_y - 20)], fill=accent_color, width=2)
    
    draw.text((30, validity_y), "ISSUED", fill=(100, 116, 139), font=small_font)
    draw.text((30, validity_y + 20), datetime.now().strftime("%d/%m/%Y"), fill=text_color, font=label_font)
    
    draw.text((280, validity_y), "VALID UNTIL", fill=(100, 116, 139), font=small_font)
    draw.text((280, validity_y + 20), "31/12/2026", fill=text_color, font=label_font)
    
    # QR Code
    qr = qrcode.QRCode(version=1, box_size=5, border=1)
    qr.add_data(f"TCH-{teacher.id:06d}|{teacher.user.email}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((100, 100))
    card.paste(qr_img, (card_width - 140, validity_y))
    
    return card


# PDF Export Functions
def export_id_card_to_pdf(card_image):
    """
    Convert PIL Image to PDF for printing (A6 ID card size).
    
    Args:
        card_image: PIL Image object
        
    Returns:
        BytesIO object containing PDF
    """
    from reportlab.pdfgen.canvas import Canvas, ImageReader
    from reportlab.lib.pagesizes import A6
    from reportlab.lib.units import mm
    
    pdf_buffer = BytesIO()
    
    # A6 is 105 x 148 mm (standard ID card size)
    c = Canvas(pdf_buffer, pagesize=(105*mm, 148*mm))
    
    # Draw the image on canvas
    img_width = 105*mm
    img_height = 148*mm
    
    c.drawImage(
        ImageReader(card_image),
        0, 0,
        width=img_width,
        height=img_height,
        preserveAspectRatio=False
    )
    
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer


def export_multiple_id_cards_to_pdf(card_list):
    """
    Export multiple ID cards to a single PDF document.
    
    Args:
        card_list: List of (name, PIL_Image) tuples
        
    Returns:
        BytesIO object containing multi-page PDF
    """
    from reportlab.pdfgen.canvas import Canvas, ImageReader
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    
    pdf_buffer = BytesIO()
    c = Canvas(pdf_buffer, pagesize=A4)
    
    # Cards per page: 2 x 3 grid (6 cards per A4 sheet)
    cards_per_page = 6
    cards_per_row = 2
    
    card_width = 105*mm
    card_height = 148*mm
    margin = 10*mm
    
    for idx, (name, card_img) in enumerate(card_list):
        if idx > 0 and idx % cards_per_page == 0:
            c.showPage()
        
        # Calculate position in grid
        pos_in_page = idx % cards_per_page
        row = pos_in_page // cards_per_row
        col = pos_in_page % cards_per_row
        
        x = margin + col * (card_width + margin)
        y = 297*mm - margin - (row + 1) * (card_height + margin)  # A4 height is 297mm
        
        try:
            c.drawImage(
                ImageReader(card_img),
                x, y,
                width=card_width,
                height=card_height,
                preserveAspectRatio=False
            )
        except:
            pass  # Skip if image can't be drawn
    
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer
