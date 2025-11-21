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
