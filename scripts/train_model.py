import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import os

# Load engineered features
df = pd.read_csv("data/features.csv")
df["sale_date"] = pd.to_datetime(df["sale_date"])

# Sort chronologically
df = df.sort_values("sale_date").reset_index(drop=True)

# Features used by the model
features = [
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

target = "quantity"

# Time-based split
split_date = df["sale_date"].quantile(0.80)

train = df[df["sale_date"] <= split_date]
test = df[df["sale_date"] > split_date]

X_train = train[features]
y_train = train[target]

X_test = test[features]
y_test = test[target]

print("Training rows:", len(train))
print("Testing rows:", len(test))
print("Split date:", split_date.date())

# XGBoost model
model = XGBRegressor(
    n_estimators=500,
    max_depth=8,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    random_state=42,
    n_jobs=-1
)

print("\nTraining XGBoost model...")

model.fit(X_train, y_train)

# Predictions
predictions = model.predict(X_test)

# Metrics
mae = mean_absolute_error(y_test, predictions)
rmse = np.sqrt(mean_squared_error(y_test, predictions))

# Avoid division by zero for MAPE
non_zero = y_test != 0

mape = (
    np.mean(
        np.abs(
            (y_test[non_zero] - predictions[non_zero])
            / y_test[non_zero]
        )
    )
    * 100
)

print("\n===== MODEL PERFORMANCE =====")
print(f"MAE:  {mae:.2f}")
print(f"RMSE: {rmse:.2f}")
print(f"MAPE: {mape:.2f}%")

# Save model
os.makedirs("models", exist_ok=True)

model_path = "models/demand_forecaster.json"
model.save_model(model_path)

print(f"\nModel saved: {model_path}")