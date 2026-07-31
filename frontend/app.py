"""
Track A - Energy Forecasting dashboard (Streamlit).

The user-facing product. It talks to the FastAPI backend and never runs model
logic itself. Modular by design: pages/ hold the screens, components/ the
reusable widgets and charts, utils/ the API client and formatting.

Run (backend must be up on :8000):
    cd frontend
    ../.venv/bin/python -m streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="Track A - Energy Forecasting", page_icon=":material/bolt:", layout="wide")

from components.sidebar import render_sidebar
from pages import data_overview, forecasting, explainability, optimization

# st.navigation defines the pages and disables Streamlit's automatic pages/ discovery.
nav = st.navigation([
    st.Page(data_overview.render, title="Data Overview", url_path="overview", icon=":material/table_chart:", default=True),
    st.Page(forecasting.render, title="Forecast", url_path="forecast", icon=":material/show_chart:"),
    st.Page(explainability.render, title="Explainability", url_path="explainability", icon=":material/insights:"),
    st.Page(optimization.render, title="Energy Mix", url_path="mix", icon=":material/bolt:"),
])

render_sidebar()
nav.run()
