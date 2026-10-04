# SupplySense

**AI-Powered Demand Forecasting & Inventory Optimization Platform**

SupplySense is an end-to-end supply chain analytics platform that combines machine learning demand forecasting with inventory risk analysis and replenishment recommendations.

It helps answer three practical questions:

1. **How much demand should we expect?**
2. **Which product-warehouse combinations are at risk?**
3. **How much inventory should we consider replenishing?**

---

## Key Capabilities

- Demand forecasting using XGBoost
- Product and warehouse-level forecasting
- Multiple forecast horizons:
  - 7 days
  - 14 days
  - 30 days
  - 3 months
  - 6 months
  - 12 months
- Inventory risk classification
- Replenishment recommendations
- What-if demand scenario simulation
- Interactive React dashboard
- FastAPI backend
- PostgreSQL data layer

---

## System Architecture

```text
                    SupplySense
                         |
        +----------------+----------------+
        |                                 |
   Historical Data                    Master Data
        |                                 |
   Sales / Inventory          Products / Warehouses
        |                     Suppliers / Promotions
        +----------------+----------------+
                         |
                         v
               Feature Engineering
                         |
                         v
                 XGBoost Forecasting
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
      Forecasts     Risk Analysis   Replenishment
          |              |              |
          +--------------+--------------+
                         |
                         v
                  FastAPI Backend
                         |
                         v
                 React Dashboard