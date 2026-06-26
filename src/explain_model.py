import os
import joblib
import shap
import pandas as pd
import matplotlib.pyplot as plt

from src.preprocessing import load_data, clean_data, split_and_scale


def explain_model():
    os.makedirs("reports", exist_ok=True)

    print("Đang đọc dữ liệu...")

    df = load_data()
    df = clean_data(df)

    X_train, X_test, y_train, y_test, scaler, feature_names, target_col = split_and_scale(df)

    model = joblib.load("models/best_model.pkl")
    model_name = joblib.load("models/best_model_name.pkl")

    print("Mô hình đang giải thích:", model_name)

    X_train_df = pd.DataFrame(X_train, columns=feature_names)
    X_test_df = pd.DataFrame(X_test, columns=feature_names)

    # Lấy một phần dữ liệu để SHAP chạy nhanh hơn
    background = X_train_df.sample(
        n=min(50, len(X_train_df)),
        random_state=42
    )

    X_explain = X_test_df.sample(
        n=min(50, len(X_test_df)),
        random_state=42
    )

    # Hàm dự đoán xác suất lớp 1
    if hasattr(model, "predict_proba"):
        def predict_fn(data):
            return model.predict_proba(data)[:, 1]
    else:
        def predict_fn(data):
            return model.predict(data)

    print("Đang tính SHAP values, bước này có thể mất một lúc...")

    explainer = shap.Explainer(
        predict_fn,
        background
    )

    shap_values = explainer(X_explain)

    # Biểu đồ tổng quan mức độ ảnh hưởng của các đặc trưng
    plt.figure()
    shap.summary_plot(
        shap_values.values,
        X_explain,
        feature_names=feature_names,
        show=False
    )
    plt.tight_layout()
    plt.savefig("reports/shap_summary.png", bbox_inches="tight")
    plt.close()

    print("Đã lưu biểu đồ SHAP Summary:")
    print("reports/shap_summary.png")

    # Biểu đồ dạng bar dễ đưa vào báo cáo
    plt.figure()
    shap.summary_plot(
        shap_values.values,
        X_explain,
        feature_names=feature_names,
        plot_type="bar",
        show=False
    )
    plt.tight_layout()
    plt.savefig("reports/shap_bar.png", bbox_inches="tight")
    plt.close()

    print("Đã lưu biểu đồ SHAP Bar:")
    print("reports/shap_bar.png")


if __name__ == "__main__":
    explain_model()