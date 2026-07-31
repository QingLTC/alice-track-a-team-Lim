"""Page 1: understand the uploaded data before forecasting."""
import pandas as pd
import streamlit as st

from components import charts


def render():
    st.title("Data Overview")
    st.caption("Sanity-check the uploaded CSV before sending it to the forecasting backend.")
    df = st.session_state.get("uploaded_df")
    if df is None:
        st.info("Upload an energy CSV in the sidebar to begin. For the demo, use backend/sample_test/energy_2018_slice.csv.")
        return

    required = ["time", "total load actual"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        st.error(f"Missing required column(s): {', '.join(missing)}")

    time = pd.to_datetime(df["time"], utc=True, errors="coerce") if "time" in df else None
    c = st.columns(3)
    c[0].metric("Rows (hours)", f"{len(df):,}")
    c[1].metric("Columns", f"{df.shape[1]}")
    if time is not None:
        c[2].metric("Period", f"{time.min().date()} to {time.max().date()}")

    if "total load actual" in df.columns and time is not None:
        st.plotly_chart(charts.demand_history(df.assign(time=time)), width="stretch")

    st.subheader("First rows")
    st.dataframe(df.head(12), width="stretch")
    st.caption("This is the raw upload. The backend does the cleaning, weather merge and feature building.")
