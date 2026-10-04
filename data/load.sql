\copy suppliers(supplier_id, supplier_name, lead_time_days) FROM 'data/suppliers.csv' WITH (FORMAT csv, HEADER true);
\copy warehouses(warehouse_id, warehouse_name, city, region) FROM 'data/warehouses.csv' WITH (FORMAT csv, HEADER true);
\copy products(product_id, product_name, category, unit_price, supplier_id, base_daily_demand) FROM 'data/products.csv' WITH (FORMAT csv, HEADER true);
\copy promotions(promotion_id, product_id, start_date, end_date, discount_percent) FROM 'data/promotions.csv' WITH (FORMAT csv, HEADER true);
\copy sales(sale_date, product_id, warehouse_id, quantity, unit_price, promotion_applied) FROM 'data/sales.csv' WITH (FORMAT csv, HEADER true);
\copy inventory(inventory_date, product_id, warehouse_id, stock_quantity) FROM 'data/inventory.csv' WITH (FORMAT csv, HEADER true);
