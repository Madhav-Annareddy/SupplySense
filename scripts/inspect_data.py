import pandas as pd

sales = pd.read_csv("data/sales.csv", parse_dates=["sale_date"])
inventory = pd.read_csv("data/inventory.csv", parse_dates=["inventory_date"])
products = pd.read_csv("data/products.csv")

print("\n=== SupplySense Dataset ===")
print(f"Sales rows:       {len(sales):,}")
print(f"Inventory rows:   {len(inventory):,}")
print(f"Products:         {len(products)}")
print(f"Date range:       {sales.sale_date.min().date()} -> {sales.sale_date.max().date()}")
print(f"Total units sold: {sales.quantity.sum():,}")

print("\nSales by product:")
print(
    sales.groupby("product_id")["quantity"]
    .agg(["sum", "mean", "std"])
    .sort_values("sum", ascending=False)
    .to_string()
)

print("\nPromotion rows:")
print(sales["promotion_applied"].value_counts())
