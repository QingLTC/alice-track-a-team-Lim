"""Pydantic models: the typed contract of the API (STUDENT scaffold).

FastAPI uses these to validate inputs and auto-document every endpoint at /docs.
`ModelInfo` is given as a worked example. Fill the others.
"""

from typing import Optional
from pydantic import BaseModel, Field


# ------------------------------------------------------------------ /model-info  (GIVEN example)
class ModelInfo(BaseModel):
  model_name: str
  target: str
  horizon: str
  n_features: int
  features: list[str]
  test_metrics: dict
  weather_assumption: str


# ------------------------------------------------------------------ /forecast
class Metric(BaseModel):
  mae: Optional[float] = None
  rmse: Optional[float] = None
  mape: Optional[float] = None
  n: int = 0


class ForecastResponse(BaseModel):
  model_name: str
  horizon: str
  n_hours: int
  warmup_hours_dropped: int
  timestamps: list[str]
  predictions: list[float]
  actual: list[Optional[float]]
  reference: list[Optional[float]]
  naive_yesterday: list[Optional[float]]
  peak_demand: float
  average_demand: float
  metrics: dict[str, Metric] = Field(default_factory=dict)


# ------------------------------------------------------------------ /optimize
class OptimizeRequest(BaseModel):
  """Energy-mix optimization request. Demand in MW."""

  demand: float = Field(..., gt=0, description="Demand in MW, must be > 0")
  carbon_limit: Optional[float] = Field(
      None, gt=0, description="Carbon limit, must be > 0"
  )
  renewable_min: Optional[float] = Field(
      None, ge=0, le=1, description="Minimum renewable share between 0 and 1"
  )
  capacities: Optional[dict[str, float]] = None


class Allocation(BaseModel):
  source: str
  generation_mwh: float
  cost: float
  emissions: float
  selected: bool


class OptimizeResponse(BaseModel):
  feasible: bool
  message: str
  demand: Optional[float] = None
  allocation: list[Allocation] = Field(default_factory=list)
  total_cost: Optional[float] = None
  total_emissions: Optional[float] = None
  renewable_share: Optional[float] = None