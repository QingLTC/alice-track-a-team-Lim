"""
Central configuration for the Track A forecasting backend.

Everything the backend needs to know that is NOT logic lives here: where the
artifacts are, the exact feature list the model expects, and the fixed
energy-mix parameters imposed by the brief. Keeping this in one place means the
preprocessing, forecasting and optimization services all agree on the contract.
"""
from pathlib import Path
import os

# ------------------------------------------------------------------ paths
BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent

# The model is exported by notebook 05 into <repo>/models. Overridable via env
# var so the backend can be moved without editing code.
MODEL_PATH = Path(os.environ.get("MODEL_PATH", REPO_ROOT / "models" / "forecasting_model.joblib"))
# Aggregated, cleaned hourly weather (one row per hour) bundled with the backend.
# It stands in for the day-ahead weather feed a real system would query.
WEATHER_PATH = Path(os.environ.get("WEATHER_PATH", BACKEND_DIR / "artifacts" / "weather_hourly.csv"))

# ------------------------------------------------------------------ modeling contract
TARGET = "total load actual"
REFERENCE = "total load forecast"

# The 19 features, in the exact order the model was trained on (notebook 04).
# The backend recomputes these from the uploaded data; it never invents columns.
FEATURES = [
    "hour", "day_of_week", "month", "is_weekend",
    "hour_sin", "hour_cos", "dow_sin", "dow_cos", "month_sin", "month_cos",
    "load_lag_24", "load_lag_48", "load_lag_168",
    "load_roll_mean_24", "load_roll_std_24", "load_roll_mean_168",
    "temp", "humidity", "wind_speed",
]
WEATHER_FEATURES = ["temp", "humidity", "wind_speed"]

# Day-ahead rule: nothing younger than 24 hours may feed a target hour, so the
# smallest usable demand lag is 24. A row needs 168 h of history to be scored.
MIN_HISTORY_HOURS = 168

# Physical clipping bounds, identical to Part B / notebook 04.
PRESSURE_BOUNDS = (870.0, 1085.0)
WIND_BOUNDS = (0.0, 40.0)

# ------------------------------------------------------------------ energy-mix (advanced module)
# Fixed workshop parameters (brief). Cost in EUR/MWh, emissions in kgCO2e/MWh.
# Capacity in MW derived from the observed max hourly generation per source over
# the TRAINING period (2015-2016), rounded; may be overridden per request.
ENERGY_SOURCES = {
    "Solar":        {"cost": 60,  "emissions": 48,  "renewable": True,  "capacity": 5800},
    "Wind onshore": {"cost": 50,  "emissions": 11,  "renewable": True,  "capacity": 17450},
    "Hydro":        {"cost": 55,  "emissions": 24,  "renewable": True,  "capacity": 11200},
    "Nuclear":      {"cost": 180, "emissions": 12,  "renewable": False, "capacity": 7100},
    "Gas":          {"cost": 80,  "emissions": 490, "renewable": False, "capacity": 16250},
    "Coal":         {"cost": 120, "emissions": 820, "renewable": False, "capacity": 8350},
}
