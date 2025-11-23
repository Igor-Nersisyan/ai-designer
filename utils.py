import base64
import json
import os
from google import genai
from google.genai import types

def encode_image(uploaded_file):
    """Конвертирует загруженный файл в base64"""
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def call_gemini_vision(system_prompt: str, user_text: str, image_bytes: bytes) -> str:
    """Вызов Gemini Pro Vision для анализа изображения. Возвращает только поле 'analysis' из JSON-ответа."""
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY не найден. Пожалуйста, добавьте API ключ в настройки.")
        
        if not image_bytes:
            raise Exception("Изображение не загружено. Пожалуйста, загрузите фото помещения.")
        
        client = genai.Client(api_key=api_key)
        
        full_prompt = f"""{system_prompt}

{user_text}

ВАЖНО: Верни ответ в JSON формате:
{{
  "reasoning": "твои внутренние рассуждения и анализ",
  "analysis": "финальный анализ в формате Markdown для пользователя"
}}"""
        
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg",
                ),
                full_prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            )
        )
        
        raw_content = response.text
        
        if not raw_content:
            raise Exception("Пустой ответ от Gemini Vision")
        
        try:
            parsed_json = json.loads(raw_content)
            if "analysis" in parsed_json:
                return parsed_json["analysis"]
            else:
                return raw_content
        except json.JSONDecodeError:
            return raw_content
            
    except Exception as e:
        raise Exception(f"Ошибка Gemini Vision: {str(e)}")

def call_gemini_vision_markdown(system_prompt: str, user_text: str, image_bytes: bytes, second_image_bytes: bytes = None) -> str:
    """Вызов Gemini Pro Vision для анализа изображения(й). Возвращает обычный Markdown текст.
    
    Args:
        system_prompt: Системный промпт
        user_text: Текст пользователя
        image_bytes: Байты основного изображения
        second_image_bytes: (опционально) Байты второго изображения для сравнения
    """
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY не найден. Пожалуйста, добавьте API ключ в настройки.")
        
        if not image_bytes:
            raise Exception("Изображение не загружено. Пожалуйста, загрузите фото помещения.")
        
        client = genai.Client(api_key=api_key)
        
        full_prompt = f"""{system_prompt}

{user_text}"""
        
        contents = [
            full_prompt,
            types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg",
            )
        ]
        
        if second_image_bytes:
            contents.append(types.Part.from_bytes(
                data=second_image_bytes,
                mime_type="image/jpeg",
            ))
        
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=8000,
            )
        )
        
        if not response:
            raise Exception("Не получен ответ от Gemini Vision API")
        
        content = None
        
        if hasattr(response, 'text') and response.text and response.text.strip():
            content = response.text.strip()
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                parts = candidate.content.parts
                text_parts = []
                for part in parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                if text_parts:
                    content = ''.join(text_parts).strip()
        
        if not content:
            raise Exception("Пустой ответ от Gemini Vision")
        
        return content
            
    except Exception as e:
        raise Exception(f"Ошибка Gemini Vision: {str(e)}")

def call_gemini(system_prompt: str, user_prompt: str, return_json_key: str = None) -> str:
    """Обычный вызов Gemini для текста. 
    
    Args:
        system_prompt: Системный промпт
        user_prompt: Промпт пользователя
        return_json_key: Если указан, функция попытается распарсить JSON ответ и вернуть значение этого ключа
    
    Returns:
        Текстовый ответ или значение указанного ключа из JSON
    """
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY не найден. Пожалуйста, добавьте API ключ в настройки.")
        
        client = genai.Client(api_key=api_key)
        
        full_prompt = f"""{system_prompt}

{user_prompt}"""
        
        config_params = {
            "temperature": 0.7,
            "max_output_tokens": 8000,
        }
        
        if return_json_key:
            config_params["response_mime_type"] = "application/json"
        
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=full_prompt,
            config=types.GenerateContentConfig(**config_params)
        )
        
        if not response:
            raise Exception("Не получен ответ от Gemini API")
        
        content = None
        
        if hasattr(response, 'text') and response.text and response.text.strip():
            content = response.text.strip()
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                parts = candidate.content.parts
                text_parts = []
                for part in parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                if text_parts:
                    content = ''.join(text_parts).strip()
        
        if not content:
            raise Exception("Пустой ответ от Gemini")
        
        if return_json_key:
            try:
                parsed_json = json.loads(content)
                if return_json_key in parsed_json:
                    return parsed_json[return_json_key]
                else:
                    raise Exception(f"Ключ '{return_json_key}' не найден в JSON ответе. Получен ответ: {content}")
            except json.JSONDecodeError as e:
                raise Exception(f"Не удалось распарсить JSON ответ: {e}. Получен ответ: {content}")
        
        return content
    except Exception as e:
        raise Exception(f"Ошибка Gemini: {str(e)}")

def generate_image(source_image_bytes: bytes, prompt: str) -> str:
    """Генерация изображения через Google Gemini API (gemini-2.5-flash-image)"""
    try:
        import requests
        from PIL import Image
        import io
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY не найден. Пожалуйста, добавьте API ключ в настройки.")
        
        img = Image.open(io.BytesIO(source_image_bytes))
        img_format = img.format.lower() if img.format else 'jpeg'
        mime_type = f"image/{img_format}" if img_format in ['jpeg', 'png', 'jpg'] else "image/jpeg"
        
        base64_image = base64.b64encode(source_image_bytes).decode('utf-8')
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        request_body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"Instruction: {prompt}. Keep geometry and structural elements unchanged. Output ONLY the modified image."
                        },
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64_image
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "response_modalities": ["IMAGE"]
            }
        }
        
        response = requests.post(url, headers=headers, json=request_body, timeout=120)
        
        if response.status_code != 200:
            error_detail = response.text
            raise Exception(f"API вернул ошибку {response.status_code}: {error_detail}")
        
        response_data = response.json()
        
        if "candidates" not in response_data:
            raise Exception(f"Неожиданный формат ответа: {response_data}")
        
        if len(response_data["candidates"]) == 0:
            raise Exception("API не вернул результатов генерации")
        
        candidate = response_data["candidates"][0]
        
        if "content" not in candidate:
            raise Exception(f"Отсутствует 'content' в ответе: {candidate}")
        
        if "parts" not in candidate["content"]:
            raise Exception(f"Отсутствует 'parts' в content: {candidate['content']}")
        
        parts = candidate["content"]["parts"]
        if len(parts) == 0:
            raise Exception("Parts пустой")
        
        part = parts[0]
        
        inline_data = part.get("inlineData") or part.get("inline_data")
        if not inline_data:
            raise Exception(f"Отсутствует 'inlineData' или 'inline_data' в part: {part}")
        
        base64_response = inline_data.get("data")
        if not base64_response:
            raise Exception(f"Отсутствует 'data' в inline_data: {inline_data}")
        data_url = f"data:image/jpeg;base64,{base64_response}"
        
        return data_url
        
    except Exception as e:
        raise Exception(f"Ошибка Gemini Image Generation: {str(e)}")

def refine_design_with_vision(design_image_url: str, original_prompt: str, user_feedback: str, refine_system_prompt: str) -> str:
    """Доработка дизайна с помощью Gemini Vision - анализирует изображение дизайна и создаёт новый промпт с минимальными изменениями"""
    try:
        import requests
        from io import BytesIO
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY не найден")
        
        if design_image_url.startswith('data:image'):
            header, encoded = design_image_url.split(',', 1)
            image_bytes = base64.b64decode(encoded)
        else:
            response = requests.get(design_image_url, timeout=10)
            image_bytes = response.content
        
        client = genai.Client(api_key=api_key)
        
        user_text = f"""ИСХОДНЫЙ ПРОМПТ, который создал этот дизайн:
{original_prompt}

ПОЖЕЛАНИЯ ПОЛЬЗОВАТЕЛЯ (внеси ТОЛЬКО эти изменения):
{user_feedback}

Проанализируй изображение текущего дизайна и создай промпт для точечной корректировки."""
        
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg",
                ),
                f"{refine_system_prompt}\n\n{user_text}"
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            )
        )
        
        raw_content = response.text
        
        if not raw_content:
            raise Exception("Пустой ответ от Gemini Vision при доработке дизайна")
        
        try:
            parsed_json = json.loads(raw_content)
            if "prompt" in parsed_json:
                return parsed_json["prompt"]
            else:
                raise Exception(f"Ключ 'prompt' не найден в JSON ответе. Получен ответ: {raw_content}")
        except json.JSONDecodeError as e:
            raise Exception(f"Не удалось распарсить JSON ответ при доработке: {e}. Получен ответ: {raw_content}")
            
    except Exception as e:
        raise Exception(f"Ошибка при доработке дизайна с Gemini Vision: {str(e)}")

def create_before_after_comparison(original_image_bytes: bytes, result_image_url: str) -> bytes:
    """Создает композитное изображение с половиной исходного изображения слева и половиной результата справа, 
    разделенные вертикальной линией в центре"""
    try:
        from PIL import Image as PILImage, ImageDraw
        from io import BytesIO
        import requests
        
        original_img = PILImage.open(BytesIO(original_image_bytes)).convert('RGB')
        
        if result_image_url.startswith('data:image'):
            header, encoded = result_image_url.split(',', 1)
            result_bytes = base64.b64decode(encoded)
            result_img = PILImage.open(BytesIO(result_bytes)).convert('RGB')
        else:
            resp = requests.get(result_image_url, timeout=10)
            result_img = PILImage.open(BytesIO(resp.content)).convert('RGB')
        
        width = 500
        height = 350
        half_width = width // 2
        
        original_img = original_img.resize((width, height), PILImage.Resampling.LANCZOS)
        result_img = result_img.resize((width, height), PILImage.Resampling.LANCZOS)
        
        composite = PILImage.new('RGB', (width, height), 'white')
        
        original_half = original_img.crop((0, 0, half_width, height))
        result_half = result_img.crop((half_width, 0, width, height))
        
        composite.paste(original_half, (0, 0))
        composite.paste(result_half, (half_width, 0))
        
        draw = ImageDraw.Draw(composite)
        line_color = (200, 200, 200)
        draw.line([(half_width, 0), (half_width, height)], fill=line_color, width=2)
        
        output_buffer = BytesIO()
        composite.save(output_buffer, format='PNG')
        output_buffer.seek(0)
        
        return output_buffer.getvalue()
        
    except Exception as e:
        raise Exception(f"Ошибка при создании композитного изображения: {str(e)}")

def generate_design_project_pdf(room_type: str, recommendations: str, shopping_list: str, design_image_url: str = None) -> bytes:
    """Генерирует PDF файл с рекомендациями и списком покупок"""
    try:
        import re
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from io import BytesIO
        import requests
        import subprocess
        
        def clean_text_for_pdf(text: str) -> str:
            """Удаляет эмодзи и markdown форматирование из текста"""
            if not text:
                return ""
            
            emoji_pattern = re.compile("["
                u"\U0001F600-\U0001F64F"
                u"\U0001F300-\U0001F5FF"
                u"\U0001F680-\U0001F6FF"
                u"\U0001F1E0-\U0001F1FF"
                u"\U00002702-\U000027B0"
                u"\U000024C2-\U0001F251"
                u"\U0001f926-\U0001f937"
                u"\U00010000-\U0010ffff"
                u"\u2640-\u2642"
                u"\u2600-\u2B55"
                u"\u200d"
                u"\u23cf"
                u"\u23e9"
                u"\u231a"
                u"\ufe0f"
                u"\u3030"
                "]+", flags=re.UNICODE)
            
            text = emoji_pattern.sub('', text)
            
            text = re.sub(r'^\s*#+\s+', '', text, flags=re.MULTILINE)
            
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
            
            text = re.sub(r'^[\s\-\*]+', '', text, flags=re.MULTILINE)
            
            return text.strip()
        
        try:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            
            if not os.path.exists(font_path):
                result = subprocess.run(['find', '/usr/share/fonts', '-name', '*DejaVu*Sans*.ttf'], 
                                       capture_output=True, text=True, timeout=5)
                if result.stdout:
                    font_path = result.stdout.strip().split('\n')[0]
                    font_bold_path = [f for f in result.stdout.strip().split('\n') if 'Bold' in f]
                    if font_bold_path:
                        font_bold_path = font_bold_path[0]
            
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('CustomFont', font_path))
                if os.path.exists(font_bold_path):
                    pdfmetrics.registerFont(TTFont('CustomFontBold', font_bold_path))
                    font_name = 'CustomFontBold'
                    normal_font = 'CustomFont'
                else:
                    font_name = 'CustomFont'
                    normal_font = 'CustomFont'
            else:
                font_name = 'Helvetica-Bold'
                normal_font = 'Helvetica'
        except:
            font_name = 'Helvetica-Bold'
            normal_font = 'Helvetica'
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName=font_name
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=10,
            spaceBefore=10,
            fontName=font_name
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_LEFT,
            fontName=normal_font
        )
        
        story.append(Paragraph("Дизайн-проект", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph(f"<b>Тип помещения:</b> {room_type}", normal_style))
        story.append(Spacer(1, 0.1*inch))
        
        if design_image_url:
            try:
                if design_image_url.startswith('data:image'):
                    header, encoded = design_image_url.split(',', 1)
                    image_bytes = base64.b64decode(encoded)
                    temp_image = BytesIO(image_bytes)
                else:
                    resp = requests.get(design_image_url, timeout=10)
                    temp_image = BytesIO(resp.content)
                
                from PIL import Image as PILImage
                img = PILImage.open(temp_image)
                max_width = 6*inch
                max_height = 4*inch
                img.thumbnail((int(max_width), int(max_height)), PILImage.Resampling.LANCZOS)
                
                img_buffer = BytesIO()
                img.save(img_buffer, format='JPEG')
                img_buffer.seek(0)
                
                img_obj = Image(img_buffer, width=4*inch, height=3*inch)
                story.append(img_obj)
                story.append(Spacer(1, 0.2*inch))
            except Exception as e:
                pass
        
        story.append(Paragraph("Финальные рекомендации", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        if recommendations:
            for line in recommendations.split('\n'):
                cleaned_line = clean_text_for_pdf(line)
                if cleaned_line:
                    story.append(Paragraph(cleaned_line, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        story.append(PageBreak())
        
        story.append(Paragraph("Список покупок", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        if shopping_list:
            for line in shopping_list.split('\n'):
                cleaned_line = clean_text_for_pdf(line)
                if cleaned_line:
                    story.append(Paragraph(cleaned_line, normal_style))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        raise Exception(f"Ошибка при генерации PDF: {str(e)}")

def track_achievement(user_id: str, achievement_type: str, target_count: int = None):
    """Track and unlock achievements when milestones are reached.
    
    Args:
        user_id: User ID
        achievement_type: Type of achievement (e.g., 'first_project', 'projects_3', etc)
        target_count: Optional target count for milestone achievements
    
    Returns:
        Tuple (is_newly_unlocked, current_count)
    """
    from database import SessionLocal, Achievement
    from datetime import datetime
    
    try:
        db = SessionLocal()
        
        achievement = db.query(Achievement).filter(
            Achievement.user_id == user_id,
            Achievement.achievement_type == achievement_type
        ).first()
        
        if not achievement:
            achievement = Achievement(
                user_id=user_id,
                achievement_type=achievement_type,
                count=1,
                unlocked=None
            )
            db.add(achievement)
        else:
            achievement.count += 1
        
        current_count = achievement.count
        is_newly_unlocked = False
        
        if target_count and current_count >= target_count and not achievement.unlocked:
            achievement.unlocked = 'yes'
            achievement.unlocked_at = datetime.utcnow()
            is_newly_unlocked = True
        
        db.commit()
        db.close()
        
        return is_newly_unlocked, current_count
    except Exception as e:
        print(f"Error tracking achievement: {e}")
        return False, 0

def get_achievement_details(user_id: str, achievement_type: str):
    """Get achievement details for display.
    
    Returns:
        Dict with title, description, icon, target_count, current_count, unlocked
    """
    from database import SessionLocal, Achievement
    
    db = SessionLocal()
    
    achievement_data = {
        'first_project': {
            'title': '🎯 Первый проект',
            'description': 'Создал свой первый дизайн-проект',
            'icon': '🎯',
            'target': 1
        },
        'projects_3': {
            'title': '🌟 Триумф трёх проектов',
            'description': 'Создал 3 дизайн-проекта',
            'icon': '🌟',
            'target': 3
        },
        'generations_5': {
            'title': '✨ Мастер вариаций',
            'description': 'Сгенерировал 5 вариантов дизайна',
            'icon': '✨',
            'target': 5
        },
        'all_styles': {
            'title': '🎨 Универсал стилей',
            'description': 'Использовал все доступные стили дизайна',
            'icon': '🎨',
            'target': 1
        },
        'pdf_3': {
            'title': '📄 Коллекционер PDF',
            'description': 'Экспортировал в PDF 3 раза',
            'icon': '📄',
            'target': 3
        },
        'edits_3': {
            'title': '✏️ Перфекционист',
            'description': 'Отредактировал промпт 3 раза',
            'icon': '✏️',
            'target': 3
        }
    }
    
    achievement = db.query(Achievement).filter(
        Achievement.user_id == user_id,
        Achievement.achievement_type == achievement_type
    ).first()
    
    data = achievement_data.get(achievement_type, {
        'title': achievement_type,
        'description': 'Достижение',
        'icon': '🏆',
        'target': 1
    })
    
    if achievement:
        data['current'] = achievement.count
        data['unlocked'] = achievement.unlocked == 'yes'
        data['progress'] = min(100, int((achievement.count / data['target']) * 100))
    else:
        data['current'] = 0
        data['unlocked'] = False
        data['progress'] = 0
    
    db.close()
    return data
