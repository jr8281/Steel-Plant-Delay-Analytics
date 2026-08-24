import streamlit as st
from datetime import date

from pages_content.utils import api_request, render_hero_banner


def render():
    render_hero_banner()
    st.markdown('<h2 class="page-title">Delay Risk Prediction</h2>', unsafe_allow_html=True)
    st.markdown(
        '<p class="assistant-subtitle">Predicts the expected delay-duration risk bucket '
        '(short / medium / long) for a given shop, equipment, and cause, based on historical patterns.</p>',
        unsafe_allow_html=True,
    )

    info = api_request("GET", "/predictions/model-info")

    if not info or not info.get("trained"):
        st.warning(
            "No trained model is available yet. An administrator needs to train the model "
            "from the current dataset before predictions can be made."
        )
        if st.session_state.get("role") == "admin":
            if st.button("Train Model Now", type="primary"):
                with st.spinner("Training model on current data..."):
                    result = api_request("POST", "/predictions/retrain")
                if result:
                    st.success(f"Model trained. Accuracy: {result['accuracy']:.1%}, Macro-F1: {result['macro_f1']:.3f}")
                    st.rerun()
        return

    with st.expander("📊 Model performance (honest, evaluated on held-out test data)", expanded=False):
        col1, col2, col3 = st.columns(3)
        col1.metric("Accuracy", f"{info['accuracy']:.1%}")
        col2.metric("Macro F1", f"{info['macro_f1']:.3f}")
        col3.metric("Training samples", info["n_samples"])
        st.caption(f"Target definition: {info['target_definition']}")
        st.caption(f"Trained at: {info['trained_at']}")
        if info["n_samples"] < 500:
            st.info(
                "This model is trained on a small sample dataset from a limited internship data export. "
                "Accuracy is expected to improve substantially with the full production dataset."
            )

    st.markdown("### Make a Prediction")
    filters = api_request("GET", "/filters")

    col1, col2, col3 = st.columns(3)
    with col1:
        shops = api_request("GET", "/shops") or []
        shop_options = {s["name"]: s["shop_code"] for s in shops}
        shop_name = st.selectbox("Shop", options=list(shop_options.keys()) if shop_options else ["No shops available"])
    with col2:
        equipment_options = (filters or {}).get("equipment", [])
        equipment = st.selectbox("Equipment", options=["(unspecified)"] + equipment_options)
    with col3:
        cause_options = (filters or {}).get("causes", [])
        cause = st.selectbox("Cause / Agency", options=cause_options if cause_options else ["No causes available"])

    predict_date = st.date_input("Date", value=date.today())

    if st.button("Predict Delay Risk", type="primary"):
        payload = {
            "shop_code": shop_options.get(shop_name, ""),
            "equipment_name": None if equipment == "(unspecified)" else equipment,
            "agency_code": cause,
            "delay_date": predict_date.isoformat(),
        }
        result = api_request("POST", "/predictions/predict", json=payload)
        if result:
            bucket = result["predicted_bucket"]
            confidence = result["confidence"]

            bucket_colors = {"short": "🟢", "medium": "🟡", "long": "🔴"}
            st.markdown(f"## {bucket_colors.get(bucket, '⚪')} Predicted risk: **{bucket.upper()}**")
            st.caption(f"Confidence: {confidence:.1%}")

            st.markdown("#### Full probability breakdown")
            for label, prob in sorted(result["probabilities"].items(), key=lambda x: -x[1]):
                st.progress(prob, text=f"{label}: {prob:.1%}")