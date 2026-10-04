import pandas as pd
import numpy as np
from sqlalchemy import create_engine

DATABASE_URL = "postgresql+psycopg2://postgres:1234@localhost:5432/supplysense"

engine = create_engine(DATABASE_URL)

# -----------------------------
# 1. Load latest inventory
# -----------------------------

inventory_query = """
SELECT
    i.inventory_date,
    i.product_id,
    i.warehouse_id,
    i.stock_quantity,
    p.product_name,
    p.supplier_id,
    s.lead_time_days
FROM inventory i
JOIN products p
    ON i.product_id = p.product_id
JOIN suppliers s
    ON p.supplier_id = s.supplier_id
WHERE i.inventory_date = (
    SELECT MAX(inventory_date)
    FROM inventory
);
"""

inventory = pd.read_sql(inventory_query, engine)

# -----------------------------
# 2. Load historical sales
# -----------------------------

sales_query = """
SELECT
    sale_date,
    product_id,
    warehouse_id,
    quantity
FROM sales;
"""

sales = pd.read_sql(sales_query, engine)

sales["sale_date"] = pd.to_datetime(sales["sale_date"])

# -----------------------------
# 3. Calculate average demand
# -----------------------------

avg_demand = (
    sales
    .groupby(["product_id", "warehouse_id"])["quantity"]
    .mean()
    .reset_index()
    .rename(columns={"quantity": "avg_daily_demand"})
)

# -----------------------------
# 4. Combine inventory + demand
# -----------------------------

df = inventory.merge(
    avg_demand,
    on=["product_id", "warehouse_id"],
    how="left"
)

# -----------------------------
# 5. Calculate inventory metrics
# -----------------------------

df["days_of_inventory"] = (
    df["stock_quantity"] /
    df["avg_daily_demand"]
)

df["lead_time_demand"] = (
    df["avg_daily_demand"] *
    df["lead_time_days"]
)

# Safety stock:
# 20% buffer over expected lead-time demand
df["safety_stock"] = (
    df["lead_time_demand"] * 0.20
)

# Reorder point
df["reorder_point"] = (
    df["lead_time_demand"] +
    df["safety_stock"]
)

# -----------------------------
# 6. Stockout risk
# -----------------------------

def calculate_risk(row):

    if row["days_of_inventory"] <= row["lead_time_days"]:
        return "HIGH"

    elif row["days_of_inventory"] <= row["lead_time_days"] * 1.5:
        return "MEDIUM"

    else:
        return "LOW"


df["stockout_risk"] = df.apply(
    calculate_risk,
    axis=1
)

# -----------------------------
# 7. Recommended order
# -----------------------------

df["recommended_order_qty"] = np.maximum(
    0,
    np.ceil(df["reorder_point"] - df["stock_quantity"])
)

# -----------------------------
# 8. Display results
# -----------------------------

columns = [
    "product_id",
    "product_name",
    "warehouse_id",
    "stock_quantity",
    "avg_daily_demand",
    "lead_time_days",
    "days_of_inventory",
    "lead_time_demand",
    "safety_stock",
    "reorder_point",
    "stockout_risk",
    "recommended_order_qty"
]

result = df[columns].sort_values(
    ["stockout_risk", "recommended_order_qty"],
    ascending=[True, False]
)

print("\n===== INVENTORY INTELLIGENCE =====")
print(result.to_string(index=False))

print("\n===== RISK SUMMARY =====")
print(
    result["stockout_risk"]
    .value_counts()
)

# Save results
result.to_csv(
    "data/inventory_intelligence.csv",
    index=False
)

print("\nSaved: data/inventory_intelligence.csv")