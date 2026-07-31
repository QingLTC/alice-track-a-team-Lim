"""
Preprocessing service: turn an uploaded energy CSV into the exact feature table
the model was trained on.

This is the single most important guarantee of the backend: the features built
here must be IDENTICAL to the ones built in notebook 04. Same weather
aggregation, same clipping, same target interpolation, same calendar / cyclic /
lag / rolling definitions, same day-ahead rule (nothing younger than 24 h).
If this drifts from training, the model silently degrades.
"""
from functools import lru_cache
import numpy as np
import pandas as pd

from config import (
    TARGET, REFERENCE, FEATURES, WEATHER_FEATURES,
    WEATHER_PATH, PRESSURE_BOUNDS, WIND_BOUNDS,
)


@lru_cache(maxsize=1)
def load_weather_hourly() -> pd.DataFrame:
    """Load the bundled aggregated weather once and cache it."""
    w = pd.read_csv(WEATHER_PATH)
    w["time"] = pd.to_datetime(w["time"], utc=True)
    return w


def read_energy_csv(raw_bytes: bytes) -> pd.DataFrame:
    """Parse an uploaded energy CSV and validate the minimum required columns."""
    from io import BytesIO
    df = pd.read_csv(BytesIO(raw_bytes))
    if "time" not in df.columns:
        raise ValueError("CSV must contain a 'time' column.")
    if TARGET not in df.columns:
        raise ValueError(f"CSV must contain the '{TARGET}' column (needed to build demand lags).")
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
    if df["time"].isna().any():
        raise ValueError("Some 'time' values could not be parsed as timestamps.")
    df = df.sort_values("time").reset_index(drop=True)
    if df["time"].duplicated().any():
        raise ValueError("Duplicate timestamps found; the series must be hourly and unique.")
    return df


def build_features(energy: pd.DataFrame) -> pd.DataFrame:
    """
    Reproduce the notebook-04 feature pipeline on an uploaded energy slice.

    Returns a frame with: time, the original target and reference (if present),
    a `target_missing` flag, and the 19 model features. Warm-up rows that lack
    enough history keep NaN features and are dropped later by the forecaster.
    """
    df = energy.copy()

    # 1. Weather: merge the bundled hourly aggregate unless the upload already
    # carries the weather columns. Then clip the physically-bounded variables.
    if not set(WEATHER_FEATURES).issubset(df.columns):
        df = df.merge(load_weather_hourly(), on="time", how="left")
    if "pressure" in df.columns:
        df["pressure"] = df["pressure"].clip(*PRESSURE_BOUNDS)
    df["wind_speed"] = df["wind_speed"].clip(*WIND_BOUNDS)

    # 2. Target handling: keep the original (with its gaps flagged) and build an
    # interpolated copy used ONLY to compute lags/rolling, never scored.
    df["target_missing"] = df[TARGET].isna()
    df["target_filled"] = df.set_index("time")[TARGET].interpolate("time").values

    # 3. Calendar features.
    df["hour"] = df["time"].dt.hour
    df["day_of_week"] = df["time"].dt.dayofweek          # 0 = Monday
    df["month"] = df["time"].dt.month
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # 4. Cyclic encodings (hours/days/months live on a circle).
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    # 5. Lag features on the filled target. Day-ahead rule: smallest lag is 24.
    for lag in (24, 48, 168):
        df[f"load_lag_{lag}"] = df["target_filled"].shift(lag)

    # 6. Rolling features. Shift by 24 FIRST so the window ends 24 h before the
    # target hour and never uses information we would not have at forecast time.
    df["load_roll_mean_24"] = df["target_filled"].shift(24).rolling(24).mean()
    df["load_roll_std_24"] = df["target_filled"].shift(24).rolling(24).std()
    df["load_roll_mean_168"] = df["target_filled"].shift(24).rolling(168).mean()

    keep = ["time", "target_missing"]
    if TARGET in df.columns:
        keep.append(TARGET)
    if REFERENCE in df.columns:
        keep.append(REFERENCE)
    return df[keep + FEATURES]


def split_ready_rows(feat: pd.DataFrame):
    """
    Separate rows the model can score (all features present) from warm-up rows.
    Returns (ready_frame, n_dropped).
    """
    ready = feat.dropna(subset=FEATURES).copy()
    return ready, len(feat) - len(ready)
