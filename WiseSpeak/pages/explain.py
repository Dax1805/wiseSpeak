import streamlit as st
import importlib.util
import sys
import os

# ---------- Dynamic Import for prompts.py ----------
PROMPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prompts.py"))
spec = importlib.util.spec_from_file_location("prompts", PROMPT_PATH)
prompts = importlib.util.module_from_spec(spec)
sys.modules["prompts"] = prompts
spec.loader.exec_module(prompts)

# ---------- Page Config ----------
st.set_page_config(page_title="WiseSpeak Chat", page_icon="💬")

# ---------- Accessibility: Font Boost ----------
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
    .stSelectbox label, .stRadio label {
        font-weight: bold;
        font-size: 18px;
    }
    .stMarkdown {
        font-size: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Access Control ----------
if "onboarded" not in st.session_state:
    st.warning("Please complete the onboarding first.")
    st.stop()

# ---------- Get User Data ----------
user_name = st.session_state["user_name"]
hobby = st.session_state["hobby"]

# ---------- Header ----------
st.title("WiseSpeak")
st.subheader("AI that speaks your language.")
st.markdown(f"**Welcome back, {user_name}!**")
st.markdown("---")

# ---------- User Question Input ----------
user_query = st.text_input("What would you like help understanding?",
                           placeholder="e.g., Why is my phone slow today?")
st.markdown("")

# ---------- Explanation Style Toggle ----------
selected_styles = st.multiselect(
    label="Choose how you'd like to see the explanation(s):",
    options=["Short", "Simplify", "Step-by-step"],
    default=["Short"],
    help="Select one or more styles to see multiple formats of the explanation."
)

# ---------- Search Button ----------
if st.button("🔎 Search"):
    if not user_query.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner(f"Thinking..."):
            response = prompts.get_explanation(user_name, user_query, selected_styles, hobby)
            st.session_state["results"] = response

# ---------- Output Display ----------
if "results" in st.session_state and st.session_state["results"]:
    st.markdown("### 🧠 WiseSpeak says:")
    st.write(st.session_state["results"])

# ---------- Suggested Prompts ----------
st.markdown("---")
st.markdown("### Try asking:")
st.markdown("""
- Why is my phone suddenly slower today?  
- What does it mean when it says ‘update failed’?  
- Why is my internet working on one device but not another?  
- What should I do if I clicked a suspicious link?  
- Can I turn off updates without causing problems?
""")
