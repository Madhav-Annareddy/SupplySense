import pandas as pd
import numpy as np


# Load data
forecast = pd.read_csv("data/forecast_7_day.csv")
inventory = pd.read_csv("data/inventory_intelligence.csv")

# Keep only the inventory fields we need
inventory = inventory[
    [
        "product_id",
        "warehouse_id",
        "stock_quantity",
        "lead_time_days"
    ]
]

# Combine forecast with current inventory
df = forecast.merge(
    inventory,
    on=["product_id", "warehouse_id"],
    how="left"
)

# Convert 7-day forecast into average daily forecast
df["forecast_daily_demand"] = (
    df["forecast_7_day_demand"] / 7
)

# Expected demand during supplier lead time
df["lead_time_demand"] = (
    df["forecast_daily_demand"] * df["lead_time_days"]
)

# Safety stock = 20% of lead-time demand
df["safety_stock"] = (
    df["lead_time_demand"] * 0.20
)

# Reorder point
df["reorder_point"] = (
    df["lead_time_demand"] + df["safety_stock"]
)

# Recommended order quantity
df["recommended_order_qty"] = np.maximum(
    0,
    np.ceil(df["reorder_point"] - df["stock_quantity"])
)

# Stockout risk
def calculate_risk(row):
    if row["stock_quantity"] <= row["lead_time_demand"]:
        return "HIGH"
    elif row["stock_quantity"] <= row["reorder_point"]:
        return "MEDIUM"
    else:
        return "LOW"


df["stockout_risk"] = df.apply(calculate_risk, axis=1)

# Round values for readability
numeric_columns = [
    "forecast_7_day_demand",
    "forecast_daily_demand",
    "lead_time_demand",
    "safety_stock",
    "reorder_point"
]

df[numeric_columns] = df[numeric_columns].round(2)

# Save result
df.to_csv(
    "data/reorder_recommendations.csv",
    index=False
)

print("\n===== REORDER RECOMMENDATIONS =====")
print(
    df[
        [
            "product_id",
            "warehouse_id",
            "stock_quantity",
            "forecast_7_day_demand",
            "lead_time_days",
            "reorder_point",
            "recommended_order_qty",
            "stockout_risk"
        ]
    ].to_string(index=False)
)

print("\n===== RISK SUMMARY =====")
print(df["stockout_risk"].value_counts())

print("\n===== ORDER SUMMARY =====")
print(
    "Total recommended units:",
    int(df["recommended_order_qty"].sum())
)

print("\nSaved: data/reorder_recommendations.csv")