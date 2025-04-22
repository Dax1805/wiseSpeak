import streamlit as st

# ---------- Page Setup ----------
st.set_page_config(page_title="WiseSpeak", page_icon="💬")

# ---------- Styling ----------
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-size: 20px !important;
        line-height: 1.6;
    }
    .stButton>button {
        font-size: 18px !important;
        padding: 10px 20px;
    }
    .stSelectbox label {
        font-weight: bold;
        font-size: 18px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Title ----------
st.title("WiseSpeak")
st.markdown("**AI that speaks your language.**")

# ---------- Name Input ----------
user_name = st.text_input("Before we begin, what should I call you?")
if user_name:
    st.session_state["user_name"] = user_name

# ---------- Hobby Selector ----------
hobby = st.selectbox("What do you enjoy? (optional)", [
    "None",
    "Gardening",
    "Cooking & Baking",
    "Listening to Music",
    "Arts & Crafts",
    "Birdwatching",
    "Walking / Jogging",
    "Puzzles & Games",
    "Reading",
    "Outdoor Chores"
])
st.session_state["hobby"] = hobby

# ---------- Continue Button ----------
if user_name and st.button("Continue to Ask a Question"):
    st.session_state["onboarded"] = True
    st.switch_page("pages/explain.py")
