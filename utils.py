import base64
import json
import os
from openai import OpenAI
from google import genai
from google.genai import types

def encode_image(uploaded_file):
    """Конвертирует загруженный файл в base64"""
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def call_gemini_vision(system_prompt: str, user_text: str, image_bytes: bytes) -> str:
    """Вызов Gemini Pro Vision для анализа изображения. Возвращает только поле 'analysis' из JSON-ответа."""
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        full_prompt = f"""{system_prompt}

{user_text}

ВАЖНО: Верни ответ в JSON формате:
{{
  "reasoning": "твои внутренние рассуждения и анализ",
  "analysis": "финальный анализ в формате Markdown для пользователя"
}}"""
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
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

def call_gpt4o_vision(client: OpenAI, system_prompt: str, user_text: str, image_base64: str) -> str:
    """Вызов GPT-4o Vision для анализа изображения. Возвращает только поле 'analysis' из JSON-ответа."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=2000,
            temperature=0.7
        )
        
        raw_content = response.choices[0].message.content
        
        if not raw_content:
            raise Exception("Пустой ответ от GPT-4o Vision")
        
        try:
            parsed_json = json.loads(raw_content)
            if "analysis" in parsed_json:
                return parsed_json["analysis"]
            else:
                return raw_content
        except json.JSONDecodeError:
            return raw_content
            
    except Exception as e:
        raise Exception(f"Ошибка GPT-4o Vision: {str(e)}")

def call_gpt4o(client: OpenAI, system_prompt: str, user_prompt: str) -> str:
    """Обычный вызов GPT-4o для текста"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Ошибка GPT-4o: {str(e)}")

def generate_image(client: OpenAI, prompt: str) -> str:
    """Генерация изображения через DALL-E 3"""
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1792",
            quality="hd",
            n=1
        )
        return response.data[0].url
    except Exception as e:
        raise Exception(f"Ошибка DALL-E 3: {str(e)}")
