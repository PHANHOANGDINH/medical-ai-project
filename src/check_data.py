import pandas as pd

DATA_PATH = "data/raw/heart.csv"

df = pd.read_csv(DATA_PATH)

print("===== 5 DÒNG ĐẦU =====")
print(df.head())

print("\n===== KÍCH THƯỚC DỮ LIỆU =====")
print("Số dòng, số cột:", df.shape)

print("\n===== TÊN CÁC CỘT =====")
print(df.columns.tolist())

print("\n===== KIỂU DỮ LIỆU =====")
print(df.dtypes)

print("\n===== GIÁ TRỊ THIẾU =====")
print(df.isnull().sum())

print("\n===== THỐNG KÊ DỮ LIỆU =====")
print(df.describe(include="all"))

print("\n===== PHÂN BỐ CỘT CUỐI CÙNG =====")
last_col = df.columns[-1]
print("Cột cuối cùng là:", last_col)
print(df[last_col].value_counts())