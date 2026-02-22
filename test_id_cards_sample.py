"""
Test ID card generation with mock data (no database required)
"""
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import qrcode
from datetime import datetime
from pathlib import Path

def generate_sample_student_id_card(name="John Doe", student_id=1001, class_name="Basic 7"):
    """
    Generate a sample student ID card as PIL Image.
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
    
    # Profile placeholder circle with gradient effect
    draw.ellipse(
        [(profile_x, profile_y), (profile_x + profile_size, profile_y + profile_size)],
        fill=light_bg,
        outline=primary_color,
        width=2
    )
    
    # Add initials in profile area
    draw.text((profile_x + 50, profile_y + 55), name[0], fill=primary_color, font=ImageFont.load_default())
    
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
    draw.text((card_width // 2 - 100, 70), "SchoolPortal", fill='white', font=small_font)
    
    # Student information
    draw.text((text_x, text_y), "NAME", fill=(100, 116, 139), font=label_font)
    draw.text((text_x, text_y + 25), name[:35], fill=text_color, font=name_font)
    
    # ID Number
    draw.text((text_x, text_y + 70), "ID NUMBER", fill=(100, 116, 139), font=label_font)
    draw.text((text_x, text_y + 95), f"STU-{student_id:06d}", fill=text_color, font=name_font)
    
    # Class
    draw.text((text_x, text_y + 140), f"CLASS: {class_name}", fill=text_color, font=label_font)
    
    # Bottom section - validity
    validity_y = 420
    draw.line([(30, validity_y - 20), (card_width - 30, validity_y - 20)], fill=primary_color, width=2)
    
    draw.text((30, validity_y), "ISSUED", fill=(100, 116, 139), font=small_font)
    draw.text((30, validity_y + 20), datetime.now().strftime("%d/%m/%Y"), fill=text_color, font=label_font)
    
    draw.text((280, validity_y), "VALID UNTIL", fill=(100, 116, 139), font=small_font)
    draw.text((280, validity_y + 20), "31/12/2026", fill=text_color, font=label_font)
    
    # QR Code
    qr = qrcode.QRCode(version=1, box_size=5, border=1)
    qr.add_data(f"STU-{student_id:06d}|{name}@school.edu")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((100, 100))
    card.paste(qr_img, (card_width - 140, validity_y))
    
    return card


def generate_sample_teacher_id_card(name="Jane Smith", teacher_id=2001, subjects="Mathematics, Physics"):
    """
    Generate a sample teacher ID card as PIL Image.
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
    
    # Add initials in profile area
    draw.text((profile_x + 50, profile_y + 55), name[0], fill=accent_color, font=ImageFont.load_default())
    
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
    draw.text((card_width // 2 - 100, 70), "SchoolPortal", fill='white', font=small_font)
    
    # Teacher information
    draw.text((text_x, text_y), "NAME", fill=(100, 116, 139), font=label_font)
    draw.text((text_x, text_y + 25), name[:35], fill=text_color, font=name_font)
    
    # ID Number
    draw.text((text_x, text_y + 70), "ID NUMBER", fill=(100, 116, 139), font=label_font)
    draw.text((text_x, text_y + 95), f"TCH-{teacher_id:06d}", fill=text_color, font=name_font)
    
    # Subjects
    draw.text((text_x, text_y + 140), f"SUBJECTS: {subjects[:40]}", fill=text_color, font=label_font)
    
    # Bottom section
    validity_y = 420
    draw.line([(30, validity_y - 20), (card_width - 30, validity_y - 20)], fill=accent_color, width=2)
    
    draw.text((30, validity_y), "ISSUED", fill=(100, 116, 139), font=small_font)
    draw.text((30, validity_y + 20), datetime.now().strftime("%d/%m/%Y"), fill=text_color, font=label_font)
    
    draw.text((280, validity_y), "VALID UNTIL", fill=(100, 116, 139), font=small_font)
    draw.text((280, validity_y + 20), "31/12/2026", fill=text_color, font=label_font)
    
    # QR Code
    qr = qrcode.QRCode(version=1, box_size=5, border=1)
    qr.add_data(f"TCH-{teacher_id:06d}|{name}@school.edu")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((100, 100))
    card.paste(qr_img, (card_width - 140, validity_y))
    
    return card


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎓 ID Card Generation Test (Sample Data)")
    print("="*60)
    
    # Create output directory
    output_dir = Path("id_cards")
    output_dir.mkdir(exist_ok=True)
    
    # Test Student ID Cards
    print("\n📚 Generating Sample Student ID Cards...")
    print("-" * 60)
    
    students = [
        ("John Doe", 1001, "Basic 7"),
        ("Mary Jane", 1002, "Basic 8"),
        ("Samuel Asante", 1003, "Basic 9"),
    ]
    
    for name, student_id, class_name in students:
        try:
            card = generate_sample_student_id_card(name, student_id, class_name)
            filename = f"{output_dir}/sample_student_{student_id}_{name.replace(' ', '_')}.png"
            card.save(filename)
            print(f"✅ Generated: {name} (ID: STU-{student_id:06d}, Class: {class_name})")
            print(f"   → Saved to: {filename}")
        except Exception as e:
            print(f"❌ Error generating card for {name}: {str(e)}")
    
    # Test Teacher ID Cards
    print("\n👨‍🏫 Generating Sample Teacher ID Cards...")
    print("-" * 60)
    
    teachers = [
        ("Jane Smith", 2001, "Mathematics, Physics"),
        ("Mr. Kwame", 2002, "English, Literature"),
        ("Dr. Ama Owusu", 2003, "Biology, Chemistry"),
    ]
    
    for name, teacher_id, subjects in teachers:
        try:
            card = generate_sample_teacher_id_card(name, teacher_id, subjects)
            filename = f"{output_dir}/sample_teacher_{teacher_id}_{name.replace(' ', '_')}.png"
            card.save(filename)
            print(f"✅ Generated: {name} (ID: TCH-{teacher_id:06d})")
            print(f"   → Subjects: {subjects}")
            print(f"   → Saved to: {filename}")
        except Exception as e:
            print(f"❌ Error generating card for {name}: {str(e)}")
    
    # Summary
    print("\n" + "="*60)
    print("✨ Test Complete!")
    print("="*60)
    print(f"📁 All ID cards saved to: {output_dir.absolute()}")
    print(f"📊 Generated {len(students)} student cards and {len(teachers)} teacher cards")
    print("="*60 + "\n")
