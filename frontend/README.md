# Build the Dashboard (student scaffold)

Session goal: build the Streamlit dashboard, connect it to the FastAPI backend,
and handle errors cleanly. The structure, sidebar and most components are given
so you focus on the three things that matter.

## What is given vs what you build

| Given (do not edit) | You build (look for `# TODO`) |
|---|---|
| `app.py` (navigation), `components/sidebar.py`, `components/cards.py` | `utils/api_client.py` (connect to the backend) |
| `pages/data_overview.py`, `explainability.py`, `optimization.py` | `pages/forecasting.py` (assemble the forecast page) |
| `utils/formatting.py`, most of `components/charts.py` | `components/charts.py::forecast_curve` (the main chart) |

## Steps
1. `utils/api_client.py`: complete `model_info`, `forecast`, `optimize`
   (copy the pattern in `health`). This is the **connect to backend** part.
2. `components/charts.py::forecast_curve`: build the actual-vs-forecast line chart.
3. `pages/forecasting.py`: wire the KPI row, the forecast chart, the metrics
   table and the comparison bar (four `# TODO`s).

## Run

```bash
# 1) start the backend on :8000 first (see ../backend)
cd "$(dirname "$0")"
python -m streamlit run app.py
```

Sidebar: confirm "Connected", upload `../backend/sample_test/energy_2018_slice.csv`,
press **Run forecast**. You are done when the Forecast page shows the curve,
the KPI cards and the model-vs-baselines table.

## Error handling
Every `api_client` function returns `(ok, data_or_error)`. When `ok` is False,
show the error with `st.error(...)` instead of crashing. The sidebar already
does this for the forecast call; keep the same habit in your pages.
