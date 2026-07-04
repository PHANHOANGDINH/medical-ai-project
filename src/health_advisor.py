import os
import json


def add_item(items, level, title, value, explanation, advice):
    items.append(
        {
            "level": level,
            "title": title,
            "value": value,
            "explanation": explanation,
            "advice": advice,
        }
    )


def analyze_health_indicators(data):
    """
    Phân tích từng chỉ số người dùng nhập theo luật tham khảo.
    Hàm này không chẩn đoán bệnh, chỉ giúp hệ thống giải thích chỉ số dễ hiểu hơn.

    data gồm các khóa:
    age, sex, cp, trestbps, chol, fbs, restecg, thalach,
    exang, oldpeak, slope, ca, thal
    """

    danger_items = []
    warning_items = []
    normal_items = []
    general_advice = []

    age = int(float(data.get("age", 0)))
    sex = int(float(data.get("sex", 0)))
    cp = int(float(data.get("cp", 0)))
    trestbps = int(float(data.get("trestbps", 0)))
    chol = int(float(data.get("chol", 0)))
    fbs = int(float(data.get("fbs", 0)))
    restecg = int(float(data.get("restecg", 0)))
    thalach = int(float(data.get("thalach", 0)))
    exang = int(float(data.get("exang", 0)))
    oldpeak = float(data.get("oldpeak", 0))
    slope = int(float(data.get("slope", 0)))
    ca = int(float(data.get("ca", 0)))
    thal = int(float(data.get("thal", 0)))

    sex_text = "Nam" if sex == 1 else "Nữ"

    # 1. Tuổi + giới tính
    if age >= 60:
        if sex == 1:
            explanation = (
                "Nam giới ở nhóm tuổi từ 60 trở lên là nhóm cần theo dõi kỹ hơn về sức khỏe tim mạch, "
                "đặc biệt khi đi kèm huyết áp cao, cholesterol cao hoặc đau ngực khi vận động."
            )
        else:
            explanation = (
                "Nữ giới từ 60 tuổi trở lên vẫn cần theo dõi nguy cơ tim mạch kỹ hơn, "
                "nhất là khi có thêm huyết áp cao, cholesterol cao hoặc bất thường điện tâm đồ."
            )

        add_item(
            warning_items,
            "warning",
            "Tuổi và giới tính",
            f"{age} tuổi - {sex_text}",
            explanation,
            "Nên kiểm tra sức khỏe định kỳ, theo dõi huyết áp, mỡ máu và trao đổi với nhân viên y tế nếu có triệu chứng bất thường.",
        )
    elif age >= 45:
        add_item(
            warning_items,
            "warning",
            "Tuổi và giới tính",
            f"{age} tuổi - {sex_text}",
            "Độ tuổi này nên bắt đầu quan tâm hơn đến các yếu tố nguy cơ tim mạch, đặc biệt khi có nhiều chỉ số cùng bất thường.",
            "Nên duy trì vận động, ăn uống lành mạnh, kiểm tra huyết áp và mỡ máu định kỳ.",
        )
    else:
        add_item(
            normal_items,
            "normal",
            "Tuổi và giới tính",
            f"{age} tuổi - {sex_text}",
            "Tuổi hiện tại chưa thuộc nhóm cao tuổi trong đánh giá tham khảo của hệ thống.",
            "Vẫn nên duy trì lối sống lành mạnh và theo dõi sức khỏe định kỳ.",
        )

    # 2. Loại đau ngực
    cp_map = {
        0: "Đau thắt ngực điển hình",
        1: "Đau thắt ngực không điển hình",
        2: "Đau ngực không giống bệnh tim",
        3: "Không rõ hoặc không có triệu chứng",
    }
    cp_text = cp_map.get(cp, "Không rõ")

    if cp in [0, 1]:
        add_item(
            warning_items,
            "warning",
            "Loại đau ngực",
            cp_text,
            "Triệu chứng đau ngực là thông tin quan trọng trong đánh giá nguy cơ tim mạch.",
            "Nếu đau ngực lặp lại, đau khi gắng sức, đau lan tay/hàm/lưng hoặc kèm khó thở, nên liên hệ cơ sở y tế.",
        )
    elif cp == 3:
        add_item(
            warning_items,
            "warning",
            "Loại đau ngực",
            cp_text,
            "Thông tin đau ngực chưa rõ ràng nên kết quả đánh giá có thể cần thận trọng hơn.",
            "Nếu thật sự có triệu chứng đau ngực, nên ghi nhận thời điểm đau, mức độ đau và yếu tố làm tăng/giảm đau.",
        )
    else:
        add_item(
            normal_items,
            "normal",
            "Loại đau ngực",
            cp_text,
            "Thông tin đau ngực hiện chưa nằm trong nhóm cảnh báo cao của hệ thống.",
            "Tiếp tục theo dõi nếu xuất hiện triệu chứng mới.",
        )

    # 3. Huyết áp lúc nghỉ
    if trestbps >= 180:
        add_item(
            danger_items,
            "danger",
            "Huyết áp lúc nghỉ",
            f"{trestbps} mmHg",
            "Huyết áp rất cao là dấu hiệu cần đặc biệt chú ý.",
            "Nên đo lại sau khi nghỉ ngơi. Nếu vẫn rất cao hoặc kèm đau ngực, khó thở, đau đầu dữ dội, yếu liệt, cần liên hệ cơ sở y tế ngay.",
        )
    elif trestbps >= 140:
        add_item(
            danger_items,
            "danger",
            "Huyết áp lúc nghỉ",
            f"{trestbps} mmHg",
            "Huyết áp lúc nghỉ đang ở mức cao theo ngưỡng tham khảo.",
            "Nên theo dõi huyết áp nhiều thời điểm, ghi lại kết quả và trao đổi với bác sĩ hoặc nhân viên y tế.",
        )
    elif trestbps >= 130:
        add_item(
            warning_items,
            "warning",
            "Huyết áp lúc nghỉ",
            f"{trestbps} mmHg",
            "Huyết áp đang ở mức cần theo dõi.",
            "Nên giảm ăn mặn, ngủ đủ, vận động phù hợp và kiểm tra lại huyết áp định kỳ.",
        )
    elif trestbps >= 120:
        add_item(
            warning_items,
            "warning",
            "Huyết áp lúc nghỉ",
            f"{trestbps} mmHg",
            "Huyết áp hơi cao so với mức tối ưu.",
            "Nên duy trì lối sống lành mạnh và theo dõi thêm.",
        )
    else:
        add_item(
            normal_items,
            "normal",
            "Huyết áp lúc nghỉ",
            f"{trestbps} mmHg",
            "Huyết áp lúc nghỉ đang ở mức tương đối ổn theo ngưỡng tham khảo.",
            "Tiếp tục duy trì chế độ sinh hoạt lành mạnh.",
        )

    # 4. Cholesterol
    if chol >= 240:
        add_item(
            danger_items,
            "danger",
            "Cholesterol",
            f"{chol} mg/dL",
            "Cholesterol toàn phần đang ở mức cao theo ngưỡng tham khảo.",
            "Nên kiểm tra bộ mỡ máu đầy đủ gồm LDL, HDL, triglycerides và trao đổi với nhân viên y tế.",
        )
    elif chol >= 200:
        add_item(
            warning_items,
            "warning",
            "Cholesterol",
            f"{chol} mg/dL",
            "Cholesterol đang ở mức cần chú ý.",
            "Nên điều chỉnh chế độ ăn, hạn chế chất béo bão hòa, tăng rau xanh và kiểm tra lại mỡ máu.",
        )
    elif chol <= 100:
        add_item(
            warning_items,
            "warning",
            "Cholesterol",
            f"{chol} mg/dL",
            "Cholesterol nhập vào khá thấp, có thể cần kiểm tra lại dữ liệu hoặc đơn vị đo.",
            "Nên đảm bảo chỉ số nhập đúng đơn vị mg/dL.",
        )
    else:
        add_item(
            normal_items,
            "normal",
            "Cholesterol",
            f"{chol} mg/dL",
            "Cholesterol toàn phần chưa vượt ngưỡng cảnh báo cao của hệ thống.",
            "Tiếp tục duy trì chế độ ăn uống và vận động phù hợp.",
        )

    # 5. Đường huyết lúc đói
    if fbs == 1:
        add_item(
            warning_items,
            "warning",
            "Đường huyết lúc đói",
            "Trên 120 mg/dL",
            "Đường huyết lúc đói cao là yếu tố cần theo dõi vì có thể liên quan đến rối loạn chuyển hóa.",
            "Nên kiểm tra lại đường huyết hoặc HbA1c nếu có điều kiện, đặc biệt khi đi kèm huyết áp cao hoặc cholesterol cao.",
        )
    else:
        add_item(
            normal_items,
            "normal",
            "Đường huyết lúc đói",
            "Không vượt 120 mg/dL",
            "Đường huyết lúc đói chưa vượt ngưỡng cảnh báo trong bộ dữ liệu.",
            "Tiếp tục duy trì chế độ ăn uống hợp lý.",
        )

    # 6. Điện tâm đồ lúc nghỉ
    if restecg in [1, 2]:
        add_item(
            warning_items,
            "warning",
            "Điện tâm đồ lúc nghỉ",
            "Có bất thường",
            "Kết quả điện tâm đồ bất thường là yếu tố nên được đọc và đánh giá bởi nhân viên y tế.",
            "Nên mang kết quả điện tâm đồ đến cơ sở y tế nếu có triệu chứng như đau ngực, hồi hộp, khó thở.",
        )
    else:
        add_item(
            normal_items,
            "normal",
            "Điện tâm đồ lúc nghỉ",
            "Bình thường",
            "Điện tâm đồ lúc nghỉ không có bất thường theo dữ liệu nhập.",
            "Tiếp tục theo dõi nếu có triệu chứng mới.",
        )

    # 7. Nhịp tim tối đa
    estimated_max_hr = 220 - age

    if thalach < 90:
        add_item(
            warning_items,
            "warning",
            "Nhịp tim tối đa",
            f"{thalach} bpm",
            "Nhịp tim tối đa nhập vào khá thấp, cần xem lại bối cảnh đo và tình trạng sức khỏe.",
            "Nếu thường xuyên mệt, khó thở, chóng mặt hoặc đau ngực khi vận động, nên trao đổi với nhân viên y tế.",
        )
    elif thalach > estimated_max_hr + 20:
        add_item(
            warning_items,
            "warning",
            "Nhịp tim tối đa",
            f"{thalach} bpm",
            "Nhịp tim tối đa cao hơn nhiều so với giá trị ước tính theo tuổi.",
            "Nên kiểm tra lại dữ liệu nhập và theo dõi nếu có hồi hộp, đau ngực hoặc khó thở.",
        )
    else:
        add_item(
            normal_items,
            "normal",
            "Nhịp tim tối đa",
            f"{thalach} bpm",
            "Nhịp tim tối đa chưa được hệ thống đánh dấu là bất thường rõ.",
            "Nên đánh giá thêm cùng các chỉ số khác và triệu chứng thực tế.",
        )

    # 8. Đau thắt ngực khi vận động
    if exang == 1:
        add_item(
            danger_items,
            "danger",
            "Đau thắt ngực khi vận động",
            "Có",
            "Đau thắt ngực khi vận động là dấu hiệu cần chú ý trong đánh giá nguy cơ tim mạch.",
            "Nên hạn chế gắng sức quá mức và liên hệ cơ sở y tế nếu đau ngực xuất hiện thường xuyên, kéo dài hoặc kèm khó thở.",
        )
    else:
        add_item(
            normal_items,
            "normal",
            "Đau thắt ngực khi vận động",
            "Không",
            "Không ghi nhận đau thắt ngực khi vận động trong dữ liệu nhập.",
            "Tiếp tục theo dõi nếu có triệu chứng mới khi hoạt động thể lực.",
        )

    # 9. Oldpeak
    if oldpeak >= 2.0:
        add_item(
            danger_items,
            "danger",
            "Độ chênh ST / Oldpeak",
            f"{oldpeak:g}",
            "Oldpeak cao cho thấy có thay đổi ST đáng chú ý trong dữ liệu đầu vào của mô hình.",
            "Nên xem xét chỉ số này cùng kết quả điện tâm đồ và triệu chứng thực tế; nếu có đau ngực hoặc khó thở, nên đi khám.",
        )
    elif oldpeak >= 1.0:
        add_item(
            warning_items,
            "warning",
            "Độ chênh ST / Oldpeak",
            f"{oldpeak:g}",
            "Oldpeak ở mức cần theo dõi.",
            "Nên đánh giá cùng các yếu tố khác như đau ngực khi vận động, điện tâm đồ và huyết áp.",
        )
    else:
        add_item(
            normal_items,
            "normal",
            "Độ chênh ST / Oldpeak",
            f"{oldpeak:g}",
            "Oldpeak thấp, chưa nằm trong nhóm cảnh báo của hệ thống.",
            "Tiếp tục theo dõi cùng các chỉ số khác.",
        )

    # 10. Slope
    slope_map = {
        0: "Dốc lên",
        1: "Phẳng",
        2: "Dốc xuống",
    }
    slope_text = slope_map.get(slope, "Không rõ")

    if slope in [1, 2]:
        add_item(
            warning_items,
            "warning",
            "Độ dốc đoạn ST",
            slope_text,
            "Dạng phẳng hoặc dốc xuống thường được hệ thống xem là yếu tố cần chú ý hơn so với dốc lên.",
            "Nên đánh giá cùng oldpeak, điện tâm đồ và triệu chứng khi vận động.",
        )
    else:
        add_item(
            normal_items,
            "normal",
            "Độ dốc đoạn ST",
            slope_text,
            "Độ dốc đoạn ST chưa nằm trong nhóm cảnh báo của hệ thống.",
            "Tiếp tục theo dõi cùng các chỉ số khác.",
        )

    # 11. CA
    if ca >= 2:
        add_item(
            danger_items,
            "danger",
            "Số mạch chính bị ảnh hưởng",
            f"{ca}",
            "Số mạch chính được ghi nhận cao là yếu tố làm tăng mức chú ý trong mô hình.",
            "Nên tham khảo ý kiến bác sĩ nếu chỉ số này đến từ kết quả cận lâm sàng thực tế.",
        )
    elif ca == 1:
        add_item(
            warning_items,
            "warning",
            "Số mạch chính bị ảnh hưởng",
            f"{ca}",
            "Có ghi nhận mạch chính liên quan trong dữ liệu, cần theo dõi cùng các yếu tố khác.",
            "Nên xem xét kết hợp với triệu chứng đau ngực và kết quả kiểm tra tim mạch.",
        )
    else:
        add_item(
            normal_items,
            "normal",
            "Số mạch chính bị ảnh hưởng",
            f"{ca}",
            "Chỉ số này chưa nằm trong nhóm cảnh báo của hệ thống.",
            "Tiếp tục theo dõi các yếu tố nguy cơ khác.",
        )

    # 12. Thal
    thal_map = {
        0: "Không rõ / không ghi nhận",
        1: "Bình thường",
        2: "Khiếm khuyết cố định",
        3: "Khiếm khuyết có thể hồi phục",
    }
    thal_text = thal_map.get(thal, "Không rõ")

    if thal in [2, 3]:
        add_item(
            warning_items,
            "warning",
            "Kết quả Thal",
            thal_text,
            "Chỉ số thal bất thường là yếu tố cần chú ý trong bộ dữ liệu dự đoán.",
            "Nên đánh giá cùng bác sĩ nếu đây là kết quả xét nghiệm hoặc kiểm tra chuyên sâu.",
        )
    else:
        add_item(
            normal_items,
            "normal",
            "Kết quả Thal",
            thal_text,
            "Chỉ số này chưa nằm trong nhóm cảnh báo của hệ thống.",
            "Tiếp tục theo dõi cùng các yếu tố khác.",
        )

    # Lời khuyên tổng quát
    general_advice.append(
        "Kết quả chỉ mang tính tham khảo, không thay thế chẩn đoán hoặc điều trị của bác sĩ."
    )
    general_advice.append(
        "Nên theo dõi huyết áp, cholesterol, đường huyết và khám sức khỏe định kỳ."
    )
    general_advice.append(
        "Duy trì ăn uống lành mạnh, vận động phù hợp, ngủ đủ và tránh hút thuốc lá."
    )
    general_advice.append(
        "Nếu có đau ngực dữ dội, khó thở, ngất, yếu liệt hoặc triệu chứng bất thường, cần liên hệ cơ sở y tế ngay."
    )

    return {
        "danger": danger_items,
        "warning": warning_items,
        "normal": normal_items,
        "general_advice": general_advice,
    }


def get_overall_explanation_by_probability(probability):
    """
    probability là xác suất nguy cơ từ mô hình, ví dụ 0.82.
    """

    if probability is None:
        return {
            "level": "unknown",
            "title": "Chưa có xác suất",
            "message": (
                "Mô hình hiện chưa trả về xác suất nguy cơ, hệ thống chỉ hiển thị kết quả phân loại tham khảo."
            ),
        }

    probability = float(probability)

    if probability >= 0.7:
        return {
            "level": "high",
            "title": "Nguy cơ cao",
            "message": (
                "Mô hình đánh giá người dùng đang có nguy cơ cao. "
                "Nên xem kỹ các chỉ số cảnh báo và trao đổi với nhân viên y tế để được đánh giá chính xác hơn."
            ),
        }

    if probability >= 0.4:
        return {
            "level": "medium",
            "title": "Cần theo dõi",
            "message": (
                "Mô hình đánh giá người dùng đang ở mức cần theo dõi. "
                "Một số chỉ số có thể chưa ở mức nguy hiểm nhưng vẫn nên được kiểm tra định kỳ."
            ),
        }

    return {
        "level": "low",
        "title": "Nguy cơ thấp",
        "message": (
            "Mô hình đánh giá nguy cơ hiện tại ở mức thấp. "
            "Tuy nhiên, vẫn nên duy trì lối sống lành mạnh và theo dõi sức khỏe định kỳ."
        ),
    }


def generate_suggested_questions(indicator_analysis):
    """
    Sinh câu hỏi gợi ý cho chatbot dựa trên các chỉ số đang nguy cơ cao/cần theo dõi.
    """

    questions = []
    all_risk_items = indicator_analysis.get("danger", []) + indicator_analysis.get("warning", [])

    for item in all_risk_items:
        title = item.get("title", "")

        if "Huyết áp" in title:
            questions.append("Huyết áp cao ảnh hưởng như thế nào đến tim mạch?")
        elif "Cholesterol" in title:
            questions.append("Cholesterol cao có nguy hiểm không và nên theo dõi như thế nào?")
        elif "Đường huyết" in title:
            questions.append("Đường huyết cao có liên quan gì đến nguy cơ tim mạch?")
        elif "Đau thắt ngực" in title or "đau ngực" in title.lower():
            questions.append("Đau thắt ngực khi vận động có thể là dấu hiệu gì?")
        elif "Oldpeak" in title or "ST" in title:
            questions.append("Chỉ số Oldpeak và đoạn ST trong điện tâm đồ có ý nghĩa gì?")
        elif "Điện tâm đồ" in title:
            questions.append("Điện tâm đồ bất thường có ý nghĩa gì trong đánh giá tim mạch?")
        elif "Tuổi" in title:
            questions.append("Tuổi và giới tính ảnh hưởng như thế nào đến nguy cơ tim mạch?")

    unique_questions = []
    for question in questions:
        if question not in unique_questions:
            unique_questions.append(question)

    if not unique_questions:
        unique_questions = [
            "Tôi nên theo dõi những chỉ số nào để phòng ngừa bệnh tim mạch?",
            "Làm sao để duy trì lối sống tốt cho tim mạch?",
            "Khi nào đau ngực cần đi khám hoặc đi cấp cứu?",
        ]

    return unique_questions[:5]


def _get_text_value(input_data):
    sex_text = "Nam" if int(float(input_data.get("sex", 0))) == 1 else "Nữ"

    cp_map = {
        0: "Đau thắt ngực điển hình",
        1: "Đau thắt ngực không điển hình",
        2: "Đau ngực không giống bệnh tim",
        3: "Không rõ hoặc không có triệu chứng",
    }

    fbs_text = "Trên 120 mg/dL" if int(float(input_data.get("fbs", 0))) == 1 else "Không vượt 120 mg/dL"
    restecg_text = "Bất thường" if int(float(input_data.get("restecg", 0))) in [1, 2] else "Bình thường"
    exang_text = "Có" if int(float(input_data.get("exang", 0))) == 1 else "Không"

    slope_map = {
        0: "Dốc lên",
        1: "Phẳng",
        2: "Dốc xuống",
    }

    thal_map = {
        0: "Không rõ / không ghi nhận",
        1: "Bình thường",
        2: "Khiếm khuyết cố định",
        3: "Khiếm khuyết có thể hồi phục",
    }

    return {
        "tuoi": input_data.get("age"),
        "gioi_tinh": sex_text,
        "loai_dau_nguc": cp_map.get(int(float(input_data.get("cp", 0))), "Không rõ"),
        "huyet_ap_luc_nghi": f"{input_data.get('trestbps')} mmHg",
        "cholesterol": f"{input_data.get('chol')} mg/dL",
        "duong_huyet_luc_doi": fbs_text,
        "dien_tam_do_luc_nghi": restecg_text,
        "nhip_tim_toi_da": f"{input_data.get('thalach')} bpm",
        "dau_that_nguc_khi_van_dong": exang_text,
        "oldpeak": input_data.get("oldpeak"),
        "slope": slope_map.get(int(float(input_data.get("slope", 0))), "Không rõ"),
        "so_mach_chinh": input_data.get("ca"),
        "thal": thal_map.get(int(float(input_data.get("thal", 0))), "Không rõ"),
    }


def _flatten_indicator_analysis(indicator_analysis):
    danger = indicator_analysis.get("danger", [])
    warning = indicator_analysis.get("warning", [])
    normal = indicator_analysis.get("normal", [])

    return {
        "chi_so_nguy_co_cao": [
            {
                "ten": item.get("title"),
                "gia_tri": item.get("value"),
                "giai_thich": item.get("explanation"),
                "goi_y": item.get("advice"),
            }
            for item in danger
        ],
        "chi_so_can_theo_doi": [
            {
                "ten": item.get("title"),
                "gia_tri": item.get("value"),
                "giai_thich": item.get("explanation"),
                "goi_y": item.get("advice"),
            }
            for item in warning
        ],
        "chi_so_tuong_doi_on": [
            {
                "ten": item.get("title"),
                "gia_tri": item.get("value"),
            }
            for item in normal
        ],
    }


def _retrieve_rag_context(query, k=4):
    """
    Truy xuất thêm tài liệu từ ChromaDB nếu vector_db đã được build.
    Nếu RAG lỗi thì trả về ngữ cảnh rỗng để AI vẫn có thể tư vấn dựa trên chỉ số.
    """

    try:
        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings

        vector_db_folder = "vector_db"
        local_embedding_model = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

        embeddings = HuggingFaceEmbeddings(
            model_name=local_embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        vector_db = Chroma(
            persist_directory=vector_db_folder,
            embedding_function=embeddings,
        )

        retriever = vector_db.as_retriever(search_kwargs={"k": k})
        docs = retriever.invoke(query)

        context = "\n\n".join(
            [
                f"Nguồn: {doc.metadata}\nNội dung: {doc.page_content}"
                for doc in docs
            ]
        )

        return context, docs

    except Exception:
        return "", []


def generate_ai_health_advice(input_data, indicator_analysis, probability):
    """
    Dùng AI để tạo lời khuyên cá nhân hóa hơn dựa trên:
    - Tuổi, giới tính và các chỉ số người dùng nhập
    - Kết quả mô hình học máy
    - Phân tích rule-based từ analyze_health_indicators
    - Tài liệu RAG nếu có

    Hàm này vẫn giới hạn ở mức tư vấn tham khảo, không kê thuốc và không thay bác sĩ.
    """

    try:
        from dotenv import load_dotenv
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.prompts import ChatPromptTemplate
    except Exception as e:
        return (
            f"Chưa cài đủ thư viện để tạo lời khuyên AI. Lỗi: {e}",
            [],
        )

    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        return (
            "Chưa có GOOGLE_API_KEY trong file .env nên hệ thống chưa thể tạo lời khuyên AI cá nhân hóa.",
            [],
        )

    profile = _get_text_value(input_data)
    analysis = _flatten_indicator_analysis(indicator_analysis)

    if probability is None:
        risk_percent = "Không có xác suất"
    else:
        risk_percent = f"{round(float(probability) * 100, 2)}%"

    rag_query = (
        "tư vấn tim mạch cho người "
        f"{profile['gioi_tinh']} {profile['tuoi']} tuổi, "
        f"huyết áp {profile['huyet_ap_luc_nghi']}, "
        f"cholesterol {profile['cholesterol']}, "
        f"đau thắt ngực khi vận động {profile['dau_that_nguc_khi_van_dong']}, "
        f"đường huyết {profile['duong_huyet_luc_doi']}"
    )

    rag_context, docs = _retrieve_rag_context(rag_query, k=4)

    prompt = ChatPromptTemplate.from_template(
        """
Bạn là trợ lý AI hỗ trợ tư vấn tham khảo về nguy cơ tim mạch trong một hệ thống demo môn học.

NHIỆM VỤ:
Dựa trên thông tin người dùng, kết quả mô hình học máy, các chỉ số nguy cơ đã được hệ thống phát hiện và tài liệu tham khảo, hãy viết lời khuyên cá nhân hóa, dễ hiểu.

QUY TẮC:
- Có thể giải thích nguy cơ và đưa lời khuyên tham khảo.
- Không kê thuốc, không nêu liều thuốc, không thay thế bác sĩ.
- Không khẳng định chắc chắn người dùng mắc bệnh.
- Có thể nói "nên đi khám", "nên trao đổi với bác sĩ", "nên kiểm tra lại chỉ số".
- Nếu có đau ngực dữ dội, khó thở, ngất, yếu liệt, vã mồ hôi hoặc triệu chứng nghiêm trọng, phải khuyên liên hệ cơ sở y tế ngay.
- Với nữ giới, không tự suy đoán mang thai, mãn kinh hoặc tiền sử sản khoa nếu người dùng không nhập.
- Với nam giới, có thể nhắc nam giới và tuổi cao là yếu tố nền cần theo dõi nhưng không kết luận bệnh.
- Trả lời bằng tiếng Việt, rõ ràng, có cấu trúc.

THÔNG TIN NGƯỜI DÙNG:
{profile}

KẾT QUẢ MÔ HÌNH:
Xác suất nguy cơ từ mô hình học máy: {risk_percent}

PHÂN TÍCH CHỈ SỐ TỪ HỆ THỐNG:
{analysis}

TÀI LIỆU THAM KHẢO TRUY XUẤT TỪ RAG:
{rag_context}

YÊU CẦU ĐỊNH DẠNG:

### 1. Nhận xét tổng quan
Viết 2-3 câu về mức độ cần chú ý.

### 2. Các yếu tố đáng chú ý nhất
Liệt kê theo thứ tự ưu tiên. Giải thích vì sao tổ hợp chỉ số đó đáng chú ý.

### 3. Lời khuyên cá nhân hóa
Nêu rõ nên theo dõi chỉ số nào, thay đổi lối sống gì, khi nào nên đi khám.

### 4. Lưu ý
Nhắc lại đây là tư vấn tham khảo, không thay thế bác sĩ.

CÂU TRẢ LỜI:
"""
    )

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.2,
            google_api_key=api_key,
        )

        chain = prompt | llm

        response = chain.invoke(
            {
                "profile": json.dumps(profile, ensure_ascii=False, indent=2),
                "risk_percent": risk_percent,
                "analysis": json.dumps(analysis, ensure_ascii=False, indent=2),
                "rag_context": rag_context if rag_context else "Không có tài liệu RAG phù hợp được truy xuất.",
            }
        )

        return response.content, docs

    except Exception as e:
        return (
            f"Hiện chưa thể tạo lời khuyên AI cá nhân hóa. Lỗi: {e}",
            docs,
        )
