import base64
from pathlib import Path
import requests
import streamlit as st
from pages_content.utils import API


def load_css():
    css_path = Path(__file__).parent.parent / "assets" / "styles" / "login.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def image_to_base64(path: Path):
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def render():
    load_css()

    assets = Path(__file__).parent.parent / "assets" / "images"
    logo_path = assets / "logo.png"

    logo_html = ""
    b64 = image_to_base64(logo_path)
    if b64:
        logo_html = f'<img src="data:image/png;base64,{b64}" width="72">'

    # Background image: embedded as base64 rather than referenced via a
    # CSS url() path. A relative url("...") in login.css is resolved by
    # the BROWSER against the current page URL, not your project folder —
    # inside Docker this almost never lines up with where Streamlit
    # actually serves static files from, so the image silently fails to
    # load. Base64-embedding it here guarantees it always renders.
    background_style = ""
    background_candidates = sorted(assets.glob("background.*"))
    if background_candidates:
        bg_path = background_candidates[0]
        bg_mime = "jpeg" if bg_path.suffix.lower() in (".jpg", ".jpeg") else bg_path.suffix.lstrip(".").lower()
        bg_b64 = image_to_base64(bg_path)
        if bg_b64:
            background_style = (
                f' style="background-image:linear-gradient(rgba(3,10,18,.72),rgba(3,10,18,.82)),'
                f'url(data:image/{bg_mime};base64,{bg_b64});"'
            )

    # Decorative full-screen backdrop only — deliberately has no children.
    # A hand-written <div> here can't be closed later by a different
    # st.markdown call (see login.css comments), so all real content below
    # lives in an actual Streamlit container instead.
    st.markdown(f'<div class="login-page"{background_style}></div>', unsafe_allow_html=True)

    card = st.container(key="login_card")

    with card:
        st.markdown(
            f"""
<div class="brand">
  {logo_html}
  <div class="brand-text">
    <div class="brand-title">Steel Plant Delay Analytics</div>
    <div class="brand-subtitle">Enterprise Operational Intelligence</div>
  </div>
</div>

<div class="hero-badge">LIVE MONITORING</div>

<div class="login-title">Welcome Back</div>

<div class="login-description">
  Sign in to access production analytics,
  maintenance insights and operational dashboards.
</div>
""",
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):

            username = st.text_input(
                "Username",
                placeholder="Enter your username"
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )

            c1, c2 = st.columns([1, 1])

            with c1:
                st.checkbox("Remember Me")

            with c2:
                st.markdown(
                    '<div class="forgot-password"><a href="#">Forgot Password?</a></div>',
                    unsafe_allow_html=True
                )

            submitted = st.form_submit_button(
                "Access Dashboard →",
                use_container_width=True
            )

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                with st.spinner("Signing in..."):
                    try:
                        response = requests.post(
                            f"{API}/auth/login",
                            json={
                                "username": username,
                                "password": password
                            },
                            timeout=20
                        )

                        if not response.ok:
                            try:
                                detail = response.json().get(
                                    "detail",
                                    "Invalid username or password."
                                )
                            except Exception:
                                detail = "Unable to sign in."

                            st.error(detail)

                        else:
                            data = response.json()

                            st.session_state["authenticated"] = True
                            st.session_state["token"] = data["access_token"]
                            st.session_state["username"] = data["username"]
                            st.session_state["role"] = data["role"]
                            st.session_state["shop_id"] = data.get("shop_id")

                            st.success("Login successful!")

                            st.rerun()

                    except requests.RequestException:
                        st.error(
                            "Unable to connect to the FastAPI server. "
                            "Please make sure the backend is running."
                        )

        st.markdown(
            """
            <div class="login-footer">
                © 2026 Steel Plant Delay Analytics<br>
                Enterprise Operational Intelligence Platform
            </div>
            """,
            unsafe_allow_html=True,
        )