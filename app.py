import streamlit as st
import base64
from PIL import Image
import io
from prompts import SYSTEM_PROMPT_ANALYZER, SYSTEM_PROMPT_BANANA_ENGINEER, SYSTEM_PROMPT_REFINE_ENGINEER
from utils import encode_image, call_gemini_vision, call_gemini_vision_markdown, call_gemini, generate_image, refine_design_with_vision, generate_design_project_pdf, create_before_after_comparison
import os
import json
from dotenv import load_dotenv
from database import SessionLocal, Project, DesignVariant, Recommendation, init_db
from datetime import datetime, timedelta

def get_moscow_time():
    """Возвращает текущее время по Москве (UTC+3)"""
    return datetime.utcnow() + timedelta(hours=3)

load_dotenv()

try:
    init_db()
except Exception as e:
    st.warning(f"⚠️ База данных недоступна: {str(e)}. Функции сохранения проектов могут не работать.")

st.set_page_config(
    page_title="AI-Дизайнер по ремонту",
    page_icon="🏠",
    layout="wide"
)

theme_css = ""
if st.session_state.get('theme') == 'light':
    theme_css = """
    .stApp {
        background-color: #ffffff;
        color: #1f1f1f;
    }
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    [data-testid="stMarkdownContainer"] {
        color: #1f1f1f;
    }
    header[data-testid="stHeader"] {
        background-color: #ffffff !important;
    }
    [data-testid="stHeader"] {
        background-color: #ffffff !important;
    }
    .stToolbar {
        background-color: #ffffff !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #1f1f1f !important;
    }
    .stTextInput input, .stTextArea textarea {
        background-color: #ffffff !important;
        color: #1f1f1f !important;
        border: 1px solid #d0d0d0 !important;
    }
    .stSelectbox select, .stMultiSelect, [data-testid="stMultiSelect"] {
        background-color: #ffffff !important;
        color: #1f1f1f !important;
    }
    [data-testid="stSelectbox"] div {
        background-color: #ffffff !important;
        color: #1f1f1f !important;
    }
    [data-testid="stSelectbox"] {
        background-color: #ffffff !important;
        color: #1f1f1f !important;
    }
    .stSelectbox [data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #1f1f1f !important;
    }
    .stSelectbox [data-baseweb="select"] div {
        background-color: #ffffff !important;
        color: #1f1f1f !important;
    }
    [data-baseweb="input"] {
        background-color: #ffffff !important;
        color: #1f1f1f !important;
    }
    [data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #1f1f1f !important;
    }
    [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #1f1f1f !important;
    }
    [data-baseweb="popover"] {
        background-color: #ffffff !important;
    }
    [data-baseweb="popover"] > div {
        background-color: #ffffff !important;
    }
    [role="listbox"] {
        background-color: #ffffff !important;
        color: #1f1f1f !important;
    }
    [role="option"] {
        background-color: #ffffff !important;
        color: #1f1f1f !important;
    }
    [role="option"]:hover {
        background-color: #e8e8e8 !important;
        color: #1f1f1f !important;
    }
    .stButton button {
        color: #1f1f1f !important;
        background-color: #ffffff !important;
        border: 1px solid #ddd !important;
    }
    button {
        color: #1f1f1f !important;
    }
    button:not([kind="primary"]):not([class*="primary"]) {
        color: #1f1f1f !important;
    }
    .stButton button[kind="primary"], button[kind="primary"] {
        color: #ffffff !important;
        background-color: #1f77b4 !important;
        border: none !important;
        font-weight: 700 !important;
    }
    .stButton button[kind="secondary"] {
        color: #1f1f1f !important;
        background-color: #f0f0f0 !important;
        border: 1px solid #d0d0d0 !important;
    }
    [data-testid="stColorBlock"] {
        border: 1px solid #d0d0d0 !important;
        border-radius: 4px !important;
    }
    [data-testid="stFileUploadDropzone"] {
        background-color: #f8f9fa !important;
        border: 2px dashed #d0d0d0 !important;
        color: #1f1f1f !important;
    }
    [data-testid="stFileUploadDropzone"] > div {
        background-color: #f8f9fa !important;
        color: #1f1f1f !important;
    }
    [data-testid="stFileUploadDropzone"] > div > div {
        background-color: #f8f9fa !important;
        color: #1f1f1f !important;
    }
    .stFileUploadDropzone {
        background-color: #f8f9fa !important;
        border-color: #d0d0d0 !important;
        color: #1f1f1f !important;
    }
    .stFileUploadDropzone div {
        background-color: #f8f9fa !important;
        color: #1f1f1f !important;
    }
    [data-testid="stFileUploadDropzone"] p, [data-testid="stFileUploadDropzone"] span {
        color: #1f1f1f !important;
    }
    .stFileUploadDropzone p, .stFileUploadDropzone span {
        color: #1f1f1f !important;
    }
    input[type="color"], [data-testid="stColorPicker"] {
        background-color: #ffffff !important;
        width: 60px !important;
        height: 40px !important;
        border: 2px solid #d0d0d0 !important;
        cursor: pointer !important;
        border-radius: 4px !important;
    }
    [data-testid="stColorPicker"] {
        background-color: #ffffff !important;
    }
    [data-testid="stColorPicker"] input {
        background-color: #ffffff !important;
        border: 2px solid #d0d0d0 !important;
    }
    .stColorPicker input {
        background-color: #ffffff !important;
        border: 2px solid #d0d0d0 !important;
    }
    """

st.markdown(f"""
<style>
{theme_css}
.stButton>button {{
    width: 100%;
    border-radius: 8px;
    height: 3em;
    font-weight: 600;
}}
.main .block-container {{
    max-width: 1400px;
    padding: 2rem;
}}
h1 {{
    margin-bottom: 2rem;
}}
.uploaded-image {{
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}}
.generated-image {{
    border-radius: 12px;
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    margin-bottom: 1rem;
}}
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
if 'saved_shopping_list' not in st.session_state:
    st.session_state.saved_shopping_list = None
if 'saved_budget' not in st.session_state:
    st.session_state.saved_budget = {}
if 'last_selected_project' not in st.session_state:
    st.session_state.last_selected_project = None
if 'auto_save_enabled' not in st.session_state:
    st.session_state.auto_save_enabled = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

def get_design_image_bytes(design_url: str) -> bytes:
    """Вспомогательная функция для извлечения байтов изображения из URL"""
    if design_url.startswith('data:image'):
        header, encoded = design_url.split(',', 1)
        return base64.b64decode(encoded)
    else:
        import requests
        response = requests.get(design_url, timeout=10)
        return response.content

def auto_save_project():
    if not st.session_state.auto_save_enabled or not st.session_state.analysis or not st.session_state.user_id:
        return
    
    db = SessionLocal()
    try:
        moscow_time = get_moscow_time()
        project_name = f"Проект {moscow_time.strftime('%d.%m.%Y %H:%M')}"
        if st.session_state.current_project_id:
            project = db.query(Project).filter(
                Project.id == st.session_state.current_project_id,
                Project.user_id == st.session_state.user_id
            ).first()
            if project:
                project.room_type = st.session_state.room_type
                project.purpose = st.session_state.purpose
                project.analysis = st.session_state.analysis
                project.uploaded_image_b64 = st.session_state.uploaded_image_b64
                project.updated_at = moscow_time
                
                db.query(DesignVariant).filter(DesignVariant.project_id == project.id).delete()
        else:
            project = Project(
                name=project_name,
                user_id=st.session_state.user_id,
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
        
        if st.session_state.saved_recommendations or st.session_state.saved_shopping_list or st.session_state.get('saved_budget'):
            existing_rec = db.query(Recommendation).filter(Recommendation.project_id == project.id).first()
            budget_json = json.dumps(st.session_state.get('saved_budget', {})) if st.session_state.get('saved_budget') else None
            if existing_rec:
                if st.session_state.saved_recommendations:
                    existing_rec.content = st.session_state.saved_recommendations
                if st.session_state.saved_shopping_list:
                    existing_rec.shopping_list = st.session_state.saved_shopping_list
                if budget_json:
                    existing_rec.budget_data = budget_json
            else:
                rec = Recommendation(
                    project_id=project.id,
                    content=st.session_state.saved_recommendations or "",
                    shopping_list=st.session_state.saved_shopping_list,
                    budget_data=budget_json
                )
                db.add(rec)
        
        db.commit()
    except Exception as e:
        print(f"Ошибка при автосохранении: {e}")
        db.rollback()
    finally:
        db.close()

st.title("🏠 AI-Дизайнер по ремонту")

if not st.session_state.user_id:
    st.markdown("### 👤 Вход в систему")
    st.markdown("Для работы с проектами введите ваше имя или логин")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        username_input = st.text_input("Ваше имя", placeholder="Введите имя или логин", key="username_input")
    with col2:
        st.write("")
        st.write("")
        if st.button("Войти", type="primary"):
            if username_input:
                st.session_state.user_id = username_input.lower().replace(" ", "_")
                st.session_state.username = username_input
                st.rerun()
            else:
                st.error("Введите имя для входа")
    
    st.stop()

col1, col2, col3 = st.columns([4, 1, 1])
with col1:
    st.markdown(f"**Пользователь:** {st.session_state.username}")
with col2:
    theme_icon = "🌙" if st.session_state.theme == 'light' else "☀️"
    if st.button(f"{theme_icon} Тема", key="theme_btn"):
        st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
        st.rerun()
with col3:
    if st.button("Выйти", key="logout_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

st.markdown("Загрузите фото помещения и получите профессиональный дизайн-проект")

with st.sidebar:
    st.header("📋 Управление проектами")
    
    db = SessionLocal()
    projects = db.query(Project).filter(Project.user_id == st.session_state.user_id).order_by(Project.updated_at.desc()).all()
    
    if projects:
        project_options = ["Новый проект"] + [f"{p.name} ({p.room_type})" for p in projects]
        
        default_index = 0
        if st.session_state.current_project_id:
            for i, p in enumerate(projects):
                if p.id == st.session_state.current_project_id:
                    default_index = i + 1
                    break
        
        selected_project = st.selectbox(
            "Выберите проект",
            project_options,
            index=default_index,
            key="project_selector"
        )
        
        if selected_project != st.session_state.last_selected_project:
            st.session_state.last_selected_project = selected_project
            
            if selected_project != "Новый проект":
                project_idx = project_options.index(selected_project) - 1
                project = projects[project_idx]
                
                if project.user_id != st.session_state.user_id:
                    st.error("⛔ Нет доступа к этому проекту")
                    st.stop()
                
                st.session_state.current_project_id = project.id
                st.session_state.room_type = project.room_type
                st.session_state.purpose = project.purpose
                st.session_state.analysis = project.analysis
                st.session_state.uploaded_image_b64 = project.uploaded_image_b64
                if project.uploaded_image_b64:
                    import base64
                    st.session_state.uploaded_image_bytes = base64.b64decode(project.uploaded_image_b64)
                st.session_state.auto_save_enabled = True
                
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
                    st.session_state.saved_shopping_list = recommendations.shopping_list
                    if recommendations.budget_data:
                        try:
                            st.session_state.saved_budget = json.loads(recommendations.budget_data)
                        except:
                            st.session_state.saved_budget = {}
                    else:
                        st.session_state.saved_budget = {}
                else:
                    st.session_state.saved_recommendations = None
                    st.session_state.saved_shopping_list = None
                    st.session_state.saved_budget = {}
                
                if len(st.session_state.images) > 0 and recommendations:
                    st.session_state.selected_variant_idx = 0
                else:
                    st.session_state.selected_variant_idx = None
                
                st.rerun()
            else:
                for key in ['current_project_id', 'room_type', 'purpose', 'analysis', 'uploaded_image_b64', 'uploaded_image_bytes', 'images', 'saved_recommendations', 'saved_shopping_list', 'selected_variant_idx']:
                    if key in st.session_state:
                        if key == 'images':
                            st.session_state[key] = []
                        else:
                            st.session_state[key] = None
                st.session_state.auto_save_enabled = False
                st.rerun()
    
    db.close()
    
    if st.session_state.current_project_id:
        st.divider()
        
        if st.button("🗑️ Удалить текущий проект", type="secondary", key="delete_project_btn"):
            st.session_state.confirm_delete = True
        
        if st.session_state.get('confirm_delete', False):
            st.warning("⚠️ Вы уверены? Это действие нельзя отменить!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Да, удалить", type="primary", key="confirm_delete_yes"):
                    db = SessionLocal()
                    try:
                        project = db.query(Project).filter(
                            Project.id == st.session_state.current_project_id,
                            Project.user_id == st.session_state.user_id
                        ).first()
                        if project:
                            db.delete(project)
                            db.commit()
                            st.success("✅ Проект удален")
                            for key in ['current_project_id', 'room_type', 'purpose', 'analysis', 
                                       'uploaded_image_b64', 'uploaded_image_bytes', 'images', 'saved_recommendations', 
                                       'saved_shopping_list', 'confirm_delete', 'auto_save_enabled']:
                                if key in st.session_state:
                                    if key == 'images':
                                        st.session_state[key] = []
                                    else:
                                        st.session_state[key] = None
                            st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(f"Ошибка при удалении: {str(e)}")
                    finally:
                        db.close()
            with col2:
                if st.button("❌ Отмена", key="confirm_delete_no"):
                    st.session_state.confirm_delete = False
                    st.rerun()
    
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
        help="Перетащите файл сюда или нажмите для выбора. Четкое, хорошо освещенное фото"
    )
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Загруженное фото", use_container_width=True)
        uploaded_file.seek(0)
        st.session_state.uploaded_image_bytes = uploaded_file.getvalue()
        st.session_state.uploaded_image_b64 = encode_image(uploaded_file)
    elif st.session_state.uploaded_image_b64:
        image_bytes = base64.b64decode(st.session_state.uploaded_image_b64)
        image = Image.open(io.BytesIO(image_bytes))
        st.image(image, caption="Загруженное фото", use_container_width=True)
    
    purpose = st.text_area(
        "Цель использования помещения",
        placeholder="Например: хочу уютное место для работы из дома с хорошим освещением",
        height=100
    )
    
    has_image = uploaded_file is not None or st.session_state.uploaded_image_b64 is not None
    analyze_button = st.button("🔍 Начать анализ", type="primary", disabled=not has_image)

if analyze_button and has_image:
    if st.session_state.analysis:
        st.session_state.analysis = None
        st.session_state.images = []
        st.session_state.selected_image_idx = None
        st.session_state.pop('selected_variant_idx', None)
        st.session_state.saved_recommendations = None
        st.session_state.saved_shopping_list = None
        st.session_state.current_project_id = None
    
    st.session_state.room_type = room_type
    st.session_state.purpose = purpose
    st.session_state.auto_save_enabled = True
    
    with st.spinner("🔍 Анализирую помещение..."):
        try:
            analysis = call_gemini_vision(
                SYSTEM_PROMPT_ANALYZER,
                f"Тип помещения: {room_type}\nЦель использования: {purpose}",
                st.session_state.uploaded_image_bytes
            )
            st.session_state.analysis = analysis
            auto_save_project()
        except Exception as e:
            st.error(f"Ошибка при анализе изображения: {str(e)}")
            st.error("Пожалуйста, попробуйте еще раз или проверьте ваш API ключ.")

if st.session_state.analysis:
    st.header("📊 Анализ вашего помещения")
    st.markdown(st.session_state.analysis)
    
    st.divider()
    
    st.header("🎨 Создание дизайн-проекта")
    
    col1, col2 = st.columns([2, 1])
    
    if 'selected_styles' not in st.session_state:
        st.session_state.selected_styles = []
    if 'selected_color' not in st.session_state:
        default_color = "#CCCCCC" if st.session_state.get('theme') == 'light' else "#FFFFFF"
        st.session_state.selected_color = default_color
    
    with col1:
        styles = st.multiselect(
            "Выберите стили (можно несколько)",
            ["Скандинавский", "Лофт", "Минимализм", "Современный", "Классический", "Эко", "Японский", "Прованс", "Нейтральный"],
            default=st.session_state.selected_styles,
            help="Выберите хотя бы один стиль для создания дизайна",
            key="styles_multiselect"
        )
        st.session_state.selected_styles = styles
    
    with col2:
        main_color = st.color_picker("Основной цвет", st.session_state.selected_color, key="color_select")
        st.session_state.selected_color = main_color
    
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
                    dalle_prompt = call_gemini(
                        SYSTEM_PROMPT_BANANA_ENGINEER,
                        f"""Room analysis:
{st.session_state.analysis}

Room type: {st.session_state.room_type}
Purpose: {st.session_state.purpose}
Styles: {', '.join(styles)}
Accent color: {main_color}
Additional preferences: {additional_preferences if additional_preferences else 'none'}

Create the prompt now.""",
                        return_json_key="prompt"
                    )
                    
                    image_url = generate_image(st.session_state.uploaded_image_bytes, dalle_prompt)
                    
                    st.session_state.images.append({
                        'url': image_url,
                        'prompt': dalle_prompt,
                        'iterations': 0
                    })
                    
                    auto_save_project()
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
                
                with st.expander("📝 Редактировать промпт", expanded=False):
                    edited_prompt = st.text_area(
                        "Промпт",
                        value=img_data['prompt'],
                        height=150,
                        key=f"prompt_edit_{idx}",
                        label_visibility="collapsed"
                    )
                    
                    if st.button("🔄 Перегенерировать", key=f"regen_{idx}", use_container_width=True):
                        with st.spinner("🎨 Генерирую новый вариант..."):
                            try:
                                design_image_bytes = get_design_image_bytes(img_data['url'])
                                new_image_url = generate_image(design_image_bytes, edited_prompt)
                                st.session_state.images.append({
                                    'url': new_image_url,
                                    'prompt': edited_prompt,
                                    'iterations': img_data['iterations'] + 1
                                })
                                auto_save_project()
                                st.success("✅ Новый вариант создан!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Ошибка: {str(e)}")
                
                st.divider()
                
                st.markdown("**🔧 Доработка естественным языком**")
                feedback = st.text_area(
                    "Опишите желаемые изменения",
                    placeholder="Например: сделать стены светлее, добавить больше растений, заменить диван на угловой",
                    height=100,
                    key=f"feedback_input_{idx}"
                )
                
                if st.button("🎨 Применить изменения", type="primary", key=f"apply_changes_{idx}", use_container_width=True):
                    if feedback:
                        with st.spinner("🎨 Анализирую дизайн и создаю улучшенную версию..."):
                            try:
                                refined_prompt = refine_design_with_vision(
                                    img_data['url'],
                                    img_data['prompt'],
                                    feedback,
                                    SYSTEM_PROMPT_REFINE_ENGINEER
                                )
                                
                                design_image_bytes = get_design_image_bytes(img_data['url'])
                                new_image_url = generate_image(design_image_bytes, refined_prompt)
                                
                                st.session_state.images.append({
                                    'url': new_image_url,
                                    'prompt': refined_prompt,
                                    'iterations': img_data['iterations'] + 1
                                })
                                
                                auto_save_project()
                                st.success("✅ Новый вариант создан!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Ошибка при доработке дизайна: {str(e)}")
                    else:
                        st.warning("Опишите желаемые изменения")
                
                st.divider()
                
                if st.button("✅ Выбрать этот дизайн", type="primary", key=f"select_{idx}", use_container_width=True):
                    selected_variant = st.session_state.images[idx]
                    st.session_state.images = [selected_variant]
                    st.session_state.selected_variant_idx = 0
                    st.session_state.saved_recommendations = None
                    st.session_state.saved_shopping_list = None
                    st.session_state.needs_generation = True
                    
                    if st.session_state.current_project_id:
                        db = SessionLocal()
                        try:
                            db.query(DesignVariant).filter(
                                DesignVariant.project_id == st.session_state.current_project_id
                            ).delete()
                            db.commit()
                        except Exception as e:
                            st.error(f"Ошибка удаления вариантов: {str(e)}")
                            db.rollback()
                        finally:
                            db.close()
                    
                    auto_save_project()
                    st.rerun()
            
            st.divider()
    
    if ('selected_variant_idx' in st.session_state and 
        st.session_state.selected_variant_idx is not None and 
        0 <= st.session_state.selected_variant_idx < len(st.session_state.images)):
        st.divider()
        st.header("📋 Финальные рекомендации")
        
        if st.session_state.get('needs_generation', False):
            st.session_state.needs_generation = False
            
            selected_design_url = st.session_state.images[st.session_state.selected_variant_idx]['url']
            design_image_bytes = get_design_image_bytes(selected_design_url)
            
            with st.spinner("📝 Формирую рекомендации..."):
                try:
                    recommendations = call_gemini_vision_markdown(
                        """Ты — эксперт по дизайну интерьеров и материалам отделки. 

⚡ КРИТИЧНО: НАЧНИ СРАЗУ СО СПИСКА РЕКОМЕНДАЦИЙ БЕЗ ВВЕДЕНИЯ!
Не пиши 'Я проанализировал', 'На основе анализа', 'Рассмотрев изображения' и подобные фразы.
Переходи прямо к рекомендациям — число 1, число 2, и т.д.

Тебе показаны два изображения: 1) исходное помещение, 2) финальный дизайн.
ВАЖНО: Рекомендуй ТОЛЬКО то, что реально изменилось при переходе от исходного к финальному дизайну.
Не советуй менять то, что не менялось.

Дай детальные рекомендации по материалам и отделке ТОЛЬКО для новых или измененных элементов:
1. Отделке стен (если она менялась)
2. Напольному покрытию (если оно менялось)
3. Потолку (если он менялся)
4. Мебели (конкретные рекомендации с размерами только для новой мебели)
5. Освещению (только для добавленных или замененных светильников)
6. Декору и аксессуарам (только для добавленных элементов)

Будь конкретным: указывай бренды, артикулы, примерные цены (в рублях).""",
                        f"""Тип помещения: {st.session_state.room_type}
Цель: {st.session_state.purpose}

Анализ исходного помещения:
{st.session_state.analysis}

ПЕРВОЕ ИЗОБРАЖЕНИЕ (слева): исходное помещение
ВТОРОЕ ИЗОБРАЖЕНИЕ (справа): финальный дизайн

Сравни эти два изображения и дай рекомендации ТОЛЬКО по измененным элементам.""",
                        design_image_bytes,
                        st.session_state.uploaded_image_bytes
                    )
                    st.session_state.saved_recommendations = recommendations
                    st.session_state.needs_generation = False
                    auto_save_project()
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка при генерации рекомендаций: {str(e)}")
                    st.warning("Попробуйте нажать кнопку 'Обновить рекомендации' ниже для повторной генерации")
        
        st.subheader("💡 Детальные рекомендации по материалам")
        if st.session_state.saved_recommendations:
            st.markdown(st.session_state.saved_recommendations)
        
        if st.button("📝 Обновить рекомендации", key="get_recommendations"):
            selected_design_url = st.session_state.images[st.session_state.selected_variant_idx]['url']
            design_image_bytes = get_design_image_bytes(selected_design_url)
            
            with st.spinner("📝 Формирую рекомендации..."):
                try:
                    recommendations = call_gemini_vision_markdown(
                        """Ты — эксперт по дизайну интерьеров и материалам отделки. 

⚡ КРИТИЧНО: НАЧНИ СРАЗУ СО СПИСКА РЕКОМЕНДАЦИЙ БЕЗ ВВЕДЕНИЯ!
Не пиши 'Я проанализировал', 'На основе анализа', 'Рассмотрев изображения' и подобные фразы.
Переходи прямо к рекомендациям — число 1, число 2, и т.д.

Тебе показаны два изображения: 1) исходное помещение, 2) финальный дизайн.
ВАЖНО: Рекомендуй ТОЛЬКО то, что реально изменилось при переходе от исходного к финальному дизайну.
Не советуй менять то, что не менялось.

Дай детальные рекомендации по материалам и отделке ТОЛЬКО для новых или измененных элементов:
1. Отделке стен (если она менялась)
2. Напольному покрытию (если оно менялось)
3. Потолку (если он менялся)
4. Мебели (конкретные рекомендации с размерами только для новой мебели)
5. Освещению (только для добавленных или замененных светильников)
6. Декору и аксессуарам (только для добавленных элементов)

Будь конкретным: указывай бренды, артикулы, примерные цены (в рублях).""",
                        f"""Тип помещения: {st.session_state.room_type}
Цель: {st.session_state.purpose}

Анализ исходного помещения:
{st.session_state.analysis}

ПЕРВОЕ ИЗОБРАЖЕНИЕ (слева): исходное помещение
ВТОРОЕ ИЗОБРАЖЕНИЕ (справа): финальный дизайн

Сравни эти два изображения и дай рекомендации ТОЛЬКО по измененным элементам.""",
                        design_image_bytes,
                        st.session_state.uploaded_image_bytes
                    )
                    
                    st.session_state.saved_recommendations = recommendations
                    auto_save_project()
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка при формировании рекомендаций: {str(e)}")
                    st.error("Пожалуйста, попробуйте еще раз или проверьте ваш API ключ.")
        
        st.divider()
        st.header("🛒 Список покупок")
        
        if st.session_state.saved_shopping_list:
            st.markdown(st.session_state.saved_shopping_list)
        
        if st.button("📝 Создать список покупок", key="generate_shopping_list"):
            selected_design_url = st.session_state.images[st.session_state.selected_variant_idx]['url']
            design_image_bytes = get_design_image_bytes(selected_design_url)
            
            with st.spinner("🛒 Создаю список покупок..."):
                try:
                    shopping_list = call_gemini_vision_markdown(
                        """Ты — эксперт по закупкам материалов для ремонта. 

⚡ КРИТИЧНО: НАЧНИ СРАЗУ СО СПИСКА ПОКУПОК БЕЗ ВВЕДЕНИЯ!
Не пиши 'Я проанализировал', 'На основе анализа', 'Рассмотрев изображения' и подобные фразы.
Переходи прямо к категориям и товарам.

Тебе показаны два изображения: 1) исходное помещение, 2) финальный дизайн.
ВАЖНО: Создай список покупок ТОЛЬКО для того, что реально изменилось при переходе от исходного к финальному дизайну.
Не включай в список то, что не менялось и уже было в помещении.

Создай детальный список покупок ТОЛЬКО ДЛЯ НОВЫХ или ЗАМЕНЕННЫХ элементов с:
1. Категориями (Отделка стен, Пол, Потолок, Мебель, Освещение, Декор)
2. Для каждого товара укажи:
   - Конкретное название товара и артикул (если возможно)
   - Описание
   - Количество
   - Примерная цена в рублях

Формат ответа:
### Категория
1. **Название товара (артикул)** - описание
   - Количество: X шт/м²/л
   - Цена: ~X руб""",
                        f"""Тип помещения: {st.session_state.room_type}

Рекомендации по материалам:
{st.session_state.saved_recommendations if st.session_state.saved_recommendations else 'Используй анализ изображения'}

ПЕРВОЕ ИЗОБРАЖЕНИЕ (слева): исходное помещение
ВТОРОЕ ИЗОБРАЖЕНИЕ (справа): финальный дизайн

Сравни эти два изображения и создай список покупок ТОЛЬКО для измененных элементов.""",
                        design_image_bytes,
                        st.session_state.uploaded_image_bytes
                    )
                    st.session_state.saved_shopping_list = shopping_list
                    auto_save_project()
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка при создании списка: {str(e)}")
        
        st.divider()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📥 Экспортировать в PDF", type="primary", key="export_pdf", use_container_width=True):
                try:
                    if not st.session_state.saved_recommendations or not st.session_state.saved_shopping_list:
                        st.error("❌ Сначала создайте рекомендации и список покупок")
                    else:
                        with st.spinner("📄 Генерирую PDF..."):
                            design_url = st.session_state.images[st.session_state.selected_variant_idx]['url']
                            pdf_bytes = generate_design_project_pdf(
                                st.session_state.room_type,
                                st.session_state.saved_recommendations,
                                st.session_state.saved_shopping_list,
                                design_url
                            )
                            
                            moscow_time = get_moscow_time()
                            filename = f"design_project_{moscow_time.strftime('%d_%m_%Y_%H_%M')}.pdf"
                            
                            st.download_button(
                                label="💾 Скачать PDF",
                                data=pdf_bytes,
                                file_name=filename,
                                mime="application/pdf",
                                key="pdf_download"
                            )
                            st.success("✅ PDF готов к скачиванию!")
                except Exception as e:
                    st.error(f"Ошибка при экспорте: {str(e)}")
