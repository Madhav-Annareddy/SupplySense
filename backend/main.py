import pandas as pd
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path



app = FastAPI(
    title="SupplySense API",
    description="AI-powered demand forecasting and inventory optimization API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DATA_DIR = Path("data")


@app.get("/")
def root():
    return {
        "message": "SupplySense API is running",
        "status": "healthy"
    }


@app.get("/api/products")
def get_products():
    df = pd.read_csv(DATA_DIR / "products.csv")

    return df.to_dict(orient="records")


@app.get("/api/forecasts")
def get_forecasts(horizon: str = "7d"):
    allowed_horizons = ["7d", "14d", "30d", "3m", "6m", "12m"]

    if horizon not in allowed_horizons:
        return {
            "error": f"Invalid horizon. Choose from: {', '.join(allowed_horizons)}"
        }

    file_path = DATA_DIR / f"forecast_{horizon}.csv"

    if not file_path.exists():
        return {
            "error": f"Forecast file not found for horizon: {horizon}"
        }

    df = pd.read_csv(file_path)

    return df.to_dict(orient="records")


@app.get("/api/recommendations")
def get_recommendations(horizon: str = "7d"):
    allowed_horizons = ["7d", "14d", "30d", "3m", "6m", "12m"]

    if horizon not in allowed_horizons:
        return {
            "error": f"Invalid horizon. Choose from: {', '.join(allowed_horizons)}"
        }

    forecast_file = DATA_DIR / f"forecast_{horizon}.csv"

    if not forecast_file.exists():
        return {
            "error": f"Forecast file not found for horizon: {horizon}"
        }

    forecast = pd.read_csv(forecast_file)

    inventory = pd.read_csv(
    DATA_DIR / "inventory_intelligence.csv"
)

    inventory = inventory[
        [
            "product_id",
            "warehouse_id",
            "stock_quantity",
            "lead_time_days",
            "avg_daily_demand",
            "lead_time_demand",
            "safety_stock",
            "reorder_point",
            "stockout_risk"
        ]
    ]

    df = forecast.merge(
        inventory,
        on=["product_id", "warehouse_id"],
        how="left"
    )

    # Convert forecast horizon into average daily demand
    horizon_days = {
        "7d": 7,
        "14d": 14,
        "30d": 30,
        "3m": 90,
        "6m": 181,
        "12m": 365
    }

    days = horizon_days[horizon]

    df["forecast_daily_demand"] = (
        df["forecast_demand"] / days
    )

    # Expected demand during supplier lead time
    df["lead_time_demand"] = (
        df["forecast_daily_demand"]
        * df["lead_time_days"]
    )

    # Safety stock = 20% of lead-time demand
    df["safety_stock"] = (
        df["lead_time_demand"] * 0.20
    )

    # Reorder point
    df["reorder_point"] = (
        df["lead_time_demand"]
        + df["safety_stock"]
    )

    # Recommended order quantity
    df["recommended_order_qty"] = np.maximum(
        0,
        np.ceil(
            df["reorder_point"]
            - df["stock_quantity"]
        )
    )

    

    numeric_columns = [
        "forecast_demand",
        "forecast_daily_demand",
        "lead_time_demand",
        "safety_stock",
        "reorder_point",
        "recommended_order_qty"
    ]

    df[numeric_columns] = df[numeric_columns].round(2)

    df["forecast_horizon"] = horizon

    return df.to_dict(orient="records")


@app.get("/api/risk-summary")
def get_risk_summary(horizon: str = "7d"):
    recommendations = get_recommendations(horizon)

    if isinstance(recommendations, dict):
        return recommendations

    df = pd.DataFrame(recommendations)

    summary = (
        df["stockout_risk"]
        .value_counts()
        .to_dict()
    )

    # Ensure all risk categories exist
    return {
        "HIGH": int(summary.get("HIGH", 0)),
        "MEDIUM": int(summary.get("MEDIUM", 0)),
        "LOW": int(summary.get("LOW", 0))
    }


@app.get("/api/what-if")
def what_if(demand_increase: int = 20):
    df = pd.read_csv(DATA_DIR / "what_if_simulation.csv")

    scenario = df[
        df["demand_increase_pct"] == demand_increase
    ]

    return scenario.to_dict(orient="records")