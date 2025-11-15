from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import requests
from PIL import Image
import io
import re

pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))

def clean_markdown(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'###\s+', '', text)
    text = re.sub(r'##\s+', '', text)
    text = re.sub(r'#\s+', '', text)
    text = text.replace('\n\n', '<br/><br/>')
    text = text.replace('\n', '<br/>')
    return text

def generate_design_pdf(project_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName='DejaVuSans-Bold',
        fontSize=24,
        textColor=colors.HexColor('#1f1f1f'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName='DejaVuSans-Bold',
        fontSize=16,
        textColor=colors.HexColor('#1f1f1f'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName='DejaVuSans',
        fontSize=10,
        spaceAfter=12
    )
    
    story.append(Paragraph("Дизайн-проект", title_style))
    story.append(Paragraph(f"<b>{project_data['name']}</b>", heading_style))
    story.append(Spacer(1, 0.5*cm))
    
    info_data = [
        ['Тип помещения:', project_data['room_type']],
        ['Цель использования:', project_data['purpose']],
        ['Дата создания:', project_data.get('created_at', 'Не указана')]
    ]
    info_table = Table(info_data, colWidths=[5*cm, 11*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'DejaVuSans-Bold'),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc'))
    ]))
    story.append(info_table)
    story.append(Spacer(1, 1*cm))
    
    story.append(Paragraph("Анализ помещения", heading_style))
    analysis_text = clean_markdown(project_data['analysis'])
    story.append(Paragraph(analysis_text, body_style))
    story.append(PageBreak())
    
    story.append(Paragraph("Варианты дизайна", heading_style))
    
    for idx, variant in enumerate(project_data['variants'], 1):
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"<b>Вариант {idx}</b> (Итераций: {variant['iterations']})", heading_style))
        
        try:
            response = requests.get(variant['image_url'], timeout=10)
            img_data = BytesIO(response.content)
            pil_img = Image.open(img_data)
            
            img_buffer = BytesIO()
            pil_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            img = RLImage(img_buffer, width=14*cm, height=14*cm*pil_img.height/pil_img.width)
            story.append(img)
        except Exception as e:
            story.append(Paragraph(f"Не удалось загрузить изображение: {str(e)}", body_style))
        
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f"<b>Описание:</b> {variant['prompt'][:200]}...", body_style))
        
        if idx < len(project_data['variants']):
            story.append(PageBreak())
    
    if project_data.get('recommendations'):
        story.append(PageBreak())
        story.append(Paragraph("Рекомендации по материалам", heading_style))
        rec_text = clean_markdown(project_data['recommendations'])
        story.append(Paragraph(rec_text, body_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer
