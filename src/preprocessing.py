import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder


DATA_PATH = "data/raw/heart.csv"


def load_data(path=DATA_PATH):
    df = pd.read_csv(path)
    return df


def clean_data(df):
    # Chuẩn hóa tên cột: bỏ khoảng trắng dư
    df.columns = df.columns.str.strip()

    # Xóa dòng trùng
    df = df.drop_duplicates()

    # Một số dataset hay dùng dấu ? hoặc chuỗi rỗng để biểu diễn missing
    df = df.replace(["?", "NA", "N/A", "null", "None", ""], pd.NA)

    # Xử lý giá trị thiếu
    for col in df.columns:
        if df[col].isnull().sum() > 0:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(df[col].mode()[0])

    return df


def detect_target_column(df):
    possible_targets = [
        "target",
        "Target",
        "HeartDisease",
        "heartdisease",
        "output",
        "Output",
        "class",
        "Class",
        "diagnosis",
        "Diagnosis"
    ]

    for col in possible_targets:
        if col in df.columns:
            return col

    # Nếu không tìm thấy tên quen thuộc, lấy cột cuối cùng làm nhãn
    return df.columns[-1]


def split_and_scale(df):
    target_col = detect_target_column(df)

    print("Cột nhãn được sử dụng là:", target_col)

    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Nếu nhãn là chữ, mã hóa thành số
    if y.dtype == "object":
        encoder = LabelEncoder()
        y = encoder.fit_transform(y)

    # Mã hóa các cột dạng chữ trong X
    X = pd.get_dummies(X, drop_first=True)

    # Chia train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # Chuẩn hóa dữ liệu
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    feature_names = list(X.columns)

    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_names, target_col


if __name__ == "__main__":
    df = load_data()
    print("Đã đọc dữ liệu thành công.")
    print("Kích thước ban đầu:", df.shape)

    df = clean_data(df)
    print("Kích thước sau khi làm sạch:", df.shape)

    X_train, X_test, y_train, y_test, scaler, feature_names, target_col = split_and_scale(df)

    print("Số dòng train:", len(X_train))
    print("Số dòng test:", len(X_test))
    print("Số đặc trưng sau xử lý:", len(feature_names))
    print("Danh sách đặc trưng:")
    print(feature_names)