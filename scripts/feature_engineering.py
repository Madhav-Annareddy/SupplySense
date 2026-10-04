import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = "postgresql+psycopg2://postgres:1234@localhost:5432/supplysense"

engine = create_engine(DATABASE_URL)

query = """
SELECT
    sale_date,
    product_id,
    warehouse_id,
    quantity,
    unit_price,
    promotion_applied
FROM sales
ORDER BY sale_date;
"""

df = pd.read_sql(query, engine)

# Convert date
df["sale_date"] = pd.to_datetime(df["sale_date"])

# Sort before creating lag features
df = df.sort_values(["product_id", "warehouse_id", "sale_date"])

# Calendar features
df["day_of_week"] = df["sale_date"].dt.dayofweek
df["month"] = df["sale_date"].dt.month
df["week_of_year"] = df["sale_date"].dt.isocalendar().week.astype(int)
df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

# Lag features
group = df.groupby(["product_id", "warehouse_id"])["quantity"]

df["lag_1"] = group.shift(1)
df["lag_7"] = group.shift(7)
df["lag_14"] = group.shift(14)
df["lag_28"] = group.shift(28)

# Rolling demand features
df["rolling_mean_7"] = group.transform(
    lambda x: x.shift(1).rolling(7).mean()
)

df["rolling_mean_14"] = group.transform(
    lambda x: x.shift(1).rolling(14).mean()
)

df["rolling_mean_28"] = group.transform(
    lambda x: x.shift(1).rolling(28).mean()
)

# Remove rows that don't have enough history
df = df.dropna().reset_index(drop=True)

print("Final shape:", df.shape)

print("\nFeature columns:")
print(df.columns.tolist())

print("\nSample:")
print(df.head())

print("\nMissing values:")
print(df.isnull().sum())

# Save feature dataset
df.to_csv("data/features.csv", index=False)

print("\nSaved: data/features.csv")