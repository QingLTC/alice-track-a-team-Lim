# Build the Backend (student scaffold)

Session goal: reload the model you exported in the notebook and serve it through
a FastAPI backend, with Pydantic input validation.

## What is given vs what you build

| Given (do not edit) | You build (look for `# TODO`) |
|---|---|
| `config.py` (paths, the 19 features, energy-mix table) | `schemas.py` (Pydantic models) |
| `services/preprocessing.py` (your notebook-04 features) | `services/forecasting.py` (load model, predict) |
| `services/optimization.py` (energy-mix LP) | `main.py` (the endpoints) |
| `artifacts/weather_hourly.csv`, `sample_test/` | |

The shared model is loaded from `../models/forecasting_model.joblib` (exported
in notebook 05). You may replace it with your own compatible artifact, but using
the shared model keeps everyone on the same base for this session.

## Steps

1. `schemas.py`: complete `ForecastResponse` and `OptimizeRequest` (the Pydantic
   validation: `demand > 0`, `renewable_min` in `[0, 1]`).
2. `services/forecasting.py`: complete `load_artifact` (`joblib.load`) and the
   `model.predict` + metrics lines in `run_forecast`.
3. `main.py`: complete `/model-info`, `/forecast`, `/optimize`.

## Run and test

```bash
../.venv/bin/python -m uvicorn main:app --reload --port 8000
# docs: http://127.0.0.1:8000/docs
curl -s http://127.0.0.1:8000/health
curl.exe -F "file=@sample_test/energy_2018_slice.csv" "http://127.0.0.1:8000/forecast?last_hours=24"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/optimize" -Method Post -ContentType "application/json" -Body '{"demand":34000,"renewable_min":0.4}'
```

You are done when `/forecast` returns predictions that track the actual demand,
and the naive baseline error is clearly higher than the model error.
