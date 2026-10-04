import sys
import pandas as pd
import numpy as np
from xgboost import XGBRegressor


MODEL_PATH = "models/demand_forecaster.json"
FEATURES_PATH = "data/features.csv"


# --------------------------------------------------
# Read horizon
# --------------------------------------------------

if len(sys.argv) != 2:
    print("Usage:")
    print("  python .\\scripts\\forecast_horizon.py 7d")
    print("  python .\\scripts\\forecast_horizon.py 14d")
    print("  python .\\scripts\\forecast_horizon.py 30d")
    print("  python .\\scripts\\forecast_horizon.py 3m")
    print("  python .\\scripts\\forecast_horizon.py 6m")
    print("  python .\\scripts\\forecast_horizon.py 12m")
    sys.exit(1)


horizon_input = sys.argv[1].lower()

valid_horizons = [
    "7d",
    "14d",
    "30d",
    "3m",
    "6m",
    "12m"
]

if horizon_input not in valid_horizons:
    print("Invalid horizon.")
    print("Use: 7d, 14d, 30d, 3m, 6m, or 12m")
    sys.exit(1)


# --------------------------------------------------
# Convert horizon to number of days
# --------------------------------------------------

horizon_map = {
    "7d": 7,
    "14d": 14,
    "30d": 30,
    "3m": 90,
    "6m": 181,
    "12m": 365,
}

horizon_days = horizon_map[horizon_input]


# --------------------------------------------------
# Load model and historical data
# --------------------------------------------------

model = XGBRegressor()
model.load_model(MODEL_PATH)

df = pd.read_csv(FEATURES_PATH)

df["sale_date"] = pd.to_datetime(df["sale_date"])

df = df.sort_values(
    ["product_id", "warehouse_id", "sale_date"]
)


feature_columns = [
    "product_id",
    "warehouse_id",
    "unit_price",
    "promotion_applied",
    "day_of_week",
    "month",
    "week_of_year",
    "is_weekend",
    "lag_1",
    "lag_7",
    "lag_14",
    "lag_28",
    "rolling_mean_7",
    "rolling_mean_14",
    "rolling_mean_28",
]


# --------------------------------------------------
# Generate recursive forecast
# --------------------------------------------------

daily_results = []

groups = df.groupby(
    ["product_id", "warehouse_id"]
)

for (product_id, warehouse_id), group in groups:

    group = group.sort_values("sale_date")

    last_date = group["sale_date"].max()

    demand_history = group["quantity"].tolist()

    latest_price = group["unit_price"].iloc[-1]

    for day in range(1, horizon_days + 1):

        future_date = (
            last_date
            + pd.Timedelta(days=day)
        )

        # Historical + predicted demand
        lag_1 = demand_history[-1]
        lag_7 = demand_history[-7]
        lag_14 = demand_history[-14]
        lag_28 = demand_history[-28]

        rolling_mean_7 = np.mean(
            demand_history[-7:]
        )

        rolling_mean_14 = np.mean(
            demand_history[-14:]
        )

        rolling_mean_28 = np.mean(
            demand_history[-28:]
        )

        # Calendar features
        day_of_week = future_date.dayofweek
        month = future_date.month
        week_of_year = future_date.isocalendar().week
        is_weekend = int(day_of_week >= 5)

        # Assume no future promotion
        promotion_applied = 0

        features = pd.DataFrame([{
    "product_id": product_id,
    "warehouse_id": warehouse_id,
    "unit_price": latest_price,
    "promotion_applied": promotion_applied,
    "day_of_week": day_of_week,
    "month": month,
    "week_of_year": week_of_year,
    "is_weekend": is_weekend,
    "lag_1": lag_1,
    "lag_7": lag_7,
    "lag_14": lag_14,
    "lag_28": lag_28,
    "rolling_mean_7": rolling_mean_7,
    "rolling_mean_14": rolling_mean_14,
    "rolling_mean_28": rolling_mean_28,
}])[feature_columns]

        prediction = float(
            model.predict(features)[0]
        )

        prediction = max(0, prediction)

        demand_history.append(prediction)

        daily_results.append({
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "forecast_date": future_date,
            "predicted_demand": round(
                prediction,
                2
            ),
        })


# --------------------------------------------------
# Create daily forecast dataframe
# --------------------------------------------------

daily_df = pd.DataFrame(daily_results)

daily_df["forecast_date"] = pd.to_datetime(
    daily_df["forecast_date"]
)


# --------------------------------------------------
# Save daily forecast
# --------------------------------------------------

daily_output = (
    f"data/forecast_{horizon_input}_daily.csv"
)

daily_df.to_csv(
    daily_output,
    index=False
)


# --------------------------------------------------
# Create summary
# --------------------------------------------------

summary_df = (
    daily_df
    .groupby(
        ["product_id", "warehouse_id"],
        as_index=False
    )["predicted_demand"]
    .sum()
)

summary_df = summary_df.rename(
    columns={
        "predicted_demand": "forecast_demand"
    }
)

summary_df["forecast_horizon"] = horizon_input


# --------------------------------------------------
# For monthly / quarterly / annual planning
# create monthly aggregation
# --------------------------------------------------

if horizon_input.endswith("m"):

    monthly_df = daily_df.copy()

    monthly_df["month"] = (
        monthly_df["forecast_date"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly_summary = (
        monthly_df
        .groupby(
            [
                "product_id",
                "warehouse_id",
                "month"
            ],
            as_index=False
        )["predicted_demand"]
        .sum()
    )

    monthly_summary = monthly_summary.rename(
        columns={
            "predicted_demand":
                "monthly_forecast_demand"
        }
    )

    monthly_output = (
        f"data/forecast_{horizon_input}_monthly.csv"
    )

    monthly_summary.to_csv(
        monthly_output,
        index=False
    )


# --------------------------------------------------
# Save total summary
# --------------------------------------------------

summary_output = (
    f"data/forecast_{horizon_input}.csv"
)

summary_df.to_csv(
    summary_output,
    index=False
)


# --------------------------------------------------
# Display
# --------------------------------------------------

print(
    f"\n===== {horizon_input.upper()} DEMAND FORECAST ====="
)

print(
    f"Forecast days: {horizon_days}"
)

print(
    f"Product/Warehouse combinations: "
    f"{len(summary_df)}"
)

print(
    f"Total forecast demand: "
    f"{summary_df['forecast_demand'].sum():,.2f}"
)

print(
    f"\nSaved: {summary_output}"
)

print(
    f"Saved: {daily_output}"
)

if horizon_input.endswith("m"):
    print(
        f"Saved: {monthly_output}"
    )