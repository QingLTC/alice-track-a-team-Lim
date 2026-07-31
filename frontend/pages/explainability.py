"""Page 3: model explanation. Shows the model card and the XAI figures from the notebook."""
from pathlib import Path
import streamlit as st

from utils import api_client
from utils.formatting import mw, pct

IMG = Path(__file__).resolve().parents[2] / "images" / "partC"


def _img(name: str, caption: str):
    p = IMG / name
    if p.exists():
        st.image(str(p), caption=caption, width="stretch")
    else:
        st.caption(f"(missing image: {name} - re-run notebook 05 to generate it)")


def render():
    st.title("Model Explanation")
    base = st.session_state.get("base", api_client.DEFAULT_BASE)
    ok, info = api_client.model_info(base)
    if not ok:
        st.error(f"Cannot reach the backend: {info}")
        return

    c = st.columns(3)
    c[0].metric("Model", info["model_name"])
    c[1].metric("Horizon", info["horizon"])
    tm = info.get("test_metrics", {})
    c[2].metric("Test MAE (2018)", mw(tm.get("MAE")))
    st.caption(f"Weather assumption: {info['weather_assumption']}")

    st.subheader("Which features drive the forecast (permutation importance)")
    _img("permutation_importance.png",
         "Shuffle a feature; if the error rises, the model relied on it. Day-ahead lags and hour dominate.")

    st.subheader("Why a single prediction came out as it did (SHAP)")
    a, b = st.columns(2)
    with a:
        _img("shap_waterfall.png", "One hour explained: each feature pushes the prediction up or down.")
    with b:
        _img("shap_beeswarm.png", "The whole model: red = high feature value. High demand yesterday pushes today up.")
    _img("shap_temp.png", "Temperature effect: little impact in mild weather, a sharp rise above 25 C (cooling demand).")

    st.info(
        "The important features are exactly the ones the Part A reading predicted: the day-ahead demand "
        "lags (load_lag_24, load_lag_168), the hour of day, and temperature. The model uses legitimate, "
        "available information and shows no reliance on leakage-prone variables.")
