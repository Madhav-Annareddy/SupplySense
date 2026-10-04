import pandas as pd
import numpy as np


# Load current recommendations
df = pd.read_csv("data/reorder_recommendations.csv")

# Scenarios to test
demand_scenarios = [0, 10, 20, 30]

results = []

for increase in demand_scenarios:

    scenario = df.copy()

    # Increase forecast demand
    scenario["adjusted_7_day_demand"] = (
        scenario["forecast_7_day_demand"] * (1 + increase / 100)
    )

    # Daily demand under scenario
    scenario["adjusted_daily_demand"] = (
        scenario["adjusted_7_day_demand"] / 7
    )

    # Lead-time demand
    scenario["adjusted_lead_time_demand"] = (
        scenario["adjusted_daily_demand"]
        * scenario["lead_time_days"]
    )

    # Safety stock
    scenario["adjusted_safety_stock"] = (
        scenario["adjusted_lead_time_demand"] * 0.20
    )

    # Reorder point
    scenario["adjusted_reorder_point"] = (
        scenario["adjusted_lead_time_demand"]
        + scenario["adjusted_safety_stock"]
    )

    # Additional quantity required
    scenario["additional_order_qty"] = np.maximum(
        0,
        np.ceil(
            scenario["adjusted_reorder_point"]
            - scenario["stock_quantity"]
        )
    )

    # Risk calculation
    def calculate_risk(row):
        if row["stock_quantity"] <= row["adjusted_lead_time_demand"]:
            return "HIGH"
        elif row["stock_quantity"] <= row["adjusted_reorder_point"]:
            return "MEDIUM"
        else:
            return "LOW"

    scenario["stockout_risk"] = scenario.apply(
        calculate_risk,
        axis=1
    )

    # Store results
    for _, row in scenario.iterrows():
        results.append({
            "demand_increase_pct": increase,
            "product_id": row["product_id"],
            "warehouse_id": row["warehouse_id"],
            "stock_quantity": row["stock_quantity"],
            "adjusted_7_day_demand": round(
                row["adjusted_7_day_demand"], 2
            ),
            "adjusted_reorder_point": round(
                row["adjusted_reorder_point"], 2
            ),
            "additional_order_qty": int(
                row["additional_order_qty"]
            ),
            "stockout_risk": row["stockout_risk"]
        })


# Create final dataframe
results_df = pd.DataFrame(results)

# Save results
results_df.to_csv(
    "data/what_if_simulation.csv",
    index=False
)


# Display summary
print("\n===== WHAT-IF SIMULATION =====")

for increase in demand_scenarios:

    scenario = results_df[
        results_df["demand_increase_pct"] == increase
    ]

    print(f"\nDemand Increase: +{increase}%")

    print(
        "HIGH:",
        (scenario["stockout_risk"] == "HIGH").sum()
    )

    print(
        "MEDIUM:",
        (scenario["stockout_risk"] == "MEDIUM").sum()
    )

    print(
        "LOW:",
        (scenario["stockout_risk"] == "LOW").sum()
    )

    print(
        "Additional units required:",
        scenario["additional_order_qty"].sum()
    )


print("\nSaved: data/what_if_simulation.csv")