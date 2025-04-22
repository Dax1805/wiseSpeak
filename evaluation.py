import re
import textstat
import streamlit as st

TECHNICAL_JARGON = {
    'algorithm', 'cache', 'kernel', 'bandwidth', 'configure',
    'protocol', 'encryption', 'metadata'
}

def interpret_elder_x(score):
    if score >= 80: return "✅ Excellent (Instantly clear)"
    if score >= 60: return "👍 Good (Understandable with effort)"
    if score >= 40: return "⚠️ Fair (Needs simplification)"
    return "❌ Poor (Confusing)"

# Core Score Functions
def readability_score(text):
    grade = textstat.flesch_kincaid_grade(text)
    return max(0, min(100, 120 - grade * 10))

def simplicity_score(text):
    return min(100, (1 - (len(text.split()) / 100)) * 100)

def actionability_score(text):
    text_lower = text.lower()
    return min(100,
               len(re.findall(r'\btry\b', text_lower)) * 20 +
               len(re.findall(r'\bstep\b', text_lower)) * 15 +
               len(re.findall(r'\bpress\b', text_lower)) * 10
               )

def comfort_score(text):
    text_lower = text.lower()
    return min(100,
               text_lower.count("you can") * 5 +
               text_lower.count("don't worry") * 10 -
               text_lower.count("warning") * 3
               )

def jargon_penalty(text):
    return sum(5 for word in text.split()
               if word.lower() in TECHNICAL_JARGON)

def uncertainty_penalty(text):
    text_lower = text.lower()
    return sum(10 for phrase in ["might be", "could be", "not sure"]
               if phrase in text_lower)

# Final Composite Score
def calculate_elder_x_score(text):
    readability = readability_score(text)
    simplicity = simplicity_score(text)
    actionability = actionability_score(text)
    comfort = comfort_score(text)
    penalty = jargon_penalty(text) + uncertainty_penalty(text)

    score = (
            0.4 * readability +
            0.3 * simplicity +
            0.2 * actionability +
            0.1 * comfort -
            penalty
    )

    return max(0, min(100, score)), readability, simplicity, actionability, comfort

# Streamlit Display
def show_evaluation(text):
    score, r, s, a, c = calculate_elder_x_score(text)

    st.progress(score / 100)
    st.markdown(f"""
    ### 🧠 ELDER-X Score: `{score}/100`  
    **Interpretation**: {interpret_elder_x(score)}

    **Breakdown**:
    - 📚 **Readability**: `{r:.1f}` / 100
    - ✂️ **Simplicity**: `{s:.1f}` / 100
    - 👆 **Actionability**: `{a:.1f}` / 100
    - 🛋️ **Comfort**: `{c:.1f}` / 100
    """)
