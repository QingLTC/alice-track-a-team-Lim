"""
The sidebar is the control panel shared by every page: pick the backend, upload
a CSV, and run the 24-hour forecast. Results land in st.session_state so all
pages can read them.
"""
from io import BytesIO
import pandas as pd
import streamlit as st

from utils import api_client

FORECAST_HOURS = 24


def render_sidebar():
    st.sidebar.title("Energy Forecasting")
    st.sidebar.caption("Backend -> upload CSV -> run forecast")

    # ---- backend connection
    st.sidebar.subheader("Backend")
    base = st.sidebar.text_input("Backend URL", st.session_state.get("base", api_client.DEFAULT_BASE))
    st.session_state["base"] = base
    ok, info = api_client.health(base)
    if ok:
        st.sidebar.success(f"Connected to {info.get('model_name', 'model')}")
    else:
        st.sidebar.error("Backend offline. Start it, then reload.")
        st.sidebar.code("cd backend\n../.venv/bin/python -m uvicorn main:app --reload --port 8000")

    st.sidebar.divider()

    # ---- data upload
    st.sidebar.subheader("Input data")
    up = st.sidebar.file_uploader("Energy CSV", type="csv")
    st.sidebar.caption("Demo file: backend/sample_test/energy_2018_slice.csv")
    if up is not None:
        st.session_state["uploaded_name"] = up.name
        st.session_state["uploaded_bytes"] = up.getvalue()
        try:
            st.session_state["uploaded_df"] = pd.read_csv(BytesIO(st.session_state["uploaded_bytes"]))
        except Exception:
            st.session_state["uploaded_df"] = None

    uploaded_df = st.session_state.get("uploaded_df")
    if uploaded_df is not None:
        st.sidebar.caption(
            f"Loaded {st.session_state.get('uploaded_name', 'CSV')}: "
            f"{len(uploaded_df):,} rows, {uploaded_df.shape[1]} columns"
        )

    st.sidebar.divider()

    # ---- forecast controls
    st.sidebar.subheader("Forecast")
    st.sidebar.caption(
        "The workshop dashboard always requests one 24-hour day-ahead window. "
        "In the demo CSV, the backend displays the most recent scorable 24-hour window."
    )

    # ---- run
    can_run = ok and "uploaded_bytes" in st.session_state
    if st.sidebar.button("Run forecast", type="primary", disabled=not can_run, width="stretch"):
        with st.spinner("Calling the forecasting backend..."):
            ok2, res = api_client.forecast(
                base, st.session_state["uploaded_bytes"], st.session_state["uploaded_name"], FORECAST_HOURS)
        if ok2:
            st.session_state["forecast"] = res
            st.sidebar.success(f"Forecast ready: {res['n_hours']}-hour window")
        else:
            st.session_state.pop("forecast", None)
            st.sidebar.error(f"Forecast failed: {res}")

    if ok and "uploaded_bytes" not in st.session_state:
        st.sidebar.caption("Upload a CSV to enable the forecast button.")

    st.sidebar.caption("The dashboard runs no model itself. Every number comes from the backend.")
