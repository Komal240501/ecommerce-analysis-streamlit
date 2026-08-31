import json
import os

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Session Conversion Predictor", page_icon="🛒", layout="centered")

MODEL_PATH = "conversion_model.pkl"
OPTIONS_PATH = "feature_options.json"

# --- Fallback dropdown values (used only if feature_options.json is missing) ---
DEFAULT_OPTIONS = {
    "utm_source": ["gsearch", "bsearch", "socialbook"],
    "utm_campaign": ["nonbrand", "brand", "brand_seo_traffic"],
    "device_type": ["desktop", "mobile"],
}


@st.cache_resource
def load_model():
    import pickle
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


@st.cache_data
def load_options():
    if os.path.exists(OPTIONS_PATH):
        with open(OPTIONS_PATH, "r") as f:
            return json.load(f)
    return DEFAULT_OPTIONS


st.title("🛒 Website Session Conversion Predictor")
st.caption(
    "Predicts the probability that a website session converts into an order, "
    "based on the logistic regression pipeline trained on the e-commerce analytics capstone data."
)

if not os.path.exists(MODEL_PATH):
    st.error(
        f"'{MODEL_PATH}' not found. Put conversion_model.pkl in the same folder as app.py "
        "(it's created by the pipeline's pickle.dump step)."
    )
    st.stop()

model = load_model()
options = load_options()

if not os.path.exists(OPTIONS_PATH):
    st.info(
        "Using default dropdown values — add feature_options.json (see save_feature_options.py) "
        "to show the exact categories from your data."
    )

st.subheader("Session details")

col1, col2 = st.columns(2)
with col1:
    utm_source = st.selectbox("UTM Source", options["utm_source"])
    utm_campaign = st.selectbox("UTM Campaign", options["utm_campaign"])
with col2:
    device_type = st.selectbox("Device Type", options["device_type"])
    is_repeat_session = st.selectbox("Repeat Session?", ["No", "Yes"])

if st.button("Predict Conversion", type="primary"):
    input_df = pd.DataFrame([{
        "utm_source": utm_source,
        "utm_campaign": utm_campaign,
        "device_type": device_type,
        "is_repeat_session": 1 if is_repeat_session == "Yes" else 0,
    }])

    pred = model.predict(input_df)[0]
    proba = model.predict_proba(input_df)[0][1]

    st.divider()
    st.metric("Conversion Probability", f"{proba * 100:.2f}%")
    if pred == 1:
        st.success("Predicted: Session is LIKELY to convert")
    else:
        st.warning("Predicted: Session is UNLIKELY to convert")

    with st.expander("Session input used"):
        st.dataframe(input_df)

st.divider()
st.caption("Model: Logistic Regression (class_weight='balanced') · Features: utm_source, utm_campaign, device_type, is_repeat_session")
