import os
from datetime import datetime

import joblib
import pandas as pd
import streamlit as st


try:
    from src.rag_chat import get_rag_answer
    RAG_AVAILABLE = True
except Exception:
    RAG_AVAILABLE = False


st.set_page_config(
    page_title="Hệ thống hỗ trợ đánh giá nguy cơ bệnh tim mạch",
    page_icon="🩺",
    layout="wide"
)


# =========================
# CSS
# =========================
st.markdown("""
<style>
    .hero-box {
        background: linear-gradient(135deg, #EFF6FF 0%, #F8FAFC 100%);
        border: 1px solid #DBEAFE;
        border-radius: 18px;
        padding: 24px 28px;
        margin-bottom: 20px;
    }

    .main-title {
        font-size: 34px;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 6px;
    }

    .sub-title {
        font-size: 16px;
        color: #475569;
        line-height: 1.6;
    }

    .notice-box {
        background-color: #FFF7ED;
        border-left: 5px solid #F97316;
        border-radius: 12px;
        padding: 14px 18px;
        color: #7C2D12;
        margin-bottom: 18px;
    }

    .success-box {
        background-color: #ECFDF5;
        border-left: 5px solid #10B981;
        border-radius: 12px;
        padding: 16px 18px;
        color: #064E3B;
        margin-top: 14px;
    }

    .warning-box {
        background-color: #FFFBEB;
        border-left: 5px solid #F59E0B;
        border-radius: 12px;
        padding: 16px 18px;
        color: #78350F;
        margin-top: 14px;
    }

    .danger-box {
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        border-radius: 12px;
        padding: 16px 18px;
        color: #7F1D1D;
        margin-top: 14px;
    }

    .info-box {
        background-color: #F8FAFC;
        border-left: 5px solid #3B82F6;
        border-radius: 12px;
        padding: 16px 18px;
        color: #1E3A8A;
        margin-top: 14px;
    }

    .section-title {
        font-size: 23px;
        font-weight: 750;
        color: #0F172A;
        margin-bottom: 8px;
    }

    .section-desc {
        font-size: 15px;
        color: #64748B;
        margin-bottom: 16px;
        line-height: 1.6;
    }

    .small-muted {
        font-size: 14px;
        color: #64748B;
    }
</style>
""", unsafe_allow_html=True)


# =========================
# Cấu hình trường dữ liệu
# =========================
FIELD_CONFIG = {
    "age": {
        "label": "Tuổi",
        "type": "number",
        "default": 50,
        "min": 1,
        "max": 120,
        "step": 1,
        "unit": "tuổi",
        "help": "Tuổi của người được đánh giá."
    },
    "sex": {
        "label": "Giới tính",
        "type": "select",
        "default": 1,
        "options": {
            1: "Nam",
            0: "Nữ"
        },
        "help": "Quy đổi cho mô hình: Nam = 1, Nữ = 0."
    },
    "cp": {
        "label": "Loại đau ngực",
        "type": "select",
        "default": 0,
        "options": {
            0: "Đau thắt ngực điển hình",
            1: "Đau thắt ngực không điển hình",
            2: "Đau ngực không do tim",
            3: "Không có triệu chứng rõ"
        },
        "help": "Nếu không chắc, có thể chọn gần đúng theo triệu chứng."
    },
    "trestbps": {
        "label": "Huyết áp lúc nghỉ",
        "type": "number",
        "default": 120,
        "min": 60,
        "max": 250,
        "step": 1,
        "unit": "mmHg",
        "help": "Huyết áp lúc nghỉ, đơn vị mmHg."
    },
    "chol": {
        "label": "Cholesterol",
        "type": "number",
        "default": 200,
        "min": 80,
        "max": 700,
        "step": 1,
        "unit": "mg/dL",
        "help": "Chỉ số cholesterol trong máu."
    },
    "fbs": {
        "label": "Đường huyết lúc đói",
        "type": "select",
        "default": 0,
        "options": {
            0: "Bình thường hoặc ≤ 120 mg/dL",
            1: "Cao hơn 120 mg/dL"
        },
        "help": "Quy đổi cho mô hình: Bình thường = 0, Cao = 1."
    },
    "restecg": {
        "label": "Điện tâm đồ lúc nghỉ",
        "type": "select",
        "default": 0,
        "options": {
            0: "Bình thường",
            1: "Có bất thường ST-T",
            2: "Có dấu hiệu phì đại thất trái"
        },
        "help": "Nếu chưa có kết quả điện tâm đồ, có thể để mặc định là bình thường."
    },
    "thalach": {
        "label": "Nhịp tim tối đa",
        "type": "number",
        "default": 150,
        "min": 50,
        "max": 250,
        "step": 1,
        "unit": "bpm",
        "help": "Nhịp tim tối đa đạt được."
    },
    "exang": {
        "label": "Đau thắt ngực khi vận động",
        "type": "select",
        "default": 0,
        "options": {
            0: "Không",
            1: "Có"
        },
        "help": "Có xuất hiện đau thắt ngực khi vận động hay không."
    },
    "oldpeak": {
        "label": "Độ chênh ST",
        "type": "number",
        "default": 1.0,
        "min": 0.0,
        "max": 10.0,
        "step": 0.1,
        "unit": "",
        "help": "Chỉ số ST depression. Nếu không có thông tin, có thể để mặc định."
    },
    "slope": {
        "label": "Độ dốc đoạn ST",
        "type": "select",
        "default": 1,
        "options": {
            0: "Dốc lên",
            1: "Phẳng",
            2: "Dốc xuống"
        },
        "help": "Dạng độ dốc đoạn ST khi vận động."
    },
    "ca": {
        "label": "Số mạch chính",
        "type": "select",
        "default": 0,
        "options": {
            0: "0 mạch",
            1: "1 mạch",
            2: "2 mạch",
            3: "3 mạch",
            4: "4 mạch"
        },
        "help": "Nếu không có thông tin chụp mạch, có thể để 0."
    },
    "thal": {
        "label": "Chỉ số Thalassemia",
        "type": "select",
        "default": 2,
        "options": {
            0: "Không rõ / Không ghi nhận",
            1: "Bình thường",
            2: "Khiếm khuyết cố định",
            3: "Khiếm khuyết có thể hồi phục"
        },
        "help": "Nếu không có thông tin, có thể chọn Không rõ / Không ghi nhận."
    }
}


DEMO_PRESETS = {
    "low": {
        "age": 35,
        "sex": 0,
        "cp": 2,
        "trestbps": 115,
        "chol": 175,
        "fbs": 0,
        "restecg": 0,
        "thalach": 170,
        "exang": 0,
        "oldpeak": 0.2,
        "slope": 0,
        "ca": 0,
        "thal": 1
    },
    "medium": {
        "age": 52,
        "sex": 1,
        "cp": 1,
        "trestbps": 135,
        "chol": 220,
        "fbs": 0,
        "restecg": 1,
        "thalach": 140,
        "exang": 0,
        "oldpeak": 1.2,
        "slope": 1,
        "ca": 1,
        "thal": 2
    },
    "high": {
        "age": 66,
        "sex": 1,
        "cp": 3,
        "trestbps": 155,
        "chol": 275,
        "fbs": 1,
        "restecg": 1,
        "thalach": 110,
        "exang": 1,
        "oldpeak": 2.8,
        "slope": 2,
        "ca": 2,
        "thal": 3
    }
}


# =========================
# Load model
# =========================
@st.cache_resource
def load_artifacts():
    model = joblib.load("models/best_model.pkl")
    model_name = joblib.load("models/best_model_name.pkl")
    scaler = joblib.load("models/scaler.pkl")
    feature_names = joblib.load("models/feature_names.pkl")
    training_results = joblib.load("models/training_results.pkl")
    return model, model_name, scaler, feature_names, training_results


# =========================
# Hàm tiện ích giao diện
# =========================
def format_feature_name(feature):
    if feature in FIELD_CONFIG:
        return FIELD_CONFIG[feature]["label"]
    return feature.replace("_", " ").title()


def get_default_value(feature):
    if feature in FIELD_CONFIG:
        return FIELD_CONFIG[feature]["default"]
    return 0


def apply_preset(preset_name, feature_names):
    preset = DEMO_PRESETS[preset_name]

    for feature in feature_names:
        if feature in preset:
            st.session_state[f"input_{feature}"] = preset[feature]
        else:
            st.session_state[f"input_{feature}"] = get_default_value(feature)

    st.session_state["preset_applied"] = preset_name


def render_input_field(feature):
    config = FIELD_CONFIG.get(feature)
    key = f"input_{feature}"

    if config is None:
        if key not in st.session_state:
            st.session_state[key] = 0.0

        return float(st.number_input(
            format_feature_name(feature),
            value=float(st.session_state[key]),
            step=1.0,
            help=f"Trường dữ liệu gốc: {feature}",
            key=key
        ))

    if key not in st.session_state:
        st.session_state[key] = config["default"]

    if config["type"] == "select":
        options = list(config["options"].keys())
        current_value = st.session_state.get(key, config["default"])

        if current_value not in options:
            current_value = config["default"]

        index = options.index(current_value)

        return float(st.selectbox(
            config["label"],
            options=options,
            index=index,
            format_func=lambda x: config["options"].get(x, str(x)),
            help=config.get("help", ""),
            key=key
        ))

    if config["type"] == "number":
        return float(st.number_input(
            config["label"],
            min_value=config.get("min"),
            max_value=config.get("max"),
            value=st.session_state.get(key, config["default"]),
            step=config.get("step"),
            help=config.get("help", ""),
            key=key
        ))

    return 0.0


def display_input_value(feature, value):
    config = FIELD_CONFIG.get(feature)

    if config is None:
        return value

    if config["type"] == "select":
        return config["options"].get(int(value), str(value))

    unit = config.get("unit", "")
    value_text = f"{value:g}"

    if unit:
        return f"{value_text} {unit}"

    return value_text


def build_friendly_input_table(input_data):
    rows = []

    for feature, value in input_data.items():
        rows.append({
            "Thông số": format_feature_name(feature),
            "Giá trị hiển thị": display_input_value(feature, value),
            "Mã đưa vào mô hình": value
        })

    return pd.DataFrame(rows)


def validate_input(input_data):
    warnings = []

    age = input_data.get("age")
    if age is not None and age < 18:
        warnings.append("Tuổi nhập vào khá thấp so với nhóm dữ liệu bệnh tim thường gặp. Vui lòng kiểm tra lại.")

    trestbps = input_data.get("trestbps")
    if trestbps is not None:
        if trestbps >= 180:
            warnings.append("Huyết áp lúc nghỉ rất cao. Vui lòng kiểm tra lại đơn vị đo hoặc tham khảo cơ sở y tế.")
        elif trestbps < 80:
            warnings.append("Huyết áp lúc nghỉ khá thấp. Vui lòng kiểm tra lại giá trị nhập.")

    chol = input_data.get("chol")
    if chol is not None:
        if chol >= 400:
            warnings.append("Cholesterol rất cao. Vui lòng kiểm tra lại đơn vị đo hoặc kết quả xét nghiệm.")
        elif chol < 100:
            warnings.append("Cholesterol khá thấp so với khoảng thường gặp. Vui lòng kiểm tra lại.")

    thalach = input_data.get("thalach")
    if thalach is not None:
        if thalach < 80:
            warnings.append("Nhịp tim tối đa khá thấp. Vui lòng kiểm tra lại giá trị nhập.")
        elif thalach > 220:
            warnings.append("Nhịp tim tối đa rất cao. Vui lòng kiểm tra lại giá trị nhập.")

    oldpeak = input_data.get("oldpeak")
    if oldpeak is not None and oldpeak >= 5:
        warnings.append("Độ chênh ST khá cao. Nếu không chắc giá trị này, nên kiểm tra lại thông tin xét nghiệm.")

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
    neutral = []

    age = input_data.get("age")
    if age is not None:
        if age >= 60:
            attention.append("Tuổi từ 60 trở lên là yếu tố hệ thống cần chú ý.")
        elif age < 45:
            good.append("Tuổi còn khá thấp so với nhóm nguy cơ thường gặp trong dữ liệu.")
        else:
            neutral.append("Tuổi nằm ở nhóm trung bình, cần xem thêm các chỉ số khác.")

    trestbps = input_data.get("trestbps")
    if trestbps is not None:
        if trestbps >= 140:
            attention.append(f"Huyết áp lúc nghỉ {trestbps:g} mmHg khá cao.")
        elif trestbps >= 130:
            attention.append(f"Huyết áp lúc nghỉ {trestbps:g} mmHg hơi cao, nên tiếp tục theo dõi.")
        else:
            good.append(f"Huyết áp lúc nghỉ {trestbps:g} mmHg chưa ở mức cao.")

    chol = input_data.get("chol")
    if chol is not None:
        if chol >= 240:
            attention.append(f"Cholesterol {chol:g} mg/dL ở mức cao.")
        elif chol >= 200:
            attention.append(f"Cholesterol {chol:g} mg/dL ở mức cần chú ý.")
        else:
            good.append(f"Cholesterol {chol:g} mg/dL đang ở mức tương đối tốt.")

    fbs = input_data.get("fbs")
    if fbs is not None:
        if int(fbs) == 1:
            attention.append("Đường huyết lúc đói cao hơn 120 mg/dL.")
        else:
            good.append("Đường huyết lúc đói chưa vượt ngưỡng 120 mg/dL.")

    restecg = input_data.get("restecg")
    if restecg is not None:
        if int(restecg) == 0:
            good.append("Điện tâm đồ lúc nghỉ được ghi nhận là bình thường.")
        else:
            attention.append(f"Điện tâm đồ lúc nghỉ: {display_input_value('restecg', restecg)}.")

    thalach = input_data.get("thalach")
    if thalach is not None:
        if thalach < 120:
            attention.append(f"Nhịp tim tối đa {thalach:g} bpm tương đối thấp.")
        elif thalach >= 150:
            good.append(f"Nhịp tim tối đa {thalach:g} bpm là tín hiệu tương đối tốt trong dữ liệu.")
        else:
            neutral.append(f"Nhịp tim tối đa {thalach:g} bpm nằm ở mức trung gian.")

    exang = input_data.get("exang")
    if exang is not None:
        if int(exang) == 1:
            attention.append("Có đau thắt ngực khi vận động.")
        else:
            good.append("Không ghi nhận đau thắt ngực khi vận động.")

    oldpeak = input_data.get("oldpeak")
    if oldpeak is not None:
        if oldpeak >= 2:
            attention.append(f"Độ chênh ST {oldpeak:g} khá cao.")
        elif oldpeak >= 1:
            attention.append(f"Độ chênh ST {oldpeak:g} cần được chú ý thêm.")
        else:
            good.append(f"Độ chênh ST {oldpeak:g} ở mức thấp.")

    slope = input_data.get("slope")
    if slope is not None:
        if int(slope) == 0:
            good.append("Độ dốc đoạn ST là dốc lên, thường là tín hiệu thuận lợi hơn.")
        else:
            attention.append(f"Độ dốc đoạn ST: {display_input_value('slope', slope)}.")

    ca = input_data.get("ca")
    if ca is not None:
        if int(ca) >= 1:
            attention.append(f"Số mạch chính được ghi nhận là {int(ca)}.")
        else:
            good.append("Số mạch chính được ghi nhận là 0.")

    thal = input_data.get("thal")
    if thal is not None:
        if int(thal) in [2, 3]:
            attention.append(f"Chỉ số Thalassemia: {display_input_value('thal', thal)}.")
        elif int(thal) == 1:
            good.append("Chỉ số Thalassemia được ghi nhận là bình thường.")
        else:
            neutral.append("Chỉ số Thalassemia không rõ hoặc không được ghi nhận đầy đủ.")

    cp = input_data.get("cp")
    if cp is not None:
        neutral.append(f"Loại đau ngực được ghi nhận: {display_input_value('cp', cp)}.")

    sex = input_data.get("sex")
    if sex is not None:
        neutral.append(f"Giới tính được ghi nhận: {display_input_value('sex', sex)}.")

    return attention, good, neutral


def render_result_summary(prediction, probability):
    risk_text, risk_code = get_risk_level(prediction, probability)

    if risk_code == "low":
        st.markdown(f"""
        <div class="success-box">
            <b>Mức đánh giá:</b> {risk_text}<br>
            Dữ liệu đầu vào hiện chưa cho thấy dấu hiệu nguy cơ cao theo mô hình.
            Người dùng vẫn nên duy trì lối sống lành mạnh và kiểm tra sức khỏe định kỳ.
        </div>
        """, unsafe_allow_html=True)
    elif risk_code == "medium":
        st.markdown(f"""
        <div class="warning-box">
            <b>Mức đánh giá:</b> {risk_text}<br>
            Dữ liệu đầu vào có một số yếu tố cần chú ý. Người dùng nên tiếp tục theo dõi
            các chỉ số sức khỏe và tham khảo ý kiến chuyên môn nếu có triệu chứng bất thường.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="danger-box">
            <b>Mức đánh giá:</b> {risk_text}<br>
            Dữ liệu đầu vào cho thấy nhiều dấu hiệu nguy cơ. Người dùng nên tham khảo ý kiến bác sĩ
            hoặc cơ sở y tế để được kiểm tra chính xác hơn.
        </div>
        """, unsafe_allow_html=True)

    if probability is not None:
        st.metric("Xác suất nguy cơ theo mô hình", f"{probability:.2%}")
        st.progress(min(max(probability, 0.0), 1.0))

    return risk_text, risk_code


def render_explanation(input_data):
    attention, good, neutral = generate_explanation(input_data)

    st.subheader("Vì sao hệ thống đưa ra đánh giá này?")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Yếu tố cần chú ý")
        if attention:
            for item in attention:
                st.markdown(f"- {item}")
        else:
            st.write("Chưa phát hiện yếu tố nổi bật cần cảnh báo từ dữ liệu đầu vào.")

    with col2:
        st.markdown("#### Yếu tố tương đối ổn")
        if good:
            for item in good:
                st.markdown(f"- {item}")
        else:
            st.write("Chưa có yếu tố nào nổi bật ở nhóm tương đối ổn.")

    if neutral:
        with st.expander("Thông tin bổ sung"):
            for item in neutral:
                st.markdown(f"- {item}")


def render_next_steps(risk_code):
    st.subheader("Gợi ý tiếp theo")

    if risk_code == "high":
        st.warning("""
        Hệ thống ghi nhận dấu hiệu nguy cơ cao. Người dùng nên:

        - Theo dõi lại các chỉ số huyết áp, cholesterol và đường huyết.
        - Không tự kết luận bệnh hoặc tự dùng thuốc dựa trên kết quả này.
        - Tham khảo ý kiến bác sĩ nếu có đau ngực, khó thở, mệt bất thường hoặc hồi hộp kéo dài.
        - Duy trì chế độ ăn uống lành mạnh, hạn chế thuốc lá, rượu bia và vận động phù hợp.
        """)
    elif risk_code == "medium":
        st.info("""
        Hệ thống ghi nhận một số yếu tố cần theo dõi. Người dùng nên:

        - Kiểm tra lại các chỉ số sức khỏe định kỳ.
        - Chú ý huyết áp, cholesterol và dấu hiệu đau ngực khi vận động.
        - Cải thiện chế độ ăn uống, giấc ngủ và vận động.
        - Tham khảo nhân viên y tế nếu triệu chứng xuất hiện thường xuyên.
        """)
    else:
        st.info("""
        Hệ thống chưa ghi nhận dấu hiệu nguy cơ cao. Người dùng nên:

        - Tiếp tục duy trì lối sống lành mạnh.
        - Khám sức khỏe định kỳ.
        - Theo dõi huyết áp, cholesterol và đường huyết.
        - Không chủ quan nếu có triệu chứng bất thường.
        """)


def get_suggested_questions(input_data):
    questions = []

    if input_data.get("chol", 0) >= 200:
        questions.append("Cholesterol cao ảnh hưởng như thế nào đến tim mạch?")

    if input_data.get("trestbps", 0) >= 130:
        questions.append("Huyết áp cao có nguy hiểm không và nên theo dõi như thế nào?")

    if int(input_data.get("exang", 0)) == 1:
        questions.append("Đau thắt ngực khi vận động có thể là dấu hiệu gì?")

    if input_data.get("oldpeak", 0) >= 1:
        questions.append("Chỉ số ST trong điện tâm đồ có ý nghĩa gì?")

    if len(questions) == 0:
        questions = [
            "Làm thế nào để giảm nguy cơ bệnh tim mạch?",
            "Nên ăn uống như thế nào để tốt cho tim mạch?",
            "Khi nào nên đi khám tim mạch?"
        ]

    return questions


def add_history(input_data, risk_text, probability):
    if "history" not in st.session_state:
        st.session_state["history"] = []

    st.session_state["history"].insert(0, {
        "Thời điểm": datetime.now().strftime("%H:%M:%S %d/%m/%Y"),
        "Mức đánh giá": risk_text,
        "Xác suất": f"{probability:.2%}" if probability is not None else "Không có",
        "Tuổi": int(input_data.get("age", 0)),
        "Huyết áp": input_data.get("trestbps", 0),
        "Cholesterol": input_data.get("chol", 0)
    })

    st.session_state["history"] = st.session_state["history"][:5]


def render_header():
    st.markdown("""
    <div class="hero-box">
        <div class="main-title">🩺 Hệ thống hỗ trợ đánh giá nguy cơ bệnh tim mạch</div>
        <div class="sub-title">
            Ứng dụng sử dụng mô hình học máy để hỗ trợ đánh giá nguy cơ,
            giải thích kết quả bằng ngôn ngữ dễ hiểu và cung cấp trợ lý hỏi đáp dựa trên tài liệu y khoa.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="notice-box">
        <b>Lưu ý:</b> Hệ thống chỉ phục vụ mục đích học tập, nghiên cứu và tham khảo.
        Kết quả không thay thế cho chẩn đoán hoặc tư vấn từ bác sĩ.
    </div>
    """, unsafe_allow_html=True)


# =========================
# App chính
# =========================
render_header()

try:
    model, model_name, scaler, feature_names, training_results = load_artifacts()

    # Sidebar kỹ thuật
    with st.sidebar:
        st.header("🔧 Khu vực kỹ thuật")
        st.caption("Phần này phục vụ báo cáo và thuyết trình, không dành cho bệnh nhân.")

        with st.expander("Thông tin mô hình", expanded=False):
            st.write("Mô hình được chọn:")
            st.success(model_name)
            st.write("Số đặc trưng đầu vào:", len(feature_names))
            st.write("Số mô hình so sánh:", len(training_results))

        with st.expander("Bảng so sánh mô hình", expanded=False):
            st.dataframe(pd.DataFrame(training_results), use_container_width=True)

        with st.expander("Biểu đồ đánh giá", expanded=False):
            if os.path.exists("reports/confusion_matrix.png"):
                st.image("reports/confusion_matrix.png", caption="Confusion Matrix")
            if os.path.exists("reports/roc_curve.png"):
                st.image("reports/roc_curve.png", caption="ROC Curve")

        with st.expander("Biểu đồ SHAP", expanded=False):
            if os.path.exists("reports/shap_summary.png"):
                st.image("reports/shap_summary.png", caption="SHAP Summary")
            if os.path.exists("reports/shap_bar.png"):
                st.image("reports/shap_bar.png", caption="SHAP Bar")

    tab1, tab2, tab3 = st.tabs([
        "🧾 Nhập thông tin",
        "📋 Kết quả của tôi",
        "💬 Hỏi đáp sức khỏe"
    ])

    # =========================
    # TAB 1: Nhập thông tin
    # =========================
    with tab1:
        st.markdown('<div class="section-title">Nhập thông tin sức khỏe</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-desc">Các trường dữ liệu đã được chuyển sang dạng dễ hiểu như Nam/Nữ, Có/Không, Bình thường/Cao để người dùng thao tác thuận tiện hơn.</div>',
            unsafe_allow_html=True
        )

        st.info(f"Mô hình đang sử dụng: **{model_name}**")

        st.subheader("Chọn mẫu demo nhanh")
        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button("🟢 Mẫu nguy cơ thấp", use_container_width=True):
                apply_preset("low", feature_names)
                st.rerun()

        with c2:
            if st.button("🟡 Mẫu cần theo dõi", use_container_width=True):
                apply_preset("medium", feature_names)
                st.rerun()

        with c3:
            if st.button("🔴 Mẫu nguy cơ cao", use_container_width=True):
                apply_preset("high", feature_names)
                st.rerun()

        st.divider()

        input_data = {}

        col1, col2 = st.columns(2)

        for index, feature in enumerate(feature_names):
            if index % 2 == 0:
                with col1:
                    input_data[feature] = render_input_field(feature)
            else:
                with col2:
                    input_data[feature] = render_input_field(feature)

        warnings = validate_input(input_data)

        if warnings:
            st.warning("Một số giá trị cần kiểm tra lại:")
            for item in warnings:
                st.markdown(f"- {item}")

        st.divider()

        if st.button("🔎 Xem kết quả đánh giá nguy cơ", use_container_width=True):
            df_input = pd.DataFrame([input_data], columns=feature_names)
            input_scaled = scaler.transform(df_input)

            prediction = int(model.predict(input_scaled)[0])

            probability = None
            if hasattr(model, "predict_proba"):
                probability = float(model.predict_proba(input_scaled)[0][1])

            risk_text, risk_code = get_risk_level(prediction, probability)

            st.session_state["last_input_data"] = input_data
            st.session_state["last_prediction"] = prediction
            st.session_state["last_probability"] = probability
            st.session_state["last_risk_text"] = risk_text
            st.session_state["last_risk_code"] = risk_code

            add_history(input_data, risk_text, probability)

            st.success("Đã đánh giá xong. Vui lòng chuyển sang tab 'Kết quả của tôi' để xem chi tiết.")

    # =========================
    # TAB 2: Kết quả
    # =========================
    with tab2:
        st.markdown('<div class="section-title">Kết quả đánh giá của tôi</div>', unsafe_allow_html=True)

        if "last_input_data" not in st.session_state:
            st.markdown("""
            <div class="info-box">
                Bạn chưa thực hiện đánh giá. Vui lòng chuyển sang tab <b>Nhập thông tin</b>,
                nhập các chỉ số sức khỏe và bấm <b>Xem kết quả đánh giá nguy cơ</b>.
            </div>
            """, unsafe_allow_html=True)
        else:
            input_data = st.session_state["last_input_data"]
            prediction = st.session_state["last_prediction"]
            probability = st.session_state["last_probability"]

            risk_text, risk_code = render_result_summary(prediction, probability)

            st.divider()

            render_explanation(input_data)

            st.divider()

            render_next_steps(risk_code)

            st.divider()

            st.subheader("Câu hỏi nên tìm hiểu thêm")
            for question in get_suggested_questions(input_data):
                st.markdown(f"- {question}")

            with st.expander("Xem thông tin đầu vào đã sử dụng"):
                friendly_df = build_friendly_input_table(input_data)
                st.dataframe(friendly_df, use_container_width=True)

            with st.expander("Xem dữ liệu dạng mã số đưa vào mô hình"):
                df_input = pd.DataFrame([input_data], columns=feature_names)
                st.dataframe(df_input, use_container_width=True)

        if "history" in st.session_state and len(st.session_state["history"]) > 0:
            st.divider()
            st.subheader("Lịch sử đánh giá gần đây")
            st.dataframe(pd.DataFrame(st.session_state["history"]), use_container_width=True)

    # =========================
    # TAB 3: Chatbot
    # =========================
    with tab3:
        st.markdown('<div class="section-title">Hỏi đáp sức khỏe dựa trên tài liệu</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-desc">Trợ lý sẽ truy xuất thông tin từ tài liệu y khoa đã nạp vào hệ thống trước khi tạo câu trả lời.</div>',
            unsafe_allow_html=True
        )

        if not RAG_AVAILABLE:
            st.warning("Chưa kích hoạt được chatbot. Hãy kiểm tra file src/rag_chat.py.")
            st.code("""
python -m src.rag_build
python -m src.rag_chat
""")
        else:
            default_question = ""

            if "last_input_data" in st.session_state:
                suggestions = get_suggested_questions(st.session_state["last_input_data"])
                st.subheader("Câu hỏi gợi ý theo kết quả gần nhất")

                cols = st.columns(1)
                for i, q in enumerate(suggestions):
                    if st.button(q, key=f"suggested_q_{i}", use_container_width=True):
                        st.session_state["chat_question"] = q

                default_question = st.session_state.get("chat_question", "")

            question = st.text_input(
                "Nhập câu hỏi cần tư vấn",
                value=default_question,
                placeholder="Ví dụ: Cholesterol cao có nguy hiểm không?"
            )

            if st.button("💬 Gửi câu hỏi", use_container_width=True):
                if question.strip() == "":
                    st.warning("Vui lòng nhập câu hỏi trước khi gửi.")
                else:
                    with st.spinner("Hệ thống đang truy xuất tài liệu và tạo câu trả lời..."):
                        try:
                            answer, docs = get_rag_answer(question)

                            st.subheader("Câu trả lời tham khảo")
                            st.write(answer)

                            with st.expander("Nguồn tài liệu được hệ thống truy xuất"):
                                for i, doc in enumerate(docs, start=1):
                                    st.markdown(f"**Nguồn {i}:**")
                                    st.write(doc.page_content[:900])

                        except Exception as e:
                            st.error("Không thể tạo câu trả lời từ chatbot.")
                            st.code(str(e))

except FileNotFoundError as e:
    st.error("Chưa tìm thấy file mô hình hoặc file báo cáo cần thiết.")
    st.write("Bạn cần chạy lần lượt các lệnh sau trong Terminal:")
    st.code("""
python -m src.train_model
python -m src.evaluate_model
python -m src.explain_model
""")
    st.write("Chi tiết lỗi:")
    st.code(str(e))

except Exception as e:
    st.error("Ứng dụng gặp lỗi trong quá trình khởi chạy.")
    st.write("Chi tiết lỗi:")
    st.code(str(e))