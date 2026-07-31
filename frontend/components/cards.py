"""KPI cards built on st.metric."""
import streamlit as st
from utils.formatting import mw, pct


def forecast_kpis(res: dict):
    c = st.columns(4)
    c[0].metric("Model", res["model_name"])
    c[1].metric("Peak (forecast)", mw(res["peak_demand"]))
    c[2].metric("Average (forecast)", mw(res["average_demand"]))
    m = res["metrics"].get("model")
    c[3].metric("Model MAE", mw(m["mae"]) if m else "no ground truth")


def optimize_kpis(out: dict):
    c = st.columns(4)
    c[0].metric("Feasible", "yes" if out["feasible"] else "no")
    c[1].metric("Total cost", f"EUR {out['total_cost']:,.0f}" if out.get("total_cost") is not None else "-")
    c[2].metric("Emissions", f"{out['total_emissions']/1000:,.0f} tCO2e" if out.get("total_emissions") is not None else "-")
    c[3].metric("Renewable share", pct(out["renewable_share"] * 100) if out.get("renewable_share") is not None else "-")
