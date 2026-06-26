import os
from collections import Counter

import joblib

from imblearn.over_sampling import SMOTE

from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score

from xgboost import XGBClassifier

from src.preprocessing import load_data, clean_data, split_and_scale


def apply_smote_safely(X_train, y_train):
    """
    Áp dụng SMOTE nếu dữ liệu bị mất cân bằng.
    Nếu dữ liệu quá ít hoặc không cần SMOTE thì bỏ qua.
    """
    class_counts = Counter(y_train)

    print("\nPhân bố lớp trước SMOTE:")
    print(class_counts)

    if len(class_counts) < 2:
        raise ValueError("Dữ liệu chỉ có 1 lớp nhãn. Không thể huấn luyện mô hình phân loại.")

    min_count = min(class_counts.values())
    max_count = max(class_counts.values())

    if min_count == max_count:
        print("Dữ liệu đã cân bằng, bỏ qua SMOTE.")
        return X_train, y_train

    if min_count < 2:
        print("Lớp thiểu số có quá ít mẫu, bỏ qua SMOTE để tránh lỗi.")
        return X_train, y_train

    k_neighbors = min(5, min_count - 1)

    smote = SMOTE(
        random_state=42,
        k_neighbors=k_neighbors
    )

    X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

    print("\nPhân bố lớp sau SMOTE:")
    print(Counter(y_resampled))

    return X_resampled, y_resampled


def train_models():
    os.makedirs("models", exist_ok=True)

    print("Đang đọc dữ liệu...")

    df = load_data()
    df = clean_data(df)

    X_train, X_test, y_train, y_test, scaler, feature_names, target_col = split_and_scale(df)

    print("\nThông tin dữ liệu:")
    print("Cột nhãn:", target_col)
    print("Số mẫu train:", len(X_train))
    print("Số mẫu test:", len(X_test))
    print("Số đặc trưng:", len(feature_names))

    X_train_final, y_train_final = apply_smote_safely(X_train, y_train)

    models = {
        "KNN": {
            "model": KNeighborsClassifier(),
            "params": {
                "n_neighbors": [3, 5, 7],
                "weights": ["uniform", "distance"]
            }
        },
        "Random Forest": {
            "model": RandomForestClassifier(random_state=42),
            "params": {
                "n_estimators": [100, 200],
                "max_depth": [None, 5, 10]
            }
        },
        "XGBoost": {
            "model": XGBClassifier(
                random_state=42,
                eval_metric="logloss"
            ),
            "params": {
                "n_estimators": [100, 200],
                "max_depth": [3, 5],
                "learning_rate": [0.05, 0.1]
            }
        }
    }

    best_model = None
    best_name = None
    best_f1 = -1
    results = []

    for name, config in models.items():
        print("\n" + "=" * 60)
        print("Đang huấn luyện mô hình:", name)

        grid = GridSearchCV(
            estimator=config["model"],
            param_grid=config["params"],
            scoring="f1_weighted",
            cv=5,
            n_jobs=-1
        )

        grid.fit(X_train_final, y_train_final)

        model = grid.best_estimator_

        y_pred = model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        pre = precision_score(y_test, y_pred, average="weighted", zero_division=0)
        rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)
        f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

        print("Tham số tốt nhất:", grid.best_params_)
        print("Accuracy:", acc)
        print("Precision:", pre)
        print("Recall:", rec)
        print("F1-score:", f1)

        results.append({
            "model_name": name,
            "best_params": grid.best_params_,
            "accuracy": acc,
            "precision": pre,
            "recall": rec,
            "f1": f1
        })

        if f1 > best_f1:
            best_f1 = f1
            best_model = model
            best_name = name

    print("\n" + "=" * 60)
    print("Mô hình tốt nhất:", best_name)
    print("F1-score tốt nhất:", best_f1)

    joblib.dump(best_model, "models/best_model.pkl")
    joblib.dump(best_name, "models/best_model_name.pkl")
    joblib.dump(scaler, "models/scaler.pkl")
    joblib.dump(feature_names, "models/feature_names.pkl")
    joblib.dump(results, "models/training_results.pkl")

    print("\nĐã lưu các file model vào thư mục models:")
    print("- models/best_model.pkl")
    print("- models/best_model_name.pkl")
    print("- models/scaler.pkl")
    print("- models/feature_names.pkl")
    print("- models/training_results.pkl")


if __name__ == "__main__":
    train_models()