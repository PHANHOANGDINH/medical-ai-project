import os
import json
import re

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


load_dotenv()


ALLOWED_FIELDS = {
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal"
}


def extract_json_from_text(text):
    text = text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("AI không trả về JSON hợp lệ.")

    return json.loads(match.group(0))


def normalize_parsed_values(parsed):
    extracted = parsed.get("extracted", {})
    notes = parsed.get("notes", [])

    clean_data = {}

    for key, value in extracted.items():
        if key not in ALLOWED_FIELDS:
            continue

        if value is None or value == "":
            continue

        try:
            if key in [
                "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
                "thalach", "exang", "slope", "ca", "thal"
            ]:
                clean_data[key] = int(float(value))
            elif key == "oldpeak":
                clean_data[key] = float(value)
        except Exception:
            continue

    return clean_data, notes


def parse_health_text_with_ai(user_text):
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError("Chưa có GOOGLE_API_KEY trong file .env")

    prompt = ChatPromptTemplate.from_template("""
Bạn là bộ trích xuất dữ liệu cho hệ thống dự đoán nguy cơ tim mạch.

Nhiệm vụ:
Đọc câu nói/câu văn của người dùng bằng tiếng Việt và trích xuất các chỉ số sức khỏe thành JSON.

QUAN TRỌNG:
- Chỉ trả về JSON, không giải thích bên ngoài JSON.
- Không tự bịa chỉ số nếu người dùng không nói.
- Chỉ thêm field nếu có thông tin rõ ràng hoặc suy luận rất chắc chắn.
- Nếu thiếu thông tin, ghi vào "notes".
- Nếu người dùng nói "nam" thì sex = 1.
- Nếu người dùng nói "nữ" thì sex = 0.
- Nếu nói huyết áp 155 thì hiểu là trestbps = 155.
- Nếu nói cholesterol/mỡ máu toàn phần 250 thì chol = 250.
- Nếu nói đường huyết cao, đường đói cao, trên 120 thì fbs = 1.
- Nếu nói đường huyết bình thường hoặc không cao thì fbs = 0.
- Nếu nói đau ngực khi vận động/gắng sức thì exang = 1.
- Nếu nói không đau ngực khi vận động thì exang = 0.
- Nếu nói điện tâm đồ bình thường thì restecg = 0.
- Nếu nói điện tâm đồ bất thường/ST-T bất thường thì restecg = 1.
- Nếu nói phì đại thất trái thì restecg = 2.
- Nếu nói ST dốc lên thì slope = 0.
- Nếu nói ST phẳng thì slope = 1.
- Nếu nói ST dốc xuống thì slope = 2.
- Nếu nói số mạch chính/chụp mạch là 0-4 thì ca = số đó.
- Nếu nói thal bình thường thì thal = 1.
- Nếu nói thal khiếm khuyết cố định thì thal = 2.
- Nếu nói thal khiếm khuyết hồi phục/có thể hồi phục thì thal = 3.
- Nếu không rõ thal thì thal = 0 chỉ khi người dùng có nói "không rõ thal".

Với loại đau ngực cp:
- đau thắt ngực điển hình => cp = 0
- đau thắt ngực không điển hình => cp = 1
- đau ngực không giống bệnh tim/không do tim rõ => cp = 2
- không rõ hoặc không có triệu chứng đau ngực => cp = 3
- Nếu người dùng chỉ nói "đau ngực khi vận động", ưu tiên điền exang = 1, không bắt buộc điền cp nếu không rõ loại đau ngực.

Schema JSON bắt buộc:
{{
  "extracted": {{
    "age": số hoặc null,
    "sex": 0 hoặc 1 hoặc null,
    "cp": 0 hoặc 1 hoặc 2 hoặc 3 hoặc null,
    "trestbps": số hoặc null,
    "chol": số hoặc null,
    "fbs": 0 hoặc 1 hoặc null,
    "restecg": 0 hoặc 1 hoặc 2 hoặc null,
    "thalach": số hoặc null,
    "exang": 0 hoặc 1 hoặc null,
    "oldpeak": số hoặc null,
    "slope": 0 hoặc 1 hoặc 2 hoặc null,
    "ca": 0 hoặc 1 hoặc 2 hoặc 3 hoặc 4 hoặc null,
    "thal": 0 hoặc 1 hoặc 2 hoặc 3 hoặc null
  }},
  "notes": [
    "ghi chú ngắn nếu thiếu hoặc không chắc"
  ]
}}

Câu người dùng:
{user_text}

JSON:
""")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=api_key
    )

    chain = prompt | llm

    response = chain.invoke({
        "user_text": user_text
    })

    parsed = extract_json_from_text(response.content)
    clean_data, notes = normalize_parsed_values(parsed)

    return clean_data, notes