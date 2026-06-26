# Hệ thống hỗ trợ đánh giá nguy cơ bệnh tim mạch

Đây là đề tài kết thúc môn Trí tuệ nhân tạo. Hệ thống sử dụng học máy để hỗ trợ đánh giá nguy cơ bệnh tim mạch, kết hợp giải thích kết quả và chatbot RAG dựa trên tài liệu y khoa.

## Công nghệ sử dụng

- Python
- Pandas, NumPy
- Scikit-learn
- Imbalanced-learn
- XGBoost
- SHAP
- Streamlit
- LangChain
- ChromaDB
- Google Gemini API

## Chức năng chính

- Nhập thông tin sức khỏe bằng giao diện thân thiện
- Dự đoán mức nguy cơ bằng mô hình học máy
- Giải thích kết quả bằng ngôn ngữ dễ hiểu
- So sánh các mô hình KNN, Random Forest, XGBoost
- Hiển thị Confusion Matrix, ROC Curve, SHAP phục vụ báo cáo
- Chatbot RAG hỏi đáp sức khỏe dựa trên tài liệu y khoa

## Cài đặt

Tạo môi trường ảo:

```bash
python -m venv .venv