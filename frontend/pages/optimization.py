"""Page 4 (advanced): use the forecast to recommend an energy mix."""
import pandas as pd
import streamlit as st

from utils import api_client
from components import charts, cards


def render():
    st.title("Energy-Mix Optimization")
    st.caption("Advanced module. This page optimizes one demand level, usually the forecast peak, "
               "under capacity, carbon and renewable-share constraints.")

    base = st.session_state.get("base", api_client.DEFAULT_BASE)
    res = st.session_state.get("forecast")
    default_demand = float(res["peak_demand"]) if res else 34000.0
    if res:
        st.info(
            f"Using the forecast peak as the default demand ({default_demand:,.0f} MW). "
            "A full hour-by-hour 24 h dispatch would repeat this optimization for each forecast hour."
        )
    else:
        st.info("Run a forecast first to use its peak demand as the default optimization target.")

    c = st.columns(3)
    demand = c[0].number_input("Demand to cover (MW)", min_value=1000.0, max_value=80000.0,
                               value=round(default_demand, 0), step=500.0,
                               help="Defaults to the forecast peak when a forecast is loaded.")
    renewable_min = c[1].slider("Minimum renewable share", 0.0, 1.0, 0.0, 0.05)
    use_carbon = c[2].checkbox("Apply a carbon cap")
    carbon_limit = None
    if use_carbon:
        carbon_limit = c[2].number_input("Carbon cap (kgCO2e)", min_value=0.0,
                                         value=float(round(demand * 250, -3)), step=100000.0)

    if st.button("Optimize", type="primary"):
        payload = {"demand": demand,
                   "renewable_min": renewable_min if renewable_min > 0 else None,
                   "carbon_limit": carbon_limit}
        ok, out = api_client.optimize(base, payload)
        if not ok:
            st.error(f"Backend error: {out}")
            return
        if not out["feasible"]:
            st.error(out["message"])
            st.caption("Relax a constraint: lower the renewable floor, raise the carbon cap, or reduce demand.")
            return

        cards.optimize_kpis(out)
        st.plotly_chart(charts.mix_bar(out["allocation"]), width="stretch")
        tbl = pd.DataFrame(out["allocation"]).rename(columns={
            "generation_mwh": "Generation (MWh)", "cost": "Cost (EUR)",
            "emissions": "Emissions (kgCO2e)", "selected": "Selected", "source": "Source"})
        st.dataframe(tbl.set_index("Source"), width="stretch")
        st.success(out["message"])
