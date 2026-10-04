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

print("Shape:", df.shape)
print("\nColumns:")
print(df.columns.tolist())

print("\nFirst 5 rows:")
print(df.head())

print("\nMissing values:")
print(df.isnull().sum())