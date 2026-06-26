import os
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_auc_score,
    RocCurveDisplay
)

from src.preprocessing import load_data, clean_data, split_and_scale


def evaluate_model():
    os.makedirs("reports", exist_ok=True)

    print("Đang đọc dữ liệu...")

    df = load_data()
    df = clean_data(df)

    X_train, X_test, y_train, y_test, scaler, feature_names, target_col = split_and_scale(df)

    print("Đang tải mô hình đã huấn luyện...")

    model = joblib.load("models/best_model.pkl")
    model_name = joblib.load("models/best_model_name.pkl")

    print("\n===== THÔNG TIN MÔ HÌNH =====")
    print("Mô hình:", model_name)
    print("Cột nhãn:", target_col)
    print("Số mẫu kiểm thử:", len(X_test))

    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    recall = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    print("\n===== CHỈ SỐ ĐÁNH GIÁ =====")
    print("Accuracy:", accuracy)
    print("Precision:", precision)
    print("Recall:", recall)
    print("F1-score:", f1)

    print("\n===== CLASSIFICATION REPORT =====")
    print(classification_report(y_test, y_pred, zero_division=0))

    cm = confusion_matrix(y_test, y_pred)

    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt="d")
    plt.xlabel("Dự đoán")
    plt.ylabel("Thực tế")
    plt.title(f"Confusion Matrix - {model_name}")
    plt.tight_layout()
    plt.savefig("reports/confusion_matrix.png")
    plt.show()

    print("\nĐã lưu ảnh Confusion Matrix tại:")
    print("reports/confusion_matrix.png")

    if hasattr(model, "predict_proba"):
        try:
            y_proba = model.predict_proba(X_test)[:, 1]
            roc_auc = roc_auc_score(y_test, y_proba)

            print("\nROC-AUC:", roc_auc)

            RocCurveDisplay.from_estimator(model, X_test, y_test)
            plt.title(f"ROC Curve - {model_name}")
            plt.tight_layout()
            plt.savefig("reports/roc_curve.png")
            plt.show()

            print("Đã lưu ảnh ROC Curve tại:")
            print("reports/roc_curve.png")

        except Exception as e:
            print("Không thể vẽ ROC Curve:", e)


if __name__ == "__main__":
    evaluate_model()