"""Page 2: the 24-hour forecast, the comparison, and the honest read (STUDENT scaffold)."""

import pandas as pd
import streamlit as st

from components import cards, charts


def render():
  st.title("24-Hour Forecast")
  res = st.session_state.get("forecast")
  if not res:
    st.info(
        "Upload a CSV in the sidebar, check it in Data Overview, then press"
        " 'Run forecast'."
    )
    return

  st.caption(
      f"Showing one {res['n_hours']}-hour day-ahead window. "
      f"The backend dropped {res['warmup_hours_dropped']} warm-up rows because"
      " lag features need history. "
      f"Model horizon: {res['horizon']}."
  )

  cards.forecast_kpis(res)

  st.plotly_chart(charts.forecast_curve(res), use_container_width=True)

  metrics = res.get("metrics") or {}
  if metrics:
    st.subheader("Model vs baselines")
    st.caption(
        "Scored only on the hours where the actual demand is present in the"
        " upload."
    )
    left, right = st.columns([1, 1])
    with left:
      df_metrics = (
          pd.DataFrame({
              k: {
                  "MAE (MW)": v["mae"],
                  "RMSE (MW)": v["rmse"],
                  "MAPE (%)": v["mape"],
              }
              for k, v in metrics.items()
          })
          .T.round(2)
      )
      st.dataframe(df_metrics, use_container_width=True)

    with right:
      st.plotly_chart(charts.comparison_bar(metrics), use_container_width=True)

    _interpretation(metrics)
  else:
    st.info(
        "The upload had no ground-truth demand for the forecast window, so"
        " only predictions are shown."
    )

  if _has_values(res.get("actual", [])):
    with st.expander("Residual diagnostics", expanded=False):
      st.caption(
          "Residual = actual demand - model prediction. Values close to zero"
          " mean the model is close; "
          "positive values mean the model under-predicted; negative values mean"
          " it over-predicted."
      )
      st.plotly_chart(charts.residual_hist(res), use_container_width=True)

  out = pd.DataFrame({
      "time": res["timestamps"],
      "prediction": res["predictions"],
      "actual": res["actual"],
      "reference": res["reference"],
      "naive_yesterday": res["naive_yesterday"],
  })
  st.download_button(
      "Download predictions (CSV)",
      out.to_csv(index=False).encode(),
      file_name="forecast.csv",
      mime="text/csv",
  )


def _has_values(values: list) -> bool:
  return any(v is not None for v in values)


def _interpretation(metrics: dict):
  model = metrics.get("model", {}).get("mae")
  naive = metrics.get("naive_yesterday", {}).get("mae")
  ref = metrics.get("reference", {}).get("mae")
  lines = []
  if model is not None and naive:
    gain = (naive - model) / naive * 100
    if model < naive:
      lines.append(
          "The model beats the naive 'same hour yesterday' baseline by about"
          f" {gain:.0f} % on MAE, so machine learning is adding real value."
      )
    else:
      lines.append(
          "The model does not beat the naive 'same hour yesterday' baseline on"
          f" this window (MAE {model:,.0f} vs {naive:,.0f} MW), so this slice"
          " deserves a closer look."
      )
  if model is not None and ref is not None:
    if ref < model:
      lines.append(
          "The provided reference forecast is still ahead (MAE {ref:,.0f} vs"
          f" {model:,.0f} MW). That is expected: it is a professional"
          " day-ahead system. We report the gap honestly."
      )
    else:
      lines.append(
          "The model is on par with or ahead of the provided reference (MAE"
          f" {model:,.0f} vs {ref:,.0f} MW)."
      )
  if lines:
    st.info(" ".join(lines))