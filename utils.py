import base64
from openai import OpenAI

def encode_image(uploaded_file):
    """Конвертирует загруженный файл в base64"""
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def call_gpt4o_vision(client: OpenAI, system_prompt: str, user_text: str, image_base64: str) -> str:
    """Вызов GPT-4o Vision для анализа изображения"""
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
            max_tokens=2000,
            temperature=0.7
        )
        return response.choices[0].message.content
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
