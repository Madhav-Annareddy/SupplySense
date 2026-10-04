from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SupplySense API",
    description="Demand Forecasting & Inventory Optimization Platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "SupplySense API",
        "version": "0.1.0",
    }


@app.get("/api")
def api_root():
    return {
        "message": "SupplySense API is running",
        "docs": "/docs",
    }
