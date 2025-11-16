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
from pdf_generator import generate_design_pdf

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
[data-testid="stFileUploader"] {
    min-height: auto;
}
[data-testid="stFileUploader"] section {
    padding: 1.5rem !important;
    min-height: auto !important;
}
[data-testid="stFileUploader"] section small {
    font-size: 0 !important;
}
[data-testid="stFileUploader"] section small::before {
    content: "Перетащите файл сюда или нажмите для выбора" !important;
    font-size: 0.9rem !important;
    display: block !important;
    text-align: center;
}
[data-testid="stFileUploader"] section small::after {
    content: "Макс. размер: 200MB" !important;
    font-size: 0.75rem !important;
    display: block !important;
    text-align: center;
    color: #999;
    margin-top: 0.25rem;
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
if 'saved_shopping_list' not in st.session_state:
    st.session_state.saved_shopping_list = None
if 'last_selected_project' not in st.session_state:
    st.session_state.last_selected_project = None
if 'auto_save_enabled' not in st.session_state:
    st.session_state.auto_save_enabled = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

def auto_save_project():
    if not st.session_state.auto_save_enabled or not st.session_state.analysis or not st.session_state.user_id:
        return
    
    db = SessionLocal()
    try:
        project_name = f"Проект {datetime.now().strftime('%d.%m.%Y %H:%M')}"
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
                project.updated_at = datetime.utcnow()
                
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
        
        if st.session_state.saved_recommendations or st.session_state.saved_shopping_list:
            existing_rec = db.query(Recommendation).filter(Recommendation.project_id == project.id).first()
            if existing_rec:
                existing_rec.content = st.session_state.saved_recommendations or existing_rec.content
                existing_rec.shopping_list = st.session_state.saved_shopping_list
            else:
                rec = Recommendation(
                    project_id=project.id,
                    content=st.session_state.saved_recommendations or "",
                    shopping_list=st.session_state.saved_shopping_list
                )
                db.add(rec)
        
        db.commit()
    except Exception as e:
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

col1, col2 = st.columns([5, 1])
with col1:
    st.markdown(f"**Пользователь:** {st.session_state.username}")
with col2:
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
        selected_project = st.selectbox(
            "Выберите проект",
            project_options,
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
                else:
                    st.session_state.saved_recommendations = None
                    st.session_state.saved_shopping_list = None
                
                st.rerun()
            else:
                for key in ['current_project_id', 'room_type', 'purpose', 'analysis', 'uploaded_image_b64', 'images', 'saved_recommendations']:
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
                                       'uploaded_image_b64', 'images', 'saved_recommendations', 
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
        st.session_state.uploaded_image_b64 = encode_image(uploaded_file)
    
    purpose = st.text_area(
        "Цель использования помещения",
        placeholder="Например: хочу уютное место для работы из дома с хорошим освещением",
        height=100
    )
    
    analyze_button = st.button("🔍 Начать анализ", type="primary", disabled=not uploaded_file)

if analyze_button and uploaded_file:
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
            analysis = call_gpt4o_vision(
                client,
                SYSTEM_PROMPT_ANALYZER,
                f"Тип помещения: {room_type}\nЦель использования: {purpose}",
                st.session_state.uploaded_image_b64
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
                                new_image_url = generate_image(client, edited_prompt)
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
                        with st.spinner("🎨 Дорабатываю дизайн..."):
                            try:
                                refined_prompt = call_gpt4o(
                                    client,
                                    SYSTEM_PROMPT_DALLE_ENGINEER,
                                    f"""Исходный промпт:
{img_data['prompt']}

Фидбэк пользователя: {feedback}

Создай НОВЫЙ промпт для DALL-E 3, учитывая фидбэк. Ответь ТОЛЬКО промптом."""
                                )
                                
                                new_image_url = generate_image(client, refined_prompt)
                                
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
    
    st.divider()
    st.header("📋 Выбор варианта и финальные рекомендации")
    
    if 'selected_variant_idx' not in st.session_state:
        st.session_state.selected_variant_idx = len(st.session_state.images) - 1
    
    st.markdown("### Выберите вариант для финальных рекомендаций:")
    selected_variant = st.selectbox(
        "Вариант дизайна",
        range(len(st.session_state.images)),
        index=st.session_state.selected_variant_idx,
        format_func=lambda x: f"Вариант {x + 1}",
        key="final_variant_selector"
    )
    st.session_state.selected_variant_idx = selected_variant
    
    st.image(st.session_state.images[selected_variant]['url'], use_container_width=True, caption=f"Вариант {selected_variant + 1}")
    
    st.divider()
    
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

Итоговый дизайн (промпт выбранного варианта):
{st.session_state.images[st.session_state.selected_variant_idx]['prompt']}

Дай детальные рекомендации."""
                )
                
                st.session_state.saved_recommendations = recommendations
                auto_save_project()
                st.markdown(recommendations)
            except Exception as e:
                st.error(f"Ошибка при формировании рекомендаций: {str(e)}")
                st.error("Пожалуйста, попробуйте еще раз или проверьте ваш API ключ.")
    
    st.divider()
    st.header("🛒 Список покупок")
    
    if st.session_state.saved_shopping_list:
        st.markdown(st.session_state.saved_shopping_list)
    
    if st.button("📝 Создать список покупок", key="generate_shopping_list"):
        with st.spinner("🛒 Создаю список покупок..."):
            try:
                shopping_list = call_gpt4o(
                    client,
                    """Ты — эксперт по закупкам материалов для ремонта. Создай детальный список покупок с:
1. Категориями (Отделка стен, Пол, Потолок, Мебель, Освещение, Декор)
2. Для каждого товара укажи:
   - Конкретное название товара и артикул (если возможно)
   - Описание
   - Количество
   - Примерная цена в рублях
   - Прямая ссылка на конкретный товар в онлайн-магазине (Леруа Мерлен, ИКЕА, Hoff, OBI, Wildberries, Ozon)
   
ВАЖНО: 
- Ссылки должны вести на конкретные товары, а не на главную страницу магазина
- Все ссылки ОБЯЗАТЕЛЬНО должны начинаться с https://
- Используй реальные товары из этих магазинов
- Формат ссылок: https://leroymerlin.ru/product/..., https://www.ikea.com/ru/..., и т.д.

Формат ответа:
### Категория
1. **Название товара (артикул)** - описание
   - Количество: X шт/м²/л
   - Цена: ~X руб
   - [Купить в магазине](прямая ссылка на товар)""",
                    f"""Тип помещения: {st.session_state.room_type}
Рекомендации:
{st.session_state.saved_recommendations if st.session_state.saved_recommendations else st.session_state.analysis}

Создай список покупок."""
                )
                st.session_state.saved_shopping_list = shopping_list
                auto_save_project()
                st.markdown(shopping_list)
            except Exception as e:
                st.error(f"Ошибка при создании списка: {str(e)}")
    
    st.divider()
    st.header("💰 Калькулятор бюджета")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Основные категории расходов")
        
        walls_budget = st.number_input("Отделка стен (руб)", min_value=0, value=50000, step=5000, key="budget_walls")
        floor_budget = st.number_input("Напольное покрытие (руб)", min_value=0, value=40000, step=5000, key="budget_floor")
        ceiling_budget = st.number_input("Потолок (руб)", min_value=0, value=30000, step=5000, key="budget_ceiling")
        furniture_budget = st.number_input("Мебель (руб)", min_value=0, value=100000, step=10000, key="budget_furniture")
        lighting_budget = st.number_input("Освещение (руб)", min_value=0, value=20000, step=5000, key="budget_lighting")
        decor_budget = st.number_input("Декор (руб)", min_value=0, value=15000, step=5000, key="budget_decor")
        work_budget = st.number_input("Работы (руб)", min_value=0, value=80000, step=10000, key="budget_work")
    
    with col2:
        st.markdown("### Итоговый бюджет")
        total_budget = walls_budget + floor_budget + ceiling_budget + furniture_budget + lighting_budget + decor_budget + work_budget
        st.metric("Общая сумма", f"{total_budget:,.0f} руб")
        st.metric("С запасом (+ 15%)", f"{total_budget * 1.15:,.0f} руб")
        
        st.markdown("### Распределение по категориям")
        st.progress(walls_budget / total_budget if total_budget > 0 else 0, text=f"Стены: {walls_budget / total_budget * 100:.1f}%" if total_budget > 0 else "Стены: 0%")
        st.progress(floor_budget / total_budget if total_budget > 0 else 0, text=f"Пол: {floor_budget / total_budget * 100:.1f}%" if total_budget > 0 else "Пол: 0%")
        st.progress(furniture_budget / total_budget if total_budget > 0 else 0, text=f"Мебель: {furniture_budget / total_budget * 100:.1f}%" if total_budget > 0 else "Мебель: 0%")
        st.progress(work_budget / total_budget if total_budget > 0 else 0, text=f"Работы: {work_budget / total_budget * 100:.1f}%" if total_budget > 0 else "Работы: 0%")
    
    st.divider()
    st.header("📄 Экспорт дизайн-проекта")
    
    try:
        project_data = {
            'name': st.session_state.get('current_project_id', f"Проект {datetime.now().strftime('%d.%m.%Y')}"),
            'room_type': st.session_state.room_type,
            'purpose': st.session_state.purpose,
            'analysis': st.session_state.analysis,
            'selected_variant': st.session_state.images[st.session_state.selected_variant_idx],
            'recommendations': st.session_state.saved_recommendations,
            'created_at': datetime.now().strftime('%d.%m.%Y')
        }
        
        pdf_buffer = generate_design_pdf(project_data)
        
        st.download_button(
            label="📥 Скачать PDF-отчет",
            data=pdf_buffer,
            file_name=f"dizain_proekt_{datetime.now().strftime('%d_%m_%Y')}.pdf",
            mime="application/pdf",
            key="download_pdf_btn",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Ошибка при создании PDF: {str(e)}")
