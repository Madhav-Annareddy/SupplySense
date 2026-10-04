import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Boxes,
  PackageCheck,
  TrendingUp,
  RefreshCw,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";

const API_BASE = "https://supplysense-api-ds2u.onrender.com";

type Product = {
  product_id: number;
  product_name: string;
  category: string;
  unit_price: number;
  supplier_id: number;
  base_daily_demand: number;
};

type Forecast = {
  product_id: number;
  warehouse_id: number;
  forecast_demand: number;
  forecast_horizon: string;
};

type Recommendation = {
  product_id: number;
  warehouse_id: number;
  forecast_demand: number;
  forecast_horizon: string;
  stock_quantity: number;
  lead_time_days: number;
  reorder_point: number;
  recommended_order_qty: number;
  stockout_risk: string;
};

type RiskSummary = {
  LOW?: number;
  MEDIUM?: number;
  HIGH?: number;
};

type WhatIfResult = {
  demand_increase_pct: number;
  product_id: number;
  warehouse_id: number;
  stock_quantity: number;
  adjusted_7_day_demand: number;
  adjusted_reorder_point: number;
  additional_order_qty: number;
  stockout_risk: string;
};

function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [selectedHorizon, setSelectedHorizon] = useState("7d");
  const [recommendations, setRecommendations] = useState<Recommendation[]>(
    []
  );
  const [riskSummary, setRiskSummary] = useState<RiskSummary>({});
  const [whatIfData, setWhatIfData] = useState<WhatIfResult[]>([]);
  const [selectedScenario, setSelectedScenario] = useState(20);
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const runWhatIfSimulation = async (demandIncrease: number) => {
  try {
    setSimulationLoading(true);

    const response = await fetch(
      `${API_BASE}/api/what-if?demand_increase=${demandIncrease}`
    );

    if (!response.ok) {
      throw new Error("Simulation failed");
    }

    const data = await response.json();

    setWhatIfData(data);
    setSelectedScenario(demandIncrease);
  } catch (err) {
    console.error("What-if simulation error:", err);
  } finally {
    setSimulationLoading(false);
  }
};

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError("");

      const [
        productsResponse,
        forecastsResponse,
        recommendationsResponse,
        riskResponse,
      ] = await Promise.all([
        fetch(`${API_BASE}/api/products`),
        fetch(`${API_BASE}/api/forecasts?horizon=${selectedHorizon}`),
        fetch(`${API_BASE}/api/recommendations?horizon=${selectedHorizon}`),
        fetch(`${API_BASE}/api/risk-summary?horizon=${selectedHorizon}`),
      ]);

      if (
        !productsResponse.ok ||
        !forecastsResponse.ok ||
        !recommendationsResponse.ok ||
        !riskResponse.ok
      ) {
        throw new Error("Failed to load dashboard data");
      }

      const [
        productsData,
        forecastsData,
        recommendationsData,
        riskData,
      ] = await Promise.all([
        productsResponse.json(),
        forecastsResponse.json(),
        recommendationsResponse.json(),
        riskResponse.json(),
      ]);

      setProducts(productsData);
      setForecasts(forecastsData);
      setRecommendations(recommendationsData);
      setRiskSummary(riskData);
    } catch (err) {
      setError("Unable to load SupplySense data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
  loadDashboard();
  }, [selectedHorizon]);

  useEffect(() => {
  runWhatIfSimulation(20);
  }, []);

  const productMap = useMemo(() => {
    return new Map(
      products.map((product) => [product.product_id, product.product_name])
    );
  }, [products]);

  const forecastChartData = useMemo(() => {
    const grouped = new Map<number, number>();

    forecasts.forEach((item) => {
      grouped.set(
        item.product_id,
        (grouped.get(item.product_id) || 0) +
          item.forecast_demand
      );
    });

    return Array.from(grouped.entries())
      .map(([productId, demand]) => ({
        name:
          productMap.get(productId)?.replace("Wireless ", "") ||
          `Product ${productId}`,
        demand: Math.round(demand),
      }))
      .sort((a, b) => b.demand - a.demand);
  }, [forecasts, productMap]);

  const totalForecast = forecasts.reduce(
    (sum, item) => sum + item.forecast_demand,
    0
  );

  const totalRecommended = recommendations.reduce(
    (sum, item) => sum + item.recommended_order_qty,
    0
  );

  const atRisk =
    (riskSummary.MEDIUM || 0) + (riskSummary.HIGH || 0);

  const warehouseCount = new Set(
    recommendations.map((item) => item.warehouse_id)
  ).size;

  const riskItems = recommendations.filter(
    (item) => item.stockout_risk !== "LOW"
  );

  const simulationHigh = whatIfData.filter(
  (item) => item.stockout_risk === "HIGH"
).length;

const simulationMedium = whatIfData.filter(
  (item) => item.stockout_risk === "MEDIUM"
).length;

const simulationLow = whatIfData.filter(
  (item) => item.stockout_risk === "LOW"
).length;

const additionalUnits = whatIfData.reduce(
  (sum, item) => sum + item.additional_order_qty,
  0
);

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Loading SupplySense...</p>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <div className="brand">SUPPLYSENSE</div>
          <div className="brand-subtitle">
            AI-Powered Demand & Inventory Intelligence
          </div>
        </div>

        <button className="refresh-button" onClick={loadDashboard}>
          <RefreshCw size={16} />
          Refresh
        </button>
      </header>

      <main className="dashboard">
        {error && <div className="error-banner">{error}</div>}

        <section className="hero">
          <div>
            <p className="eyebrow">SUPPLY CHAIN CONTROL CENTER</p>
            <h1>Demand & Inventory Overview</h1>
            <p className="hero-text">
              Monitor predicted demand, inventory exposure, and
              replenishment requirements across your network.
            </p>
          </div>

          <div className="status-pill">
            <span className="status-dot"></span>
            System operational
          </div>
        </section>

        <section className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-icon">
              <Boxes size={20} />
            </div>
            <div>
              <p>Products</p>
              <h2>{products.length}</h2>
              <span>Products monitored</span>
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-icon">
              <PackageCheck size={20} />
            </div>
            <div>
              <p>Warehouses</p>
              <h2>{warehouseCount}</h2>
              <span>Distribution locations</span>
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-icon">
              <TrendingUp size={20} />
            </div>
            <div>
              <p>
  {selectedHorizon === "7d"
    ? "7-Day"
    : selectedHorizon === "14d"
    ? "14-Day"
    : selectedHorizon === "30d"
    ? "30-Day"
    : selectedHorizon === "3m"
    ? "3-Month"
    : selectedHorizon === "6m"
    ? "6-Month"
    : "12-Month"}{" "}
  Forecast
</p>
              <h2>{Math.round(totalForecast).toLocaleString()}</h2>
              <span>Expected units</span>
            </div>
          </div>

          <div className="kpi-card">
            <div className={`kpi-icon ${atRisk > 0 ? "warning" : ""}`}>
              <AlertTriangle size={20} />
            </div>
            <div>
              <p>At-Risk Locations</p>
              <h2>{atRisk}</h2>
              <span>
                {riskSummary.HIGH || 0} high ·{" "}
                {riskSummary.MEDIUM || 0} medium
              </span>
            </div>
          </div>
        </section>

        <section className="content-grid">
          <div className="panel forecast-panel">
            <div className="panel-header">
              <div>
                <h3>
  {selectedHorizon === "7d"
    ? "7-Day"
    : selectedHorizon === "14d"
    ? "14-Day"
    : selectedHorizon === "30d"
    ? "30-Day"
    : selectedHorizon === "3m"
    ? "3-Month"
    : selectedHorizon === "6m"
    ? "6-Month"
    : "12-Month"}{" "}
  Demand Forecast
</h3>
                <p>Predicted demand across all warehouses</p>
              </div>
            </div>
            <div className="horizon-controls">
  {[
    ["7d", "7D"],
    ["14d", "14D"],
    ["30d", "30D"],
    ["3m", "3M"],
    ["6m", "6M"],
    ["12m", "12M"],
  ].map(([value, label]) => (
    <button
      key={value}
      className={
        selectedHorizon === value
          ? "horizon-button active"
          : "horizon-button"
      }
      onClick={() => setSelectedHorizon(value)}
    >
      {label}
    </button>
  ))}
</div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={forecastChartData}
                  margin={{
                    top: 10,
                    right: 10,
                    left: -10,
                    bottom: 60,
                  }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="name"
                    angle={-35}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis />
                  <Tooltip
                    formatter={(value) => [
                      `${Number(value).toLocaleString()} units`,
                      "Forecast",
                    ]}
                  />
                  <Bar
                    dataKey="demand"
                    radius={[6, 6, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="panel risk-panel">
            <div className="panel-header">
              <div>
                <h3>Inventory Risk</h3>
                <p>Current stockout exposure</p>
              </div>
            </div>

            <div className="risk-summary">
              <div className="risk-row">
                <span>
                  <span className="risk-dot low"></span>
                  Low Risk
                </span>
                <strong>{riskSummary.LOW || 0}</strong>
              </div>

              <div className="risk-row">
                <span>
                  <span className="risk-dot medium"></span>
                  Medium Risk
                </span>
                <strong>{riskSummary.MEDIUM || 0}</strong>
              </div>

              <div className="risk-row">
                <span>
                  <span className="risk-dot high"></span>
                  High Risk
                </span>
                <strong>{riskSummary.HIGH || 0}</strong>
              </div>
            </div>

            <div className="risk-total">
              <span>Total monitored locations</span>
              <strong>{recommendations.length}</strong>
            </div>

            <div className="order-summary">
              <span>Recommended replenishment</span>
              <strong>
                {Math.round(totalRecommended).toLocaleString()} units
              </strong>
            </div>
          </div>
        </section>

        <section className="panel what-if-panel">
  <div className="panel-header">
    <div>
      <h3>What-If Demand Simulation</h3>
      <p>
        Evaluate inventory exposure when demand changes
      </p>
    </div>
  </div>

  <div className="scenario-controls">
    <span>Demand increase</span>

    <div className="scenario-buttons">
      {[0, 10, 20, 30].map((scenario) => (
        <button
          key={scenario}
          className={
            selectedScenario === scenario
              ? "scenario-button active"
              : "scenario-button"
          }
          onClick={() => runWhatIfSimulation(scenario)}
          disabled={simulationLoading}
        >
          +{scenario}%
        </button>
      ))}
    </div>
  </div>

  <div className="simulation-results">
    <div className="simulation-card">
      <span>Low Risk</span>
      <strong>{simulationLow}</strong>
      <small>locations</small>
    </div>

    <div className="simulation-card medium">
      <span>Medium Risk</span>
      <strong>{simulationMedium}</strong>
      <small>locations</small>
    </div>

    <div className="simulation-card high">
      <span>High Risk</span>
      <strong>{simulationHigh}</strong>
      <small>locations</small>
    </div>

    <div className="simulation-card units">
      <span>Additional Inventory</span>
      <strong>
        {Math.round(additionalUnits).toLocaleString()}
      </strong>
      <small>units required</small>
    </div>
  </div>
</section>
        <section className="panel recommendations-panel">
          <div className="panel-header">
            <div>
              <h3>Replenishment Recommendations</h3>
              <p>
                Inventory position compared with forecast demand and
                reorder point
              </p>
            </div>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Warehouse</th>
                  <th>Current Stock</th>
                  <th>
  {selectedHorizon === "7d"
    ? "7-Day"
    : selectedHorizon === "14d"
    ? "14-Day"
    : selectedHorizon === "30d"
    ? "30-Day"
    : selectedHorizon === "3m"
    ? "3-Month"
    : selectedHorizon === "6m"
    ? "6-Month"
    : "12-Month"}{" "}
  Forecast
</th>
                  <th>Reorder Point</th>
                  <th>Risk</th>
                  <th>Order Qty</th>
                </tr>
              </thead>

              <tbody>
                {recommendations.map((item) => (
                  <tr
                    key={`${item.product_id}-${item.warehouse_id}`}
                  >
                    <td className="product-name">
                      {productMap.get(item.product_id) ||
                        `Product ${item.product_id}`}
                    </td>

                    <td>Warehouse {item.warehouse_id}</td>

                    <td>
                      {item.stock_quantity.toLocaleString()}
                    </td>

                    <td>{Math.round(
                    item.forecast_demand
                    ).toLocaleString()}</td>
                    

                    <td>
                      {Math.round(
                        item.reorder_point
                      ).toLocaleString()}
                    </td>

                    <td>
                      <span
                        className={`risk-badge ${item.stockout_risk.toLowerCase()}`}
                      >
                        {item.stockout_risk}
                      </span>
                    </td>

                    <td className="order-quantity">
                      {Math.round(
                        item.recommended_order_qty
                      ).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {riskItems.length > 0 && (
          <section className="alert-panel">
            <AlertTriangle size={20} />
            <div>
              <strong>Inventory attention required</strong>
              <p>
                {riskItems.length} warehouse-product combinations
                require additional inventory review.
              </p>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;