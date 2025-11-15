import streamlit as st
import base64
from openai import OpenAI
from PIL import Image
import io
from prompts import SYSTEM_PROMPT_ANALYZER, SYSTEM_PROMPT_DALLE_ENGINEER
from utils import encode_image, call_gpt4o_vision, call_gpt4o, generate_image
import os
from dotenv import load_dotenv
from database import SessionLocal, Project, DesignVariant, Recommendation, init_db
from datetime import datetime

load_dotenv()
init_db()

st.set_page_config(
    page_title="AI-Дизайнер по ремонту",
    page_icon="🏠",
    layout="wide"
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.markdown("""
<style>
.stButton>button {
    width: 100%;
    border-radius: 8px;
    height: 3em;
    font-weight: 600;
}
.main .block-container {
    max-width: 1400px;
    padding: 2rem;
}
h1 {
    color: #1f1f1f;
    margin-bottom: 2rem;
}
.uploaded-image {
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.generated-image {
    border-radius: 12px;
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

if 'analysis' not in st.session_state:
    st.session_state.analysis = None
if 'images' not in st.session_state:
    st.session_state.images = []
if 'selected_image_idx' not in st.session_state:
    st.session_state.selected_image_idx = None
if 'uploaded_image_b64' not in st.session_state:
    st.session_state.uploaded_image_b64 = None
if 'room_type' not in st.session_state:
    st.session_state.room_type = None
if 'purpose' not in st.session_state:
    st.session_state.purpose = ""
if 'current_project_id' not in st.session_state:
    st.session_state.current_project_id = None
if 'saved_recommendations' not in st.session_state:
    st.session_state.saved_recommendations = None

st.title("🏠 AI-Дизайнер по ремонту")
st.markdown("Загрузите фото помещения и получите профессиональный дизайн-проект")

with st.sidebar:
    st.header("📋 Управление проектами")
    
    db = SessionLocal()
    projects = db.query(Project).order_by(Project.updated_at.desc()).all()
    
    if projects:
        project_options = ["Новый проект"] + [f"{p.name} ({p.room_type})" for p in projects]
        selected_project = st.selectbox(
            "Выберите проект",
            project_options,
            key="project_selector"
        )
        
        if selected_project != "Новый проект":
            project_idx = project_options.index(selected_project) - 1
            if st.button("📂 Загрузить проект", key="load_project_btn"):
                project = projects[project_idx]
                st.session_state.current_project_id = project.id
                st.session_state.room_type = project.room_type
                st.session_state.purpose = project.purpose
                st.session_state.analysis = project.analysis
                st.session_state.uploaded_image_b64 = project.uploaded_image_b64
                
                variants = db.query(DesignVariant).filter(DesignVariant.project_id == project.id).all()
                st.session_state.images = [
                    {
                        'url': v.image_url,
                        'prompt': v.prompt,
                        'iterations': v.iterations
                    } for v in variants
                ]
                
                recommendations = db.query(Recommendation).filter(Recommendation.project_id == project.id).first()
                if recommendations:
                    st.session_state.saved_recommendations = recommendations.content
                
                st.success(f"Проект '{project.name}' загружен!")
                st.rerun()
    
    db.close()
    
    st.divider()
    st.header("📋 Исходные данные")
    
    room_type = st.selectbox(
        "Тип помещения",
        ["Комната", "Кухня", "Ванная", "Гостиная", "Спальня", "Детская", "Кабинет", "Прихожая"],
        key="room_type_select"
    )
    
    uploaded_file = st.file_uploader(
        "Загрузите фото помещения",
        type=["jpg", "jpeg", "png"],
        help="Четкое, хорошо освещенное фото"
    )
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Загруженное фото", use_container_width=True)
        st.session_state.uploaded_image_b64 = encode_image(uploaded_file)
    
    purpose = st.text_area(
        "Цель использования помещения",
        placeholder="Например: хочу уютное место для работы из дома с хорошим освещением",
        height=100
    )
    
    analyze_button = st.button("🔍 Начать анализ", type="primary", disabled=not uploaded_file)
    
    st.divider()
    
    if st.session_state.analysis:
        project_name = st.text_input("Название проекта", value=f"Проект {datetime.now().strftime('%d.%m.%Y')}")
        if st.button("💾 Сохранить проект", key="save_project_btn"):
            db = SessionLocal()
            try:
                if st.session_state.current_project_id:
                    project = db.query(Project).filter(Project.id == st.session_state.current_project_id).first()
                    project.name = project_name
                    project.room_type = st.session_state.room_type
                    project.purpose = st.session_state.purpose
                    project.analysis = st.session_state.analysis
                    project.uploaded_image_b64 = st.session_state.uploaded_image_b64
                    project.updated_at = datetime.utcnow()
                    
                    db.query(DesignVariant).filter(DesignVariant.project_id == project.id).delete()
                else:
                    project = Project(
                        name=project_name,
                        room_type=st.session_state.room_type,
                        purpose=st.session_state.purpose,
                        analysis=st.session_state.analysis,
                        uploaded_image_b64=st.session_state.uploaded_image_b64
                    )
                    db.add(project)
                    db.flush()
                    st.session_state.current_project_id = project.id
                
                for img_data in st.session_state.images:
                    variant = DesignVariant(
                        project_id=project.id,
                        image_url=img_data['url'],
                        prompt=img_data['prompt'],
                        iterations=img_data['iterations']
                    )
                    db.add(variant)
                
                if st.session_state.saved_recommendations:
                    db.query(Recommendation).filter(Recommendation.project_id == project.id).delete()
                    rec = Recommendation(
                        project_id=project.id,
                        content=st.session_state.saved_recommendations
                    )
                    db.add(rec)
                
                db.commit()
                st.success(f"Проект '{project_name}' сохранен!")
            except Exception as e:
                db.rollback()
                st.error(f"Ошибка при сохранении: {str(e)}")
            finally:
                db.close()
    
    st.divider()
    
    if st.button("🔄 Начать заново"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if analyze_button and uploaded_file:
    st.session_state.room_type = room_type
    st.session_state.purpose = purpose
    
    with st.spinner("🔍 Анализирую помещение..."):
        try:
            analysis = call_gpt4o_vision(
                client,
                SYSTEM_PROMPT_ANALYZER,
                f"Тип помещения: {room_type}\nЦель использования: {purpose}",
                st.session_state.uploaded_image_b64
            )
            st.session_state.analysis = analysis
        except Exception as e:
            st.error(f"Ошибка при анализе изображения: {str(e)}")
            st.error("Пожалуйста, попробуйте еще раз или проверьте ваш API ключ.")

if st.session_state.analysis:
    st.header("📊 Анализ вашего помещения")
    st.markdown(st.session_state.analysis)
    
    st.divider()
    
    st.header("🎨 Создание дизайн-проекта")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        styles = st.multiselect(
            "Выберите стили (можно несколько)",
            ["Скандинавский", "Лофт", "Минимализм", "Современный", "Классический", "Эко", "Японский", "Прованс"],
            default=["Скандинавский"]
        )
    
    with col2:
        main_color = st.color_picker("Основной цвет", "#FFFFFF")
    
    additional_preferences = st.text_input(
        "Дополнительные пожелания (опционально)",
        placeholder="Например: больше зелени, деревянные акценты"
    )
    
    generate_button = st.button("✨ Создать дизайн-проект", type="primary", key="generate_design")
    
    if generate_button:
        if not styles:
            st.error("Выберите хотя бы один стиль")
        else:
            with st.spinner("🎨 Создаю дизайн-проект..."):
                try:
                    dalle_prompt = call_gpt4o(
                        client,
                        SYSTEM_PROMPT_DALLE_ENGINEER,
                        f"""Анализ помещения:
{st.session_state.analysis}

Тип помещения: {st.session_state.room_type}
Цель: {st.session_state.purpose}
Стили: {', '.join(styles)}
Основной цвет: {main_color}
Дополнительно: {additional_preferences}

Создай детальный промпт для DALL-E 3."""
                    )
                    
                    image_url = generate_image(client, dalle_prompt)
                    
                    st.session_state.images.append({
                        'url': image_url,
                        'prompt': dalle_prompt,
                        'iterations': 0
                    })
                    
                    st.success("✅ Дизайн-проект создан!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка при создании дизайн-проекта: {str(e)}")
                    st.error("Пожалуйста, попробуйте еще раз или проверьте ваш API ключ.")

if st.session_state.images:
    st.divider()
    st.header("🖼️ Варианты дизайна")
    
    for idx, img_data in enumerate(st.session_state.images):
        with st.container():
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.image(img_data['url'], use_container_width=True)
            
            with col2:
                st.markdown(f"**Вариант {idx + 1}**")
                st.caption(f"Итераций: {img_data['iterations']}")
                
                with st.expander("📝 Промпт для генерации"):
                    st.text(img_data['prompt'])
                
                if st.button(f"🔧 Доработать этот вариант", key=f"refine_{idx}"):
                    st.session_state.selected_image_idx = idx
                    st.rerun()
            
            st.divider()
    
    if st.session_state.selected_image_idx is not None:
        idx = st.session_state.selected_image_idx
        current_img = st.session_state.images[idx]
        
        st.subheader(f"🔧 Доработка варианта {idx + 1}")
        
        feedback = st.text_area(
            "Что нужно изменить?",
            placeholder="Например: сделать стены светлее, добавить больше растений, заменить диван на угловой",
            height=100,
            key="feedback_input"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            refine_button = st.button("🎨 Применить изменения", type="primary", key="apply_changes")
        with col2:
            if st.button("❌ Отменить", key="cancel_refine"):
                st.session_state.selected_image_idx = None
                st.rerun()
        
        if refine_button and feedback:
            with st.spinner("🎨 Дорабатываю дизайн..."):
                try:
                    refined_prompt = call_gpt4o(
                        client,
                        SYSTEM_PROMPT_DALLE_ENGINEER,
                        f"""Исходный промпт:
{current_img['prompt']}

Фидбэк пользователя: {feedback}

Создай НОВЫЙ промпт для DALL-E 3, учитывая фидбэк. Ответь ТОЛЬКО промптом."""
                    )
                    
                    new_image_url = generate_image(client, refined_prompt)
                    
                    st.session_state.images.append({
                        'url': new_image_url,
                        'prompt': refined_prompt,
                        'iterations': current_img['iterations'] + 1
                    })
                    
                    st.session_state.selected_image_idx = None
                    
                    st.success("✅ Новый вариант создан!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка при доработке дизайна: {str(e)}")
                    st.error("Пожалуйста, попробуйте еще раз или проверьте ваш API ключ.")
    
    st.divider()
    st.header("📋 Финальные рекомендации")
    
    if st.session_state.saved_recommendations:
        st.markdown(st.session_state.saved_recommendations)
    
    if st.button("📝 Получить детальные рекомендации по материалам", key="get_recommendations"):
        with st.spinner("📝 Формирую рекомендации..."):
            try:
                recommendations = call_gpt4o(
                    client,
                    """Ты — эксперт по дизайну интерьеров и материалам отделки. 
На основе анализа и выбранного дизайна дай детальные рекомендации по:
1. Отделке стен (материалы, цвета, текстуры)
2. Напольному покрытию (тип, цвет, характеристики)
3. Потолку (отделка, освещение)
4. Мебели (конкретные рекомендации с размерами)
5. Освещению (типы светильников, расположение)
6. Декору и аксессуарам

Будь конкретным: указывай бренды, артикулы, примерные цены (в рублях).""",
                    f"""Тип помещения: {st.session_state.room_type}
Цель: {st.session_state.purpose}

Анализ:
{st.session_state.analysis}

Итоговый дизайн (промпт последнего варианта):
{st.session_state.images[-1]['prompt']}

Дай детальные рекомендации."""
                )
                
                st.session_state.saved_recommendations = recommendations
                st.markdown(recommendations)
            except Exception as e:
                st.error(f"Ошибка при формировании рекомендаций: {str(e)}")
                st.error("Пожалуйста, попробуйте еще раз или проверьте ваш API ключ.")
