"""Plotly figures (STUDENT scaffold). Pure functions: data in, figure out. No Streamlit calls."""

import pandas as pd
import plotly.graph_objects as go

BLUE, ORANGE, GREEN, GREY, RED = (
    "#1f6feb",
    "#fb8500",
    "#2a9d8f",
    "#9aa0a6",
    "#d62828",
)
_LAYOUT = dict(
    height=430,
    margin=dict(l=10, r=10, t=48, b=10),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
    ),
)


def _has(series):
  return any(v is not None for v in series)


def forecast_curve(res: dict) -> go.Figure:
  """The main chart: actual demand vs the model forecast (and the reference)."""
  x = pd.to_datetime(res["timestamps"])
  fig = go.Figure()

  if _has(res.get("actual", [])):
    fig.add_scatter(
        x=x,
        y=res["actual"],
        mode="lines",
        line=dict(color=BLUE, width=2),
        name="actual demand",
    )

  if _has(res.get("predictions", [])):
    model_name = res.get("model_name", "model")
    fig.add_scatter(
        x=x,
        y=res["predictions"],
        mode="lines",
        line=dict(color=ORANGE, dash="dash", width=2),
        name=f"forecast ({model_name})",
    )

  if _has(res.get("reference", [])):
    fig.add_scatter(
        x=x,
        y=res["reference"],
        mode="lines",
        line=dict(color=GREEN, dash="dot", width=2),
        name="provided reference",
    )

  fig.update_layout(
      title="Day-ahead demand forecast", yaxis_title="MW", **_LAYOUT
  )
  return fig


def demand_history(df: pd.DataFrame, target="total load actual") -> go.Figure:
  t = pd.to_datetime(df["time"])
  fig = go.Figure()
  fig.add_scatter(
      x=t, y=df[target], mode="lines", line=dict(color=BLUE), name=target
  )
  fig.update_layout(
      title="Uploaded demand history", yaxis_title="MW", **_LAYOUT
  )
  return fig


def comparison_bar(metrics: dict) -> go.Figure:
  """Bar of MAE per model / baseline / reference (lower is better). GIVEN."""
  label = {
      "model": "Model",
      "naive_yesterday": "Naive (yesterday)",
      "reference": "Reference",
  }
  order = ["reference", "model", "naive_yesterday"]
  rows = [
      (label[k], metrics[k]["mae"])
      for k in order
      if k in metrics and metrics[k]["mae"] is not None
  ]
  rows.sort(key=lambda r: r[1])
  colors = [
      GREEN if n == "Reference" else (ORANGE if n.startswith("Model") else GREY)
      for n, _ in rows
  ]
  fig = go.Figure(
      go.Bar(
          x=[v for _, v in rows],
          y=[n for n, _ in rows],
          orientation="h",
          marker_color=colors,
          text=[f"{v:,.0f}" for _, v in rows],
          textposition="outside",
      )
  )
  fig.update_layout(
      title="Test error (MAE, MW) - lower is better",
      xaxis_title="MAE (MW)",
      height=300,
      margin=dict(l=10, r=30, t=48, b=10),
  )
  return fig


def residual_hist(res: dict) -> go.Figure:
  pairs = [
      (a, p)
      for a, p in zip(res["actual"], res["predictions"])
      if a is not None
  ]
  resid = [a - p for a, p in pairs]
  fig = go.Figure(go.Histogram(x=resid, nbinsx=40, marker_color=GREY))
  fig.add_vline(x=0, line_width=2, line_dash="dash", line_color=RED)
  fig.update_layout(
      title="Forecast errors around zero",
      xaxis_title="Actual - predicted (MW)",
      height=300,
      margin=dict(l=10, r=10, t=48, b=10),
  )
  return fig


def mix_bar(alloc: list) -> go.Figure:
  alloc = [a for a in alloc if a["generation_mwh"] > 0]
  fig = go.Figure(
      go.Bar(
          x=[a["source"] for a in alloc],
          y=[a["generation_mwh"] for a in alloc],
          marker_color=[
              GREEN if a["source"] in ("Solar", "Wind onshore", "Hydro") else GREY
              for a in alloc
          ],
          text=[f"{a['generation_mwh']:,.0f}" for a in alloc],
          textposition="outside",
      )
  )
  fig.update_layout(
      title="Recommended generation by source",
      yaxis_title="MWh",
      height=340,
      margin=dict(l=10, r=10, t=48, b=10),
  )
  return fig