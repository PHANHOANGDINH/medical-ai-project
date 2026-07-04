import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from imblearn.over_sampling import SMOTE


DATA_PATH = "data/raw/heart.csv"
MODEL_DIR = "models"


def find_target_column(df):
    possible_targets = ["target", "HeartDisease", "heart_disease", "output"]

    for col in possible_targets:
        if col in df.columns:
            return col

    raise ValueError(
        "Không tìm thấy cột nhãn. Hãy kiểm tra dataset có cột target hoặc HeartDisease không."
    )


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    print("Đang đọc dữ liệu...")
    df = pd.read_csv(DATA_PATH)

    target_col = find_target_column(df)

    print("Cột nhãn:", target_col)
    print("Kích thước dữ liệu ban đầu:", df.shape)

    df = df.drop_duplicates()

    # Xử lý giá trị thiếu nếu có
    for col in df.columns:
        if df[col].isnull().sum() > 0:
            if df[col].dtype in ["int64", "float64"]:
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(df[col].mode()[0])

    X = df.drop(columns=[target_col])
    y = df[target_col]

    feature_names = list(X.columns)

    print("Danh sách đặc trưng:")
    print(feature_names)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(
        X_train_scaled,
        y_train
    )

    models = {
        "KNN": KNeighborsClassifier(
            n_neighbors=5
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            max_depth=None
        ),
        "XGBoost": XGBClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=3,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=42
        )
    }

    trained_models = {}
    training_results = {}

    best_model_name = None
    best_model = None
    best_f1 = -1

    print("\nBắt đầu huấn luyện các mô hình...")

    for model_name, model in models.items():
        print(f"\nĐang huấn luyện: {model_name}")

        model.fit(X_train_resampled, y_train_resampled)

        y_pred = model.predict(X_test_scaled)

        acc = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        trained_models[model_name] = model

        training_results[model_name] = {
            "Accuracy": round(acc, 4),
            "Precision": round(precision, 4),
            "Recall": round(recall, 4),
            "F1-score": round(f1, 4)
        }

        print("Accuracy:", round(acc, 4))
        print("Precision:", round(precision, 4))
        print("Recall:", round(recall, 4))
        print("F1-score:", round(f1, 4))

        if f1 > best_f1:
            best_f1 = f1
            best_model_name = model_name
            best_model = model

    print("\nMô hình tốt nhất:", best_model_name)
    print("F1-score tốt nhất:", round(best_f1, 4))

    joblib.dump(trained_models, os.path.join(MODEL_DIR, "all_models.pkl"))
    joblib.dump(best_model, os.path.join(MODEL_DIR, "best_model.pkl"))
    joblib.dump(best_model_name, os.path.join(MODEL_DIR, "best_model_name.pkl"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))
    joblib.dump(feature_names, os.path.join(MODEL_DIR, "feature_names.pkl"))
    joblib.dump(training_results, os.path.join(MODEL_DIR, "training_results.pkl"))

    print("\nĐã lưu các file:")
    print("models/all_models.pkl")
    print("models/best_model.pkl")
    print("models/best_model_name.pkl")
    print("models/scaler.pkl")
    print("models/feature_names.pkl")
    print("models/training_results.pkl")


if __name__ == "__main__":
    main()