from pathlib import Path
from datetime import datetime
from html import escape

import joblib
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


try:
    from src.rag_chat import get_rag_answer
    RAG_AVAILABLE = True
except Exception:
    RAG_AVAILABLE = False


st.set_page_config(
    page_title="CardioCare AI - Tư vấn tim mạch",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="collapsed"
)


BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "assets"


def html_block(html: str):
    st.markdown(html.strip(), unsafe_allow_html=True)


def load_css():
    css_path = ASSET_DIR / "clinic_theme.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True
        )
    else:
        st.warning("Chưa tìm thấy file CSS: assets/clinic_theme.css")


def load_js():
    js_path = ASSET_DIR / "clinic_interactions.js"
    if js_path.exists():
        js_code = js_path.read_text(encoding="utf-8")
        components.html(f"<script>{js_code}</script>", height=0)


load_css()
load_js()


FIELD_CONFIG = {
    "age": {
        "label": "Tuổi",
        "simple": "Tuổi hiện tại của người cần đánh giá.",
        "type": "number",
        "default": 50,
        "min": 1,
        "max": 120,
        "step": 1,
        "unit": "tuổi",
        "help": "Tuổi càng cao thì nguy cơ bệnh tim mạch thường tăng."
    },
    "sex": {
        "label": "Giới tính",
        "simple": "Giới tính sinh học được dùng trong mô hình dự đoán.",
        "type": "select",
        "default": 1,
        "options": {1: "Nam", 0: "Nữ"},
        "help": "Nam và nữ có nguy cơ tim mạch khác nhau theo từng nhóm tuổi."
    },
    "cp": {
        "label": "Loại đau ngực",
        "simple": "Mô tả kiểu đau hoặc khó chịu ở ngực.",
        "type": "select",
        "default": 0,
        "options": {
            0: "Đau thắt ngực điển hình",
            1: "Đau thắt ngực không điển hình",
            2: "Đau ngực không giống bệnh tim",
            3: "Không rõ hoặc không có triệu chứng"
        },
        "help": "Nếu đau ngực khi gắng sức, giảm khi nghỉ, nên chú ý bệnh mạch vành."
    },
    "trestbps": {
        "label": "Huyết áp lúc nghỉ",
        "simple": "Chỉ số huyết áp đo khi cơ thể đang nghỉ ngơi.",
        "type": "number",
        "default": 120,
        "min": 60,
        "max": 250,
        "step": 1,
        "unit": "mmHg",
        "help": "Huyết áp cao kéo dài làm tăng nguy cơ đột quỵ, suy tim và bệnh mạch vành."
    },
    "chol": {
        "label": "Cholesterol",
        "simple": "Lượng cholesterol trong máu.",
        "type": "number",
        "default": 200,
        "min": 80,
        "max": 700,
        "step": 1,
        "unit": "mg/dL",
        "help": "Cholesterol cao có thể làm tăng nguy cơ xơ vữa động mạch."
    },
    "fbs": {
        "label": "Đường huyết lúc đói",
        "simple": "Đánh giá đường máu sau khi nhịn ăn.",
        "type": "select",
        "default": 0,
        "options": {
            0: "Bình thường hoặc ≤ 120 mg/dL",
            1: "Cao hơn 120 mg/dL"
        },
        "help": "Đường huyết cao liên quan đến đái tháo đường và nguy cơ tim mạch."
    },
    "restecg": {
        "label": "Điện tâm đồ lúc nghỉ",
        "simple": "Kết quả điện tâm đồ khi cơ thể đang nghỉ.",
        "type": "select",
        "default": 0,
        "options": {
            0: "Bình thường",
            1: "Có bất thường ST-T",
            2: "Có dấu hiệu phì đại thất trái"
        },
        "help": "Điện tâm đồ giúp phát hiện rối loạn nhịp, thiếu máu cơ tim hoặc bất thường tim."
    },
    "thalach": {
        "label": "Nhịp tim tối đa",
        "simple": "Nhịp tim cao nhất đạt được khi vận động hoặc test gắng sức.",
        "type": "number",
        "default": 150,
        "min": 50,
        "max": 250,
        "step": 1,
        "unit": "bpm",
        "help": "Nhịp tim tối đa thấp bất thường có thể cần được bác sĩ đánh giá thêm."
    },
    "exang": {
        "label": "Đau ngực khi vận động",
        "simple": "Có bị đau thắt ngực khi đi bộ nhanh, leo cầu thang hoặc gắng sức không.",
        "type": "select",
        "default": 0,
        "options": {0: "Không", 1: "Có"},
        "help": "Đau ngực khi vận động là dấu hiệu cần chú ý trong bệnh mạch vành."
    },
    "oldpeak": {
        "label": "Độ chênh ST",
        "simple": "Thông số trên điện tâm đồ khi gắng sức.",
        "type": "number",
        "default": 1.0,
        "min": 0.0,
        "max": 10.0,
        "step": 0.1,
        "unit": "",
        "help": "Nếu không có kết quả này, có thể giữ mặc định."
    },
    "slope": {
        "label": "Độ dốc đoạn ST",
        "simple": "Dạng biến đổi đoạn ST trên điện tâm đồ.",
        "type": "select",
        "default": 1,
        "options": {0: "Dốc lên", 1: "Phẳng", 2: "Dốc xuống"},
        "help": "Đoạn ST bất thường có thể liên quan thiếu máu cơ tim."
    },
    "ca": {
        "label": "Số mạch chính bị ảnh hưởng",
        "simple": "Số mạch vành chính ghi nhận bất thường nếu đã có chụp mạch.",
        "type": "select",
        "default": 0,
        "options": {0: "0 mạch", 1: "1 mạch", 2: "2 mạch", 3: "3 mạch", 4: "4 mạch"},
        "help": "Nếu chưa từng chụp mạch vành, có thể chọn 0."
    },
    "thal": {
        "label": "Kết quả Thal",
        "simple": "Một thông số từ dữ liệu kiểm tra tim mạch gốc.",
        "type": "select",
        "default": 2,
        "options": {
            0: "Không rõ / không ghi nhận",
            1: "Bình thường",
            2: "Khiếm khuyết cố định",
            3: "Khiếm khuyết có thể hồi phục"
        },
        "help": "Nếu không có thông tin, chọn Không rõ / không ghi nhận."
    }
}


DEFAULT_FEATURES = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal"
]


DEMO_PRESETS = {
    "low": {
        "age": 35, "sex": 0, "cp": 2, "trestbps": 115, "chol": 175,
        "fbs": 0, "restecg": 0, "thalach": 170, "exang": 0,
        "oldpeak": 0.2, "slope": 0, "ca": 0, "thal": 1
    },
    "medium": {
        "age": 52, "sex": 1, "cp": 1, "trestbps": 135, "chol": 220,
        "fbs": 0, "restecg": 1, "thalach": 140, "exang": 0,
        "oldpeak": 1.2, "slope": 1, "ca": 1, "thal": 2
    },
    "high": {
        "age": 66, "sex": 1, "cp": 3, "trestbps": 155, "chol": 275,
        "fbs": 1, "restecg": 1, "thalach": 110, "exang": 1,
        "oldpeak": 2.8, "slope": 2, "ca": 2, "thal": 3
    }
}


HEART_INFO = [
    {
        "title": "Đau ngực khi nào cần chú ý?",
        "icon": "⚠️",
        "tag": "Dấu hiệu cảnh báo",
        "content": "Đau ngực kéo dài, đau lan tay trái, hàm, lưng, kèm khó thở, vã mồ hôi hoặc choáng là dấu hiệu cần được xử trí sớm."
    },
    {
        "title": "Tăng huyết áp có nguy hiểm không?",
        "icon": "🩸",
        "tag": "Huyết áp",
        "content": "Tăng huyết áp kéo dài có thể gây đột quỵ, suy tim, bệnh thận và bệnh mạch vành dù người bệnh không có triệu chứng rõ."
    },
    {
        "title": "Suy tim thường có dấu hiệu gì?",
        "icon": "🫀",
        "tag": "Suy tim",
        "content": "Khó thở khi gắng sức, phù chân, mệt nhiều, khó thở khi nằm và tăng cân nhanh do giữ nước là các dấu hiệu cần theo dõi."
    },
    {
        "title": "Đái tháo đường và tim mạch",
        "icon": "🍬",
        "tag": "Đường huyết",
        "content": "Người đái tháo đường có nguy cơ cao mắc bệnh mạch vành, suy tim, đột quỵ và bệnh động mạch ngoại vi."
    },
    {
        "title": "Ăn uống tốt cho tim",
        "icon": "🥗",
        "tag": "Dinh dưỡng",
        "content": "Nên giảm muối, hạn chế mỡ bão hòa, ăn nhiều rau xanh, cá, ngũ cốc nguyên hạt và kiểm soát cân nặng."
    },
    {
        "title": "Vận động an toàn",
        "icon": "🚶",
        "tag": "Lối sống",
        "content": "Vận động đều đặn giúp kiểm soát huyết áp, cân nặng, đường huyết và cholesterol. Người có triệu chứng nên hỏi bác sĩ trước khi tập."
    }
]


FAQ_DATA = [
    {
        "q": "Hệ thống này có thay thế bác sĩ không?",
        "a": "Không. Hệ thống chỉ hỗ trợ tham khảo và định hướng. Chẩn đoán và điều trị cần được thực hiện bởi bác sĩ hoặc cơ sở y tế."
    },
    {
        "q": "Nếu tôi đau ngực dữ dội thì có nên hỏi chatbot trước không?",
        "a": "Không nên trì hoãn. Nếu đau ngực dữ dội, kéo dài, lan tay trái/hàm/lưng, kèm khó thở, vã mồ hôi, choáng hoặc ngất, cần đi cấp cứu."
    },
    {
        "q": "Không biết chỉ số xét nghiệm thì nhập sao?",
        "a": "Bạn có thể giữ giá trị mặc định hoặc chọn 'không rõ'. Kết quả sẽ chỉ mang tính tham khảo hơn."
    },
    {
        "q": "Dự đoán nguy cơ cao có nghĩa là chắc chắn mắc bệnh không?",
        "a": "Không. Đây chỉ là kết quả mô hình học máy dựa trên dữ liệu đầu vào. Người dùng cần khám để xác định chính xác."
    }
]


PAGES = {
    "home": "Trang chính",
    "predict": "Dự đoán",
    "guide": "Hướng dẫn",
    "knowledge": "Kiến thức"
}


def init_state():
    if "page" not in st.session_state:
        st.session_state["page"] = "home"

    if "page_history" not in st.session_state:
        st.session_state["page_history"] = []

    if "floating_chat_messages" not in st.session_state:
        st.session_state["floating_chat_messages"] = [
            {
                "role": "assistant",
                "content": "Xin chào, mình là chatbot hỗ trợ thông tin tim mạch. Bạn muốn hỏi vấn đề gì?"
            }
        ]

    if "floating_chat_input_version" not in st.session_state:
        st.session_state["floating_chat_input_version"] = 0


def go_to(page):
    current_page = st.session_state.get("page", "home")
    if page != current_page:
        st.session_state["page_history"].append(current_page)
        st.session_state["page"] = page
        st.rerun()


def go_back():
    if st.session_state.get("page_history"):
        previous = st.session_state["page_history"].pop()
        st.session_state["page"] = previous
        st.rerun()


init_state()


@st.cache_resource
def load_artifacts():
    model = joblib.load("models/best_model.pkl")
    model_name = joblib.load("models/best_model_name.pkl")
    scaler = joblib.load("models/scaler.pkl")
    feature_names = joblib.load("models/feature_names.pkl")

    try:
        feature_names = list(feature_names)
    except Exception:
        feature_names = DEFAULT_FEATURES

    try:
        training_results = joblib.load("models/training_results.pkl")
    except Exception:
        training_results = []

    return model, model_name, scaler, feature_names, training_results


def safe_load_model():
    try:
        return load_artifacts(), None
    except FileNotFoundError as e:
        return None, f"Thiếu file mô hình: {e}"
    except Exception as e:
        return None, str(e)


def render_topbar():
    html_block(
        '<div class="topbar">'
            '<div class="topbar-left">'
                '<span>📧 contact@cardiocare.vn</span>'
                '<span>☎️ 1900 0000</span>'
                '<span>💬 Zalo: 0900 000 000</span>'
            '</div>'
            '<div class="topbar-right">'
                '<span>Facebook: CardioCare AI</span>'
            '</div>'
        '</div>'
    )


def render_header():
    html_block(
        '<div class="header-card">'
            '<div class="brand-row">'
                '<div class="brand-icon">🫀</div>'
                '<div>'
                    '<div class="brand-title">CardioCare AI</div>'
                    '<div class="brand-sub">Cổng hỗ trợ thông tin và đánh giá nguy cơ sức khỏe tim mạch</div>'
                '</div>'
            '</div>'
        '</div>'
    )


def render_navigation():
    current = st.session_state["page"]
    cols = st.columns([1, 1, 1, 1, 0.8])

    nav_items = [
        ("home", "🏠 Trang chính"),
        ("predict", "📊 Dự đoán"),
        ("guide", "📘 Hướng dẫn"),
        ("knowledge", "🧠 Kiến thức")
    ]

    for index, (page_key, label) in enumerate(nav_items):
        display_label = f"● {label}" if current == page_key else label
        with cols[index]:
            if st.button(display_label, use_container_width=True, key=f"nav_{page_key}"):
                go_to(page_key)

    with cols[4]:
        if st.button("↩ Quay lại", use_container_width=True, key="nav_back"):
            go_back()


def section_title(title, desc=None):
    html_block(f'<div class="section-title">{escape(title)}</div>')
    if desc:
        html_block(f'<div class="section-desc">{escape(desc)}</div>')


def render_emergency_box():
    html_block(
        '<div class="emergency-box">'
            '<div class="emergency-icon">🚨</div>'
            '<div>'
                '<b>Dấu hiệu cần đi cấp cứu:</b> '
                'đau ngực dữ dội hoặc kéo dài, đau lan tay trái/hàm/lưng, khó thở, '
                'vã mồ hôi, ngất, yếu liệt nửa người, nói khó hoặc tím tái.'
            '</div>'
        '</div>'
    )


def render_banner_slider():
    html_block(
        '<div class="slider-wrapper">'
            '<div class="slider-track">'
                '<div class="slider-item slider-one">'
                    '<div class="slider-content">'
                        '<span class="slider-label">Thông tin tim mạch</span>'
                        '<h2>Phát hiện sớm nguy cơ bệnh tim mạch</h2>'
                        '<p>Theo dõi huyết áp, cholesterol, đường huyết và các dấu hiệu bất thường giúp bạn chủ động hơn trong chăm sóc sức khỏe tim mạch.</p>'
                    '</div>'
                    '<div class="slider-visual"><div class="slider-circle">🫀</div></div>'
                '</div>'
                '<div class="slider-item slider-two">'
                    '<div class="slider-content">'
                        '<span class="slider-label">Dấu hiệu cần chú ý</span>'
                        '<h2>Đau ngực không nên xem nhẹ</h2>'
                        '<p>Đau ngực kéo dài, đau lan tay trái, khó thở, vã mồ hôi hoặc choáng có thể là dấu hiệu cần được hỗ trợ y tế sớm.</p>'
                    '</div>'
                    '<div class="slider-visual"><div class="slider-circle">🚨</div></div>'
                '</div>'
                '<div class="slider-item slider-three">'
                    '<div class="slider-content">'
                        '<span class="slider-label">Bác sĩ AI</span>'
                        '<h2>Luôn có chatbot để bạn hỏi nhanh</h2>'
                        '<p>Bạn có thể hỏi về huyết áp, đau ngực, suy tim, cholesterol, chế độ ăn và các chỉ số sức khỏe thường gặp.</p>'
                    '</div>'
                    '<div class="slider-visual"><div class="slider-circle">💬</div></div>'
                '</div>'
            '</div>'
        '</div>'
    )


def render_card(icon, title, content, tag=None):
    tag_html = f'<span class="card-tag">{escape(tag)}</span>' if tag else ""

    html_block(
        f'<div class="info-card">'
            f'<div class="info-icon">{icon}</div>'
            f'{tag_html}'
            f'<h3>{escape(title)}</h3>'
            f'<p>{escape(content)}</p>'
        f'</div>'
    )


def render_shortcut(icon, title, content, page_key, button_label):
    html_block(
        f'<div class="shortcut-card">'
            f'<div class="shortcut-icon">{icon}</div>'
            f'<h3>{escape(title)}</h3>'
            f'<p>{escape(content)}</p>'
        f'</div>'
    )

    if st.button(button_label, use_container_width=True, key=f"shortcut_{page_key}_{title}"):
        go_to(page_key)


def render_footer():
    html_block(
        '<div class="footer">'
            '<div>'
                '<h3>CardioCare AI</h3>'
                '<p>Hệ thống hỗ trợ tra cứu kiến thức và đánh giá nguy cơ tim mạch.</p>'
                '<p class="footer-warning">Thông tin chỉ mang tính tham khảo, không thay thế chẩn đoán hoặc điều trị từ bác sĩ.</p>'
            '</div>'
            '<div>'
                '<h4>Liên hệ</h4>'
                '<p>📧 Gmail: contact@cardiocare.vn</p>'
                '<p>📘 Facebook: CardioCare AI</p>'
                '<p>💬 Zalo: 0900 000 000</p>'
            '</div>'
            '<div>'
                '<h4>Chức năng</h4>'
                '<p>Đánh giá nguy cơ</p>'
                '<p>Hỏi đáp tài liệu y khoa</p>'
                '<p>Hướng dẫn chỉ số sức khỏe</p>'
            '</div>'
        '</div>'
    )


def add_chat_message(role, content):
    st.session_state["floating_chat_messages"].append(
        {
            "role": role,
            "content": content
        }
    )

    st.session_state["floating_chat_messages"] = st.session_state["floating_chat_messages"][-12:]


def ask_rag(question):
    add_chat_message("user", question)

    if not RAG_AVAILABLE:
        add_chat_message(
            "assistant",
            "Chatbot RAG chưa được kích hoạt. Vui lòng kiểm tra file src/rag_chat.py."
        )
        return

    try:
        result = get_rag_answer(question)

        if isinstance(result, tuple):
            answer = result[0]
        else:
            answer = result

        add_chat_message("assistant", str(answer))
    except Exception as e:
        add_chat_message(
            "assistant",
            f"Hiện chưa thể tạo câu trả lời từ hệ thống tài liệu. Lỗi: {e}"
        )


def render_floating_chatbox():
    with st.popover("", icon="💬", use_container_width=False):
        html_block(
            '<div class="floating-chat-header">'
                '<div class="floating-chat-avatar">🫀</div>'
                '<div>'
                    '<h3>CardioCare Chatbot</h3>'
                    '<p>Hỏi nhanh về sức khỏe tim mạch</p>'
                '</div>'
            '</div>'
        )

        html_block(
            '<div class="floating-chat-warning">'
                'Nếu đau ngực dữ dội, khó thở, ngất hoặc yếu liệt, hãy đi cấp cứu thay vì chờ chatbot.'
            '</div>'
        )

        for msg in st.session_state["floating_chat_messages"][-8:]:
            role = msg.get("role", "assistant")
            content = escape(str(msg.get("content", ""))).replace("\n", "<br>")

            if role == "user":
                html_block(
                    f'<div class="chat-row user-row">'
                        f'<div class="chat-message user-message">{content}</div>'
                    f'</div>'
                )
            else:
                html_block(
                    f'<div class="chat-row bot-row">'
                        f'<div class="chat-message bot-message">{content}</div>'
                    f'</div>'
                )

        st.markdown("##### Câu hỏi nhanh")
        q1, q2 = st.columns(2)

        with q1:
            if st.button("Đau ngực?", use_container_width=True, key="bubble_q1"):
                with st.spinner("Đang tìm thông tin..."):
                    ask_rag("Đau ngực khi nào cần đi cấp cứu?")
                st.rerun()

        with q2:
            if st.button("Huyết áp?", use_container_width=True, key="bubble_q2"):
                with st.spinner("Đang tìm thông tin..."):
                    ask_rag("Huyết áp cao có nguy hiểm không?")
                st.rerun()

        input_key = f"floating_chat_input_{st.session_state['floating_chat_input_version']}"

        question = st.text_input(
            "Nhập câu hỏi",
            key=input_key,
            placeholder="Ví dụ: Cholesterol cao có nguy hiểm không?"
        )

        if st.button("Gửi câu hỏi", use_container_width=True, key="floating_chat_send"):
            if question.strip() == "":
                st.warning("Bạn hãy nhập câu hỏi trước.")
            else:
                with st.spinner("Đang tìm thông tin phù hợp..."):
                    ask_rag(question.strip())

                st.session_state["floating_chat_input_version"] += 1
                st.rerun()


def display_input_value(feature, value):
    config = FIELD_CONFIG.get(feature)

    if not config:
        return value

    if config["type"] == "select":
        return config["options"].get(int(value), str(value))

    unit = config.get("unit", "")
    if unit:
        return f"{value:g} {unit}"

    return f"{value:g}"


def render_input_field(feature):
    config = FIELD_CONFIG.get(feature)
    key = f"input_{feature}"

    if not config:
        if key not in st.session_state:
            st.session_state[key] = 0.0

        return float(
            st.number_input(
                feature,
                value=float(st.session_state[key]),
                key=key
            )
        )

    if key not in st.session_state:
        st.session_state[key] = config["default"]

    if config["type"] == "select":
        options = list(config["options"].keys())
        current_value = st.session_state.get(key, config["default"])

        if current_value not in options:
            current_value = config["default"]

        return float(
            st.selectbox(
                config["label"],
                options=options,
                index=options.index(current_value),
                format_func=lambda x: config["options"].get(x, str(x)),
                help=config.get("help", ""),
                key=key
            )
        )

    return float(
        st.number_input(
            config["label"],
            min_value=config.get("min"),
            max_value=config.get("max"),
            value=st.session_state.get(key, config["default"]),
            step=config.get("step"),
            help=config.get("help", ""),
            key=key
        )
    )


def apply_preset(preset_name, feature_names):
    preset = DEMO_PRESETS[preset_name]

    for feature in feature_names:
        default_value = FIELD_CONFIG.get(feature, {}).get("default", 0)
        st.session_state[f"input_{feature}"] = preset.get(feature, default_value)

    st.rerun()


def validate_input(input_data):
    warnings = []

    age = input_data.get("age", 0)
    if age < 18:
        warnings.append("Tuổi nhập vào khá thấp. Nếu đánh giá cho trẻ em, mô hình này có thể không phù hợp.")

    bp = input_data.get("trestbps", 0)
    if bp >= 180:
        warnings.append("Huyết áp lúc nghỉ rất cao. Nếu kèm đau ngực, khó thở, đau đầu dữ dội hoặc yếu liệt, cần đi cấp cứu.")
    elif bp < 80:
        warnings.append("Huyết áp lúc nghỉ khá thấp. Vui lòng kiểm tra lại chỉ số đo.")

    chol = input_data.get("chol", 0)
    if chol >= 400:
        warnings.append("Cholesterol rất cao. Vui lòng kiểm tra lại đơn vị hoặc kết quả xét nghiệm.")
    elif chol < 100:
        warnings.append("Cholesterol khá thấp so với khoảng thường gặp. Vui lòng kiểm tra lại.")

    thalach = input_data.get("thalach", 0)
    if thalach > 220:
        warnings.append("Nhịp tim tối đa rất cao. Vui lòng kiểm tra lại giá trị nhập.")
    elif thalach < 70:
        warnings.append("Nhịp tim tối đa khá thấp. Vui lòng kiểm tra lại giá trị nhập.")

    oldpeak = input_data.get("oldpeak", 0)
    if oldpeak >= 5:
        warnings.append("Độ chênh ST khá cao. Nếu không chắc thông số này, nên kiểm tra lại kết quả điện tâm đồ.")

    return warnings


def get_risk_level(prediction, probability):
    if probability is None:
        if prediction == 1:
            return "Nguy cơ cao", "high"
        return "Nguy cơ thấp", "low"

    if probability < 0.40:
        return "Nguy cơ thấp", "low"

    if probability < 0.70:
        return "Cần theo dõi", "medium"

    return "Nguy cơ cao", "high"


def generate_explanation(input_data):
    attention = []
    good = []

    age = input_data.get("age")
    if age >= 60:
        attention.append("Tuổi từ 60 trở lên là yếu tố cần chú ý trong nguy cơ tim mạch.")
    elif age < 45:
        good.append("Tuổi còn khá thấp so với nhóm nguy cơ thường gặp.")

    bp = input_data.get("trestbps")
    if bp >= 140:
        attention.append(f"Huyết áp lúc nghỉ {bp:g} mmHg đang ở mức cao.")
    elif bp >= 130:
        attention.append(f"Huyết áp lúc nghỉ {bp:g} mmHg hơi cao, nên theo dõi thêm.")
    else:
        good.append(f"Huyết áp lúc nghỉ {bp:g} mmHg chưa ở mức cao.")

    chol = input_data.get("chol")
    if chol >= 240:
        attention.append(f"Cholesterol {chol:g} mg/dL ở mức cao.")
    elif chol >= 200:
        attention.append(f"Cholesterol {chol:g} mg/dL cần được chú ý.")
    else:
        good.append(f"Cholesterol {chol:g} mg/dL đang ở mức tương đối tốt.")

    if int(input_data.get("fbs", 0)) == 1:
        attention.append("Đường huyết lúc đói cao hơn 120 mg/dL.")
    else:
        good.append("Đường huyết lúc đói chưa vượt ngưỡng 120 mg/dL.")

    if int(input_data.get("exang", 0)) == 1:
        attention.append("Có đau thắt ngực khi vận động.")
    else:
        good.append("Không ghi nhận đau thắt ngực khi vận động.")

    oldpeak = input_data.get("oldpeak")
    if oldpeak >= 2:
        attention.append(f"Độ chênh ST {oldpeak:g} khá cao.")
    elif oldpeak >= 1:
        attention.append(f"Độ chênh ST {oldpeak:g} cần theo dõi thêm.")
    else:
        good.append(f"Độ chênh ST {oldpeak:g} ở mức thấp.")

    if int(input_data.get("ca", 0)) >= 1:
        attention.append(f"Số mạch chính được ghi nhận là {int(input_data.get('ca'))}.")
    else:
        good.append("Số mạch chính được ghi nhận là 0.")

    return attention, good


def render_result_box(risk_text, risk_code, probability):
    if risk_code == "low":
        css_class = "result-low"
        message = "Các thông tin hiện tại chưa cho thấy nguy cơ cao theo mô hình."
    elif risk_code == "medium":
        css_class = "result-medium"
        message = "Một số chỉ số cần được theo dõi thêm và nên cải thiện lối sống."
    else:
        css_class = "result-high"
        message = "Có nhiều yếu tố cần chú ý. Người dùng nên tham khảo nhân viên y tế để được kiểm tra chính xác."

    prob_text = f"{probability:.2%}" if probability is not None else "Không có"

    html_block(
        f'<div class="result-box {css_class}">'
            '<div>'
                '<span class="result-label">Kết quả đánh giá</span>'
                f'<h2>{escape(risk_text)}</h2>'
                f'<p>{escape(message)}</p>'
            '</div>'
            '<div class="result-percent">'
                '<span>Xác suất</span>'
                f'<b>{escape(prob_text)}</b>'
            '</div>'
        '</div>'
    )

    if probability is not None:
        st.progress(min(max(float(probability), 0.0), 1.0))


def build_friendly_table(input_data):
    rows = []

    for feature, value in input_data.items():
        rows.append(
            {
                "Chỉ số": FIELD_CONFIG.get(feature, {}).get("label", feature),
                "Giá trị": display_input_value(feature, value),
                "Ý nghĩa đơn giản": FIELD_CONFIG.get(feature, {}).get("simple", "")
            }
        )

    return pd.DataFrame(rows)


def add_history(input_data, risk_text, probability):
    if "history" not in st.session_state:
        st.session_state["history"] = []

    st.session_state["history"].insert(
        0,
        {
            "Thời điểm": datetime.now().strftime("%H:%M:%S %d/%m/%Y"),
            "Mức đánh giá": risk_text,
            "Xác suất": f"{probability:.2%}" if probability is not None else "Không có",
            "Tuổi": int(input_data.get("age", 0)),
            "Huyết áp": input_data.get("trestbps", 0),
            "Cholesterol": input_data.get("chol", 0)
        }
    )

    st.session_state["history"] = st.session_state["history"][:5]


def render_model_explanation(training_results=None):
    html_block(
        '<div class="plain-box">'
            '<h3>Hệ thống dự đoán hoạt động như thế nào?</h3>'
            '<p>Hệ thống sử dụng mô hình học máy để học từ dữ liệu sức khỏe đã có, sau đó ước lượng nguy cơ tim mạch dựa trên các chỉ số người dùng nhập vào. Kết quả chỉ mang tính hỗ trợ tham khảo, không phải chẩn đoán y khoa.</p>'
        '</div>'
    )

    model_cards = []

    try:
        if training_results is not None and len(training_results) > 0:
            df = pd.DataFrame(training_results)

            name_col = None
            for possible_col in ["model", "model_name", "Mô hình", "name"]:
                if possible_col in df.columns:
                    name_col = possible_col
                    break

            if name_col:
                for _, row in df.head(3).iterrows():
                    model_name = str(row.get(name_col, "Mô hình học máy"))
                    score_parts = []

                    for col in ["accuracy", "Accuracy", "f1", "F1", "roc_auc", "ROC_AUC", "auc", "AUC"]:
                        if col in df.columns:
                            try:
                                score_parts.append(f"{col}: {float(row[col]):.3f}")
                            except Exception:
                                pass

                    model_cards.append(
                        {
                            "name": model_name,
                            "desc": "Mô hình được huấn luyện và so sánh trong quá trình xây dựng hệ thống.",
                            "score": " | ".join(score_parts) if score_parts else "Đã có trong bảng huấn luyện."
                        }
                    )
    except Exception:
        model_cards = []

    if not model_cards:
        model_cards = [
            {
                "name": "Logistic Regression",
                "desc": "Mô hình tuyến tính, dễ giải thích, thường dùng làm mô hình nền để so sánh.",
                "score": "Ưu điểm: dễ hiểu, nhẹ, chạy nhanh."
            },
            {
                "name": "Random Forest",
                "desc": "Mô hình gồm nhiều cây quyết định, có khả năng học quan hệ phi tuyến giữa các chỉ số.",
                "score": "Ưu điểm: ổn định, phù hợp dữ liệu bảng."
            },
            {
                "name": "Gradient Boosting / XGBoost",
                "desc": "Mô hình tăng cường tuần tự, thường cho kết quả tốt trong bài toán dự đoán nguy cơ.",
                "score": "Ưu điểm: hiệu quả cao, bắt được nhiều mẫu dữ liệu phức tạp."
            }
        ]

    cols = st.columns(3)

    for index, item in enumerate(model_cards[:3]):
        with cols[index]:
            html_block(
                f'<div class="model-card">'
                    f'<div class="model-number">0{index + 1}</div>'
                    f'<h3>{escape(str(item["name"]))}</h3>'
                    f'<p>{escape(str(item["desc"]))}</p>'
                    f'<span>{escape(str(item["score"]))}</span>'
                f'</div>'
            )


def render_index_summary():
    html_block(
        '<div class="index-summary">'
            '<h3>Giải thích nhanh các chỉ số</h3>'
            '<p><b>Tuổi</b> và <b>giới tính</b> giúp mô hình ước lượng nguy cơ nền. <b>Huyết áp</b> phản ánh áp lực máu lên thành mạch; nếu cao kéo dài có thể làm tăng nguy cơ đột quỵ, suy tim và bệnh mạch vành. <b>Cholesterol</b> liên quan đến xơ vữa động mạch. <b>Đường huyết lúc đói</b> giúp nhận biết nguy cơ rối loạn đường máu hoặc đái tháo đường. <b>Điện tâm đồ, nhịp tim tối đa, đau ngực khi vận động, độ chênh ST</b> là các thông tin hỗ trợ đánh giá tình trạng tim khi nghỉ hoặc khi gắng sức. Nếu bạn không có đầy đủ chỉ số, có thể giữ mặc định hoặc chọn không rõ, nhưng kết quả sẽ chỉ mang tính tham khảo hơn.</p>'
        '</div>'
    )


def page_home():
    render_emergency_box()
    render_banner_slider()

    section_title(
        "Tìm thông tin tim mạch",
        "Nhập từ khóa như đau ngực, huyết áp, suy tim, cholesterol, đái tháo đường..."
    )

    keyword = st.text_input(
        "Tìm kiếm thông tin",
        placeholder="Ví dụ: đau ngực, tăng huyết áp, suy tim, cholesterol...",
        label_visibility="collapsed"
    )

    filtered = HEART_INFO

    if keyword.strip():
        keyword_lower = keyword.lower()
        filtered = [
            item for item in HEART_INFO
            if keyword_lower in item["title"].lower()
            or keyword_lower in item["content"].lower()
            or keyword_lower in item["tag"].lower()
        ]

    if not filtered:
        st.info("Chưa tìm thấy nội dung phù hợp. Bạn có thể thử từ khóa khác hoặc hỏi chatbot.")
    else:
        cols = st.columns(3)

        for index, item in enumerate(filtered):
            with cols[index % 3]:
                render_card(item["icon"], item["title"], item["content"], item["tag"])

    st.divider()

    section_title(
        "Bạn muốn làm gì hôm nay?",
        "Các trang trong hệ thống được liên kết nội bộ, không mở thêm tab hoặc tạo trang mới."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        render_shortcut(
            "📊",
            "Dự đoán nguy cơ",
            "Nhập các chỉ số sức khỏe và xem kết quả đánh giá.",
            "predict",
            "Mở trang dự đoán"
        )

    with col2:
        render_shortcut(
            "📘",
            "Hướng dẫn sử dụng",
            "Xem cách nhập thông tin và hiểu ý nghĩa các chỉ số.",
            "guide",
            "Xem hướng dẫn"
        )

    with col3:
        render_shortcut(
            "🧠",
            "Kiến thức tim mạch",
            "Đọc các thông tin cơ bản về bệnh tim, huyết áp, suy tim.",
            "knowledge",
            "Xem kiến thức"
        )

    st.divider()

    section_title("Thông tin sức khỏe nên biết")

    col_a, col_b = st.columns(2)

    with col_a:
        html_block(
            '<div class="plain-box">'
                '<h3>Vì sao nên theo dõi sức khỏe tim mạch?</h3>'
                '<p>Nhiều bệnh tim mạch tiến triển âm thầm trong thời gian dài. Việc theo dõi huyết áp, cholesterol, đường huyết, cân nặng và triệu chứng giúp phát hiện sớm các yếu tố nguy cơ để điều chỉnh lối sống hoặc đi khám kịp thời.</p>'
            '</div>'
        )

    with col_b:
        html_block(
            '<div class="plain-box">'
                '<h3>Khi nào nên hỏi chatbot?</h3>'
                '<p>Bạn có thể hỏi chatbot khi muốn hiểu ý nghĩa chỉ số sức khỏe, tìm hiểu bệnh mạch vành, tăng huyết áp, suy tim, chế độ ăn, vận động hoặc cần giải thích đơn giản trước khi đi khám.</p>'
            '</div>'
        )


def page_predict():
    section_title(
        "Đánh giá nguy cơ tim mạch",
        "Nhập thông tin sức khỏe. Nếu không biết chỉ số nào, bạn có thể giữ mặc định hoặc chọn không rõ."
    )

    model_pack, error = safe_load_model()

    if error:
        st.error("Chưa tải được mô hình dự đoán.")
        st.write("Bạn cần kiểm tra thư mục `models` hoặc chạy huấn luyện mô hình trước.")
        st.code(
            """
python -m src.train_model
python -m src.evaluate_model
python -m src.explain_model
python -m streamlit run app.py
            """
        )
        st.code(error)
        return

    model, model_name, scaler, feature_names, training_results = model_pack

    if not feature_names:
        feature_names = DEFAULT_FEATURES

    if "last_prediction_result" in st.session_state:
        result = st.session_state["last_prediction_result"]
        render_result_box(result["risk_text"], result["risk_code"], result["probability"])

        attention, good = generate_explanation(result["input_data"])

        with st.expander("Xem giải thích kết quả", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Cần chú ý")
                if attention:
                    for item in attention:
                        st.markdown(f"- {item}")
                else:
                    st.write("Chưa phát hiện yếu tố nổi bật cần cảnh báo.")

            with col2:
                st.markdown("### Tương đối ổn")
                if good:
                    for item in good:
                        st.markdown(f"- {item}")
                else:
                    st.write("Chưa có yếu tố nào nổi bật ở nhóm tương đối ổn.")

        st.divider()

    html_block(
        f'<div class="model-note"><b>Mô hình đang sử dụng:</b> {escape(str(model_name))}</div>'
    )

    st.markdown("### Chọn nhanh mẫu thông tin")

    p1, p2, p3 = st.columns(3)

    with p1:
        if st.button("🟢 Mẫu nguy cơ thấp", use_container_width=True):
            apply_preset("low", feature_names)

    with p2:
        if st.button("🟡 Mẫu cần theo dõi", use_container_width=True):
            apply_preset("medium", feature_names)

    with p3:
        if st.button("🔴 Mẫu nguy cơ cao", use_container_width=True):
            apply_preset("high", feature_names)

    st.divider()

    with st.form("prediction_form"):
        input_data = {}
        col1, col2 = st.columns(2)

        for index, feature in enumerate(feature_names):
            target_col = col1 if index % 2 == 0 else col2
            with target_col:
                input_data[feature] = render_input_field(feature)

        warnings = validate_input(input_data)

        if warnings:
            st.warning("Một số thông tin cần kiểm tra lại:")
            for item in warnings:
                st.markdown(f"- {item}")

        submitted = st.form_submit_button("📊 Dự đoán ngay", use_container_width=True)

    if submitted:
        df_input = pd.DataFrame([input_data], columns=feature_names)
        input_scaled = scaler.transform(df_input)

        prediction = int(model.predict(input_scaled)[0])

        probability = None
        if hasattr(model, "predict_proba"):
            probability = float(model.predict_proba(input_scaled)[0][1])

        risk_text, risk_code = get_risk_level(prediction, probability)

        st.session_state["last_prediction_result"] = {
            "input_data": input_data,
            "prediction": prediction,
            "probability": probability,
            "risk_text": risk_text,
            "risk_code": risk_code
        }

        add_history(input_data, risk_text, probability)
        st.rerun()

    if "last_prediction_result" in st.session_state:
        with st.expander("Xem bảng thông tin đã nhập"):
            st.dataframe(
                build_friendly_table(st.session_state["last_prediction_result"]["input_data"]),
                use_container_width=True
            )

    if "history" in st.session_state and st.session_state["history"]:
        st.divider()
        st.markdown("### Lịch sử đánh giá gần đây")
        st.dataframe(pd.DataFrame(st.session_state["history"]), use_container_width=True)


def page_guide():
    section_title(
        "Hướng dẫn sử dụng hệ thống",
        "Đọc phần này trước khi nhập thông tin để hiểu cách dùng và ý nghĩa kết quả."
    )

    html_block(
        '<div class="guide-box">'
            '<h3>1. Cách sử dụng nhanh</h3>'
            '<p>Đầu tiên, bạn vào trang <b>Dự đoán</b>, nhập các thông tin sức khỏe mà bạn biết. Nếu chưa có kết quả xét nghiệm hoặc không rõ một chỉ số nào đó, bạn có thể giữ giá trị mặc định hoặc chọn mục không rõ. Sau đó bấm <b>Dự đoán ngay</b>, kết quả sẽ hiển thị ở đầu trang.</p>'
            '<h3>2. Cách hiểu kết quả</h3>'
            '<p>Kết quả gồm ba mức: <b>Nguy cơ thấp</b>, <b>Cần theo dõi</b> và <b>Nguy cơ cao</b>. Đây là kết quả hỗ trợ tham khảo từ mô hình học máy, không phải kết luận chẩn đoán. Nếu có triệu chứng bất thường, bạn vẫn nên đi khám hoặc liên hệ nhân viên y tế.</p>'
            '<h3>3. Khi nào không nên chờ hệ thống?</h3>'
            '<p>Nếu có đau ngực dữ dội hoặc kéo dài, đau lan tay trái, hàm, lưng, khó thở, vã mồ hôi, ngất, yếu liệt hoặc nói khó, bạn nên đi cấp cứu ngay.</p>'
        '</div>'
    )

    render_emergency_box()

    st.divider()

    section_title(
        "Giải thích ngắn các chỉ số",
        "Phần này giúp người dùng không chuyên hiểu các thông tin cần nhập."
    )

    render_index_summary()

    with st.expander("Xem giải thích chi tiết từng chỉ số"):
        for _, config in FIELD_CONFIG.items():
            st.markdown(f"### {config['label']}")
            st.write(config.get("simple", ""))
            st.caption(config.get("help", ""))

    st.divider()

    section_title(
        "Ba mô hình dự đoán trong hệ thống",
        "Hệ thống có thể so sánh nhiều mô hình và chọn mô hình có kết quả tốt nhất để sử dụng."
    )

    model_pack, _ = safe_load_model()

    if model_pack:
        model, model_name, scaler, feature_names, training_results = model_pack
        render_model_explanation(training_results)

        html_block(
            f'<div class="model-note"><b>Mô hình đang được hệ thống chọn để dự đoán:</b> {escape(str(model_name))}</div>'
        )
    else:
        render_model_explanation(None)


def page_knowledge():
    section_title(
        "Kiến thức tim mạch",
        "Các câu hỏi thường gặp được trình bày ngắn gọn, dễ hiểu."
    )

    render_emergency_box()

    for item in FAQ_DATA:
        with st.expander(item["q"]):
            st.write(item["a"])

    st.divider()

    section_title("Chủ đề nên tìm hiểu")

    topics = [
        ("🩸", "Tăng huyết áp", "Theo dõi huyết áp, giảm muối, dùng thuốc đúng chỉ định."),
        ("🫀", "Suy tim", "Nhận biết khó thở, phù chân, mệt nhiều và tái khám định kỳ."),
        ("⚠️", "Đau thắt ngực", "Chú ý đau khi gắng sức, đau kéo dài hoặc kèm khó thở."),
        ("🥗", "Dinh dưỡng", "Ăn nhạt, giảm mỡ bão hòa, tăng rau xanh và ngũ cốc nguyên hạt."),
        ("🚶", "Vận động", "Tập đều đặn phù hợp sức khỏe, tránh quá sức khi có triệu chứng."),
        ("💊", "Thuốc tim mạch", "Không tự ngưng thuốc, không tự tăng liều khi chưa hỏi bác sĩ.")
    ]

    cols = st.columns(3)

    for index, topic in enumerate(topics):
        with cols[index % 3]:
            render_card(topic[0], topic[1], topic[2])


render_topbar()
render_header()
render_navigation()
render_floating_chatbox()

current_page = st.session_state["page"]

if current_page == "home":
    page_home()
elif current_page == "predict":
    page_predict()
elif current_page == "guide":
    page_guide()
elif current_page == "knowledge":
    page_knowledge()
else:
    page_home()

render_footer()