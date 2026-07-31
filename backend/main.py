"""Track A - Energy Demand Forecasting backend."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from schemas import ForecastResponse, ModelInfo, OptimizeRequest, OptimizeResponse
from services.forecasting import load_artifact, model_info, run_forecast
from services.optimization import optimize_mix
from services.preprocessing import read_energy_csv


# 1. 定义 lifespan（启动预热）
@asynccontextmanager
async def lifespan(app: FastAPI):
  load_artifact()
  yield


# 2. 实例化 FastAPI 应用程序（必须放在所有 @app.xxx 路由的前面！）
app = FastAPI(
    title="Track A - Energy Demand Forecasting API",
    version="1.0.0",
    lifespan=lifespan,
)

# 3. 添加跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# 4. 定义 API 路由接口
@app.get("/health")
def health():
  try:
    info = model_info()
    return {
        "status": "ok",
        "model_loaded": True,
        "model_name": info["model_name"],
    }
  except Exception as exc:
    raise HTTPException(status_code=503, detail=f"Model not available: {exc}")


@app.get("/model-info", response_model=ModelInfo)
def get_model_info():
  try:
    return model_info()
  except Exception as exc:
    raise HTTPException(
        status_code=503, detail=f"Failed to fetch model info: {exc}"
    )


@app.post("/forecast", response_model=ForecastResponse)
async def forecast(
    file: UploadFile = File(...),
    last_hours: int | None = Query(None, ge=1, le=744),
):
  if not file.filename.endswith(".csv"):
    raise HTTPException(status_code=400, detail="Only CSV files are supported.")

  try:
    raw = await file.read()
    energy = read_energy_csv(raw)
  except ValueError as ve:
    raise HTTPException(status_code=422, detail=str(ve))
  except Exception as exc:
    raise HTTPException(status_code=400, detail=f"Error reading file: {exc}")

  try:
    return run_forecast(energy, last_hours=last_hours)
  except ValueError as ve:
    raise HTTPException(status_code=422, detail=str(ve))
  except Exception as exc:
    raise HTTPException(
        status_code=500, detail=f"Internal prediction error: {exc}"
    )


@app.post("/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest):
  try:
    return optimize_mix(
        demand=req.demand,
        carbon_limit=req.carbon_limit,
        renewable_min=req.renewable_min,
        capacities=req.capacities,
    )
  except Exception as exc:
    raise HTTPException(status_code=500, detail=f"Optimization error: {exc}")