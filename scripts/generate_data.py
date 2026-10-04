"""
SupplySense - Synthetic Business Data Generator

Generates realistic 2-year sales and inventory data for:
- 10 products
- 3 warehouses
- 30 product/warehouse combinations
- 4 suppliers with different lead times

The generator intentionally creates different business situations:
- Healthy inventory
- Medium-risk inventory
- Critical inventory
- Overstock
- Warehouse demand differences
- Product growth/decline
- Seasonality
- Promotions
- Demand spikes
- Inventory replenishment cycles

Run:
    python scripts/generate_data.py
"""

from pathlib import Path
import numpy as np
import pandas as pd


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

SEED = 42
START_DATE = "2024-01-01"
END_DATE = "2025-12-31"

rng = np.random.default_rng(SEED)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


# ---------------------------------------------------------
# LOAD EXISTING MASTER DATA
# ---------------------------------------------------------

products = pd.read_csv(DATA_DIR / "products.csv")
warehouses = pd.read_csv(DATA_DIR / "warehouses.csv")
suppliers = pd.read_csv(DATA_DIR / "suppliers.csv")


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

required_product_columns = {
    "product_id",
    "product_name",
    "category",
    "unit_price",
    "supplier_id",
    "base_daily_demand",
}

required_warehouse_columns = {
    "warehouse_id",
    "warehouse_name",
    "city",
    "region",
}

required_supplier_columns = {
    "supplier_id",
    "supplier_name",
    "lead_time_days",
}

if not required_product_columns.issubset(products.columns):
    raise ValueError("products.csv is missing required columns.")

if not required_warehouse_columns.issubset(warehouses.columns):
    raise ValueError("warehouses.csv is missing required columns.")

if not required_supplier_columns.issubset(suppliers.columns):
    raise ValueError("suppliers.csv is missing required columns.")


# ---------------------------------------------------------
# BUSINESS PARAMETERS
# ---------------------------------------------------------

dates = pd.date_range(START_DATE, END_DATE, freq="D")


# Warehouse demand multipliers.
# Bangalore has slightly higher demand for electronics,
# Hyderabad is balanced, Delhi varies by product.
warehouse_multiplier = {
    1: 1.15,   # Bangalore
    2: 0.95,   # Hyderabad
    3: 1.05,   # Delhi
}


# Product-specific demand behavior.
# Values represent long-term growth/decline over the dataset.
product_growth = {
    1: 0.08,    # Wireless Keyboard
    2: 0.15,    # Wireless Mouse
    3: 0.10,    # USB-C Hub
    4: -0.03,   # Laptop Stand
    5: 0.06,    # Mechanical Keyboard
    6: 0.12,    # Webcam
    7: 0.02,    # Monitor
    8: 0.05,    # Headset
    9: 0.09,    # Bluetooth Speaker
    10: 0.13,   # Power Bank
}


# Product-specific seasonality strength.
seasonality_strength = {
    1: 0.10,
    2: 0.12,
    3: 0.14,
    4: 0.08,
    5: 0.11,
    6: 0.16,
    7: 0.18,
    8: 0.10,
    9: 0.15,
    10: 0.13,
}


# ---------------------------------------------------------
# SALES GENERATION
# ---------------------------------------------------------

sales_rows = []

total_days = len(dates)

for _, product in products.iterrows():

    product_id = int(product["product_id"])
    base_demand = float(product["base_daily_demand"])

    growth = product_growth.get(product_id, 0.05)
    seasonal_strength = seasonality_strength.get(product_id, 0.10)

    for _, warehouse in warehouses.iterrows():

        warehouse_id = int(warehouse["warehouse_id"])
        warehouse_factor = warehouse_multiplier[warehouse_id]

        # Small product/warehouse-specific demand difference.
        local_factor = rng.uniform(0.90, 1.10)

        for day_index, date in enumerate(dates):

            # ---------------------------------------------
            # Long-term growth / decline
            # ---------------------------------------------

            progress = day_index / max(total_days - 1, 1)

            growth_factor = 1 + (growth * progress)


            # ---------------------------------------------
            # Monthly seasonality
            # ---------------------------------------------

            month_angle = 2 * np.pi * (date.month - 1) / 12

            seasonal_factor = (
                1
                + seasonal_strength * np.sin(month_angle)
            )


            # ---------------------------------------------
            # Weekly pattern
            # ---------------------------------------------

            if date.dayofweek >= 5:
                weekday_factor = 0.82
            else:
                weekday_factor = 1.05


            # ---------------------------------------------
            # Random daily variation
            # ---------------------------------------------

            noise_factor = rng.normal(1.0, 0.10)

            noise_factor = max(noise_factor, 0.55)


            # ---------------------------------------------
            # Demand spike events
            # ---------------------------------------------

            spike_factor = 1.0

            # Occasional high-demand days.
            if rng.random() < 0.025:
                spike_factor = rng.uniform(1.35, 1.90)


            # ---------------------------------------------
            # Promotion events
            # ---------------------------------------------

            promotion_applied = False
            promotion_factor = 1.0

            # Approximately 5% of days are promotion days.
            if rng.random() < 0.05:
                promotion_applied = True
                promotion_factor = rng.uniform(1.20, 1.55)


            # ---------------------------------------------
            # Final demand
            # ---------------------------------------------

            expected_demand = (
                base_demand
                * warehouse_factor
                * local_factor
                * growth_factor
                * seasonal_factor
                * weekday_factor
                * noise_factor
                * spike_factor
                * promotion_factor
            )

            quantity = max(
                1,
                int(round(expected_demand))
            )

            sales_rows.append(
                {
                    "sale_date": date.strftime("%Y-%m-%d"),
                    "product_id": product_id,
                    "warehouse_id": warehouse_id,
                    "quantity": quantity,
                    "unit_price": float(product["unit_price"]),
                    "promotion_applied": promotion_applied,
                }
            )


sales = pd.DataFrame(sales_rows)


# ---------------------------------------------------------
# INVENTORY GENERATION
# ---------------------------------------------------------

# Merge supplier lead times into products.
product_supplier = products.merge(
    suppliers[
        [
            "supplier_id",
            "lead_time_days",
        ]
    ],
    on="supplier_id",
    how="left",
)

sales["sale_date"] = pd.to_datetime(sales["sale_date"])


# ---------------------------------------------------------
# INVENTORY SCENARIO DESIGN
# ---------------------------------------------------------

# These are target coverage situations for the END of 2025.
#
# The values are deliberately varied rather than assigning
# one single risk level to the whole dataset.
#
# coverage_days:
#   very low -> potential HIGH risk
#   low      -> potential MEDIUM risk
#   normal   -> LOW risk
#   high     -> overstock
#
# We are not writing risk labels into the data.
# The existing inventory intelligence code will calculate them.

scenario_days = {
    # Product 1 - Wireless Keyboard
    (1, 1): 45,
    (1, 2): 32,
    (1, 3): 65,

    # Product 2 - Wireless Mouse
    (2, 1): 8,
    (2, 2): 42,
    (2, 3): 55,

    # Product 3 - USB-C Hub
    (3, 1): 70,
    (3, 2): 24,
    (3, 3): 48,

    # Product 4 - Laptop Stand
    (4, 1): 52,
    (4, 2): 68,
    (4, 3): 28,

    # Product 5 - Mechanical Keyboard
    (5, 1): 38,
    (5, 2): 18,
    (5, 3): 62,

    # Product 6 - Webcam
    (6, 1): 7,
    (6, 2): 46,
    (6, 3): 75,

    # Product 7 - Monitor
    (7, 1): 50,
    (7, 2): 15,
    (7, 3): 58,

    # Product 8 - Headset
    (8, 1): 35,
    (8, 2): 72,
    (8, 3): 22,

    # Product 9 - Bluetooth Speaker
    (9, 1): 60,
    (9, 2): 30,
    (9, 3): 82,

    # Product 10 - Power Bank
    (10, 1): 12,
    (10, 2): 50,
    (10, 3): 40,
}


inventory_rows = []


for _, product in product_supplier.iterrows():

    product_id = int(product["product_id"])
    lead_time = int(product["lead_time_days"])

    for _, warehouse in warehouses.iterrows():

        warehouse_id = int(warehouse["warehouse_id"])

        combination_sales = sales[
            (sales["product_id"] == product_id)
            & (sales["warehouse_id"] == warehouse_id)
        ].sort_values("sale_date")

        daily_sales = combination_sales["quantity"].to_numpy()

        # Recent demand is more important than very old demand.
        recent_window = min(60, len(daily_sales))

        recent_average = float(
            np.mean(daily_sales[-recent_window:])
        )

        target_days = scenario_days.get(
            (product_id, warehouse_id),
            45,
        )

        # Starting stock is based on average demand,
        # with additional variation.
        starting_days = rng.uniform(
            max(25, target_days * 0.75),
            max(30, target_days * 1.25),
        )

        current_stock = max(
            1,
            int(round(recent_average * starting_days))
        )

        # Replenishment target.
        replenishment_target = max(
            int(round(recent_average * target_days)),
            int(round(recent_average * (lead_time + 10))),
        )

        for day_index, date in enumerate(dates):

            daily_demand = int(
                combination_sales.iloc[day_index]["quantity"]
            )

            # ---------------------------------------------
            # Consume inventory
            # ---------------------------------------------

            current_stock -= daily_demand

            # Prevent unrealistic negative stock.
            current_stock = max(current_stock, 0)


            # ---------------------------------------------
            # Replenishment behavior
            # ---------------------------------------------

            # Every 30 days, healthy combinations replenish.
            # Low-stock combinations replenish later and less
            # aggressively, creating realistic risk.
            if day_index > 0 and day_index % 30 == 0:

                recent_sales = daily_sales[
                    max(0, day_index - 30):day_index
                ]

                recent_demand = max(
                    float(np.mean(recent_sales)),
                    1.0,
                )

                # Replenishment quantity.
                replenishment = int(
                    round(
                        max(
                            0,
                            replenishment_target
                            - current_stock,
                        )
                    )
                )

                # Add natural supplier variation.
                replenishment *= rng.uniform(
                    0.85,
                    1.15,
                )

                replenishment = int(
                    round(replenishment)
                )

                current_stock += max(
                    0,
                    replenishment,
                )


            # ---------------------------------------------
            # Occasional emergency replenishment
            # ---------------------------------------------

            # Only some combinations receive emergency stock.
            if (
                current_stock < recent_average * lead_time
                and rng.random() < 0.18
            ):

                emergency_stock = int(
                    round(
                        recent_average
                        * rng.uniform(5, 12)
                    )
                )

                current_stock += emergency_stock


            inventory_rows.append(
                {
                    "inventory_date": date.strftime("%Y-%m-%d"),
                    "product_id": product_id,
                    "warehouse_id": warehouse_id,
                    "stock_quantity": int(current_stock),
                }
            )


inventory = pd.DataFrame(inventory_rows)


# ---------------------------------------------------------
# SAFETY CHECKS
# ---------------------------------------------------------

if sales.empty:
    raise RuntimeError("Sales dataset is empty.")

if inventory.empty:
    raise RuntimeError("Inventory dataset is empty.")


expected_rows = (
    len(products)
    * len(warehouses)
    * len(dates)
)

if len(sales) != expected_rows:
    raise RuntimeError(
        f"Unexpected sales row count: {len(sales)} "
        f"(expected {expected_rows})"
    )

if len(inventory) != expected_rows:
    raise RuntimeError(
        f"Unexpected inventory row count: {len(inventory)} "
        f"(expected {expected_rows})"
    )


if sales["quantity"].min() <= 0:
    raise RuntimeError("Sales contains invalid quantities.")

if inventory["stock_quantity"].min() < 0:
    raise RuntimeError("Inventory contains negative stock.")


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

sales.to_csv(
    DATA_DIR / "sales.csv",
    index=False,
)

inventory.to_csv(
    DATA_DIR / "inventory.csv",
    index=False,
)


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

latest_inventory = (
    inventory.sort_values("inventory_date")
    .groupby(
        ["product_id", "warehouse_id"],
        as_index=False,
    )
    .tail(1)
)

print()
print("=" * 60)
print("SupplySense Synthetic Dataset Generated")
print("=" * 60)

print(f"Sales rows:       {len(sales):,}")
print(f"Inventory rows:   {len(inventory):,}")
print(
    f"Date range:       {sales['sale_date'].min()} "
    f"to {sales['sale_date'].max()}"
)

print(
    f"Total units sold: {sales['quantity'].sum():,}"
)

print()
print("Latest Inventory Summary")
print("-" * 60)

print(
    latest_inventory[
        [
            "product_id",
            "warehouse_id",
            "stock_quantity",
        ]
    ].to_string(index=False)
)

print()
print("Files updated:")
print("  data/sales.csv")
print("  data/inventory.csv")
print()
print("Products, warehouses and suppliers were preserved.")
print("=" * 60)