"""
Forecasting service
"""
from functools import lru_cache
import joblib
import numpy as np
import pandas as pd

from config import FEATURES, MODEL_PATH, REFERENCE, TARGET
from services.preprocessing import build_features, split_ready_rows


@lru_cache(maxsize=1)
def load_artifact() -> dict:
  """Load and cache the exported artifact: model + metadata."""
  art = joblib.load(MODEL_PATH)

  if "model" not in art or "features" not in art:
    raise RuntimeError("Model artifact is missing 'model' or 'features' key.")

  if list(art["features"]) != FEATURES:
    raise RuntimeError(
        f"Artifact features mismatch! Expected {FEATURES}, got"
        f" {list(art['features'])}"
    )

  return art


def model_info() -> dict:
  art = load_artifact()
  return {
      "model_name": art.get("model_name", art["model"].__class__.__name__),
      "target": art.get("target", TARGET),
      "horizon": art.get("horizon", "t+24 (day-ahead)"),
      "n_features": len(art["features"]),
      "features": art["features"],
      "test_metrics": art.get("test_metrics", {}),
      "weather_assumption": art.get("weather_assumption", ""),
  }


def _metrics(y_true, y_pred) -> dict:
  y_true = np.asarray(y_true, float)
  y_pred = np.asarray(y_pred, float)
  mask = ~(np.isnan(y_true) | np.isnan(y_pred))
  if mask.sum() == 0:
    return {"mae": None, "rmse": None, "mape": None, "n": 0}
  yt, yp = y_true[mask], y_pred[mask]
  return {
      "mae": float(np.mean(np.abs(yt - yp))),
      "rmse": float(np.sqrt(np.mean((yt - yp) ** 2))),
      "mape": float(np.mean(np.abs((yt - yp) / yt)) * 100),
      "n": int(mask.sum()),
  }


def run_forecast(
    energy: pd.DataFrame, last_hours: int | None = None
) -> dict:
  """Build features, predict every scorable hour, and package the result."""
  art = load_artifact()
  model = art["model"]

  feat = build_features(energy)
  ready, n_warmup = split_ready_rows(feat) 
  if ready.empty:
    raise ValueError("No hour has enough history (need >= 168 h) to forecast.")

  ready = ready.sort_values("time")
  if last_hours:
    ready = ready.tail(int(last_hours))

  preds = model.predict(ready[FEATURES])

  actual = (
      ready[TARGET].where(~ready["target_missing"])
      if TARGET in ready
      else pd.Series(np.nan, index=ready.index)
  )
  reference = (
      ready[REFERENCE]
      if REFERENCE in ready
      else pd.Series(np.nan, index=ready.index)
  )
  naive = ready["load_lag_24"]

  metrics = {}
  if actual.notna().any():
    metrics["model"] = _metrics(actual, preds)
    metrics["naive_yesterday"] = _metrics(actual, naive)
    if reference.notna().any():
      metrics["reference"] = _metrics(actual, reference)

  def col(s):
    return [None if pd.isna(v) else round(float(v), 2) for v in s]

  return {
      "model_name": art.get("model_name", model.__class__.__name__),
      "horizon": art.get("horizon", "t+24 (day-ahead)"),
      "n_hours": int(len(ready)),
      "warmup_hours_dropped": int(n_warmup),
      "timestamps": [t.strftime("%Y-%m-%dT%H:%M:%S%z") for t in ready["time"]],
      "predictions": [round(float(v), 2) for v in preds],
      "actual": col(actual),
      "reference": col(reference),
      "naive_yesterday": col(naive),
      "peak_demand": round(float(np.max(preds)), 2),
      "average_demand": round(float(np.mean(preds)), 2),
      "metrics": metrics,
  }