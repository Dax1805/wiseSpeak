import os
from dotenv import load_dotenv
from openai import OpenAI
import re

# ---------- Load API Key ----------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------- Cascading Style Instructions ----------
STYLE_INSTRUCTIONS = {
    "short": "Start with a short summary.",
    "simplify": "Then, explain it again using plain, friendly language with no jargon.",
    "step-by-step": "Finally, break it down step-by-step like a set of instructions."
}


# ---------- Prompt Builder ----------
def build_prompt(user_name, query, styles, hobby):
    if isinstance(styles, str):
        styles = [styles.lower()]
    else:
        styles = [s.lower() for s in styles]

    if styles == ["short"]:
        return None

    combined_instruction = " ".join(STYLE_INSTRUCTIONS.get(s, "") for s in styles).strip()
    if not combined_instruction:
        combined_instruction = "Explain clearly and simply."

    metaphor = f"Use an analogy from {hobby.lower()} if helpful." if hobby and hobby.lower() != "none" else ""

    return (
        f"The user named {user_name} asked: '{query}'. "
        f"{combined_instruction} {metaphor} Avoid technical jargon."
    )

def add_confidence_cue(response: str) -> str:
    # Token and structure stats
    word_count = len(response.split())
    sentence_count = response.count(".")
    avg_sentence_length = word_count / sentence_count if sentence_count else word_count

    # Heuristics
    factual_phrases = ["you should", "to fix this", "this will", "follow these steps", "make sure to"]
    factual_hits = sum(phrase in response.lower() for phrase in factual_phrases)
    vague_phrases = ["maybe", "might", "possibly", "i think", "could be", "not sure", "try to"]
    vague_hits = sum(phrase in response.lower() for phrase in vague_phrases)

    exclamations = response.count("!")
    imperative_verbs = len(re.findall(r"\b(try|tap|press|close|check|restart|go to|click|open|delete)\b", response.lower()))

    # Confidence base score
    score = 80  # Start optimistically

    # Penalize/reward phrasing
    score += min(factual_hits * 3, 6)
    score -= vague_hits * 5

    # Penalize too many exclamations
    score -= min(exclamations * 3, 10)

    # Reward clear instructional tone
    score += min(imperative_verbs * 2, 10)

    # Penalize excessive or too short response
    if word_count < 15:
        score -= 10
    elif word_count > 200:
        score -= 5

    # Clamp score
    score = max(50, min(score, 95))

    # Confidence message
    if score >= 88:
        cue = "📊 I'm highly confident this will help."
    elif score >= 72:
        cue = "📊 This should help in most situations."
    elif score >= 60:
        cue = "📊 This may help, but ask someone if unsure."
    else:
        cue = "📊 This might not be very reliable — double-check or ask for help."

    return f"{response.strip()}\n\n{cue} (How sure I am: {score}%)"


# ---------- Main Explanation Generator ----------
def get_explanation(user_name, query, styles, hobby):
    if not query:
        return "Please enter a question."

    if isinstance(styles, str):
        styles = [styles.lower()]
    else:
        styles = [s.lower() for s in styles]

    # 🔹 Short mode: Refined GPT-4 summarization for all users
    if styles == ["short"]:
        print("🧠 [Short mode] Using GPT-4 with refined structure.")

        def is_valid_answer(query, answer):
            bad_signals = [
                "i'm not sure", "i cannot help", "this may not be accurate",
                "as an ai language model", "i don't have enough information"
            ]
            return not any(phrase in answer.lower() for phrase in bad_signals)

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant. Respond in 1–2 sentences only. Avoid greetings, empathy, or metaphors. "
                            "Focus on the most likely causes and simplest solutions. "
                            "If more details are needed, say so clearly. "
                            "Format: [Cause(s)]. [Solution(s)]."
                        )
                    },
                    {"role": "user", "content": query}
                ],
                temperature=0.2,
                max_tokens=150
            )

            short_answer = response.choices[0].message.content.strip()
            print("🧠 GPT Short Answer (pre-validation):", short_answer)

            if is_valid_answer(query, short_answer):
                return add_confidence_cue(short_answer)
            else:
                return "I need more details to help. Could you specify what exactly you're referring to?"

        except Exception as e:
            error_msg = f"⚠️ Technical issue: {str(e)}"
            if "rate limit" in str(e).lower():
                error_msg += "\nPlease wait a moment and try again."
            return error_msg

    # 🔹 Short + Simplify Combo
    if set(styles) == {"short", "simplify"}:
        print("🧠 [Short + Simplify] Rewriting short answer with calm tone (tight control on metaphors).")

        try:
            # Step 1: Get short summary
            short_summary = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant. Respond in 1–2 sentences only. "
                            "Avoid greetings, empathy, or metaphors. "
                            "Focus on the most likely causes and simplest solutions."
                        )
                    },
                    {"role": "user", "content": query}
                ],
                temperature=0.2,
                max_tokens=150
            ).choices[0].message.content.strip()

            print("🔹 Short summary for simplify:", short_summary)

            # Step 2: Rephrase calmly — with *tight metaphor constraints*
            hobby_clause = (
                f"Use at most one short metaphor related to {hobby.lower()} if it makes the explanation easier to understand."
                if hobby and hobby.lower() != "none"
                else "Avoid metaphors unless one clearly improves clarity. Use only one if used."
            )

            simplified_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a simplifier assistant for elderly and non-technical users. "
                            "Your job is to rephrase explanations in calm, plain, easy-to-understand language. "
                            "Use short, simple sentences. "
                            "Avoid creativity or storytelling. "
                            f"{hobby_clause} Do not add new information or more than one metaphor."
                        )
                    },
                    {"role": "user", "content": short_summary}
                ],
                temperature=0.3,
                max_tokens=400
            )

            simplified_text = simplified_response.choices[0].message.content.strip()
            return add_confidence_cue(simplified_text)

        except Exception as e:
            return f"⚠️ Error during short+simplify pipeline: {str(e)}"

    # 🔹 Simplify Only
    if styles == ["simplify"]:
        print("🧠 [Simplify only] Rewriting full query in friendly plain language.")

        try:
            hobby_clause = f"If helpful, use one metaphor from {hobby.lower()}." if hobby and hobby.lower() != "none" else \
                "Use one metaphor if it helps. Avoid jargon."

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a simplifier assistant for older and non-technical users. "
                            "Rewrite the following explanation using calm, friendly, plain language. "
                            "Keep it easy to understand. "
                            f"{hobby_clause}"
                        )
                    },
                    {"role": "user", "content": query}
                ],
                temperature=0.5,
                max_tokens=400
            )

            simplified_text = response.choices[0].message.content.strip()
            return add_confidence_cue(simplified_text)


        except Exception as e:
            return f"⚠️ Error during simplification: {str(e)}"

    # 🔹 Step by step Only
    if styles == ["step-by-step"]:
        print("🧠 [Step-by-step mode] Generating ultra-clear instructions.")

        try:
            # Pre-process query to focus the model on physical interaction
            processed_query = (
                f"Break this down for a first-time user: {query}. "
                "Assume they need to see every single button press."
            )

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You create ultra-clear guides for elderly users. Follow these rules:\n\n"
                            "1. 👣 Step Format: [Action] → [Location] → [Visual cue]\n"
                            "   Example: 'Tap the HOME button → bottom center → looks like a circle'\n\n"
                            "2. 🧠 Why (Optional): Add only if needed.\n"
                            "   Format: 'Why: [Explain briefly]'\n\n"
                            "3. ⚠️ WARNING (Optional): If a step is risky.\n"
                            "   Format: '⚠️ WARNING: [Caution]'\n\n"
                            "4. ✅ Guidelines:\n"
                            "- Max 6 steps\n"
                            "- Max 10 words per step\n"
                            "- Use plain English\n"
                            "- Use physical cues ('top right', 'blue button')\n"
                            "- No metaphors, no jokes, no nested steps"
                        )
                    },
                    {"role": "user", "content": processed_query}
                ],
                temperature=0.4,
                max_tokens=600
            )

            simplified_text = response.choices[0].message.content.strip()
            return add_confidence_cue(simplified_text)

        except Exception as e:
            return f"⚠️ Error in step-by-step mode: {str(e)}"

    # 🔹 Simplify + Step-by-Step Combo
    if set(styles) == {"simplify", "step-by-step"}:
        print("🧠 [Simplify + Step-by-Step] Providing plain intro + detailed instructions.")

        try:
            # Step 1: Generate Simplified Overview
            hobby_clause = f"If helpful, use one metaphor related to {hobby.lower()}." \
                if hobby and hobby.lower() != "none" else "Use at most one metaphor if it helps."

            simplified_part = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a friendly assistant explaining things to elderly or non-technical users. "
                            "Use plain language, calm tone, no jargon. "
                            f"{hobby_clause} Be brief but helpful."
                        )
                    },
                    {"role": "user", "content": query}
                ],
                temperature=0.5,
                max_tokens=300
            ).choices[0].message.content.strip()

            # Step 2: Generate Step-by-Step Instructions
            stepwise_part = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You create ultra-clear guides for elderly users. Follow these rules:\n\n"
                            "1. 👣 Step Format: [Action] → [Location] → [Visual cue]\n"
                            "   Example: 'Tap the HOME button → bottom center → looks like a circle'\n\n"
                            "2. 🧠 Why (Optional): Add only if needed.\n"
                            "3. ⚠️ WARNING (Optional): If a step is risky.\n"
                            "4. ✅ Guidelines:\n"
                            "- Max 6 steps\n"
                            "- Max 10 words per step\n"
                            "- Use plain English, no jokes/metaphors\n"
                            "- Use physical cues ('top right', 'blue button')"
                        )
                    },
                    {"role": "user", "content": f"Break this down for a first-time user: {query}"}
                ],
                temperature=0.4,
                max_tokens=400
            ).choices[0].message.content.strip()

            simplified_text = f"\n{simplified_part}\n\n👣 **Step-by-Step Instructions**:\n{stepwise_part}"
            return add_confidence_cue(simplified_text)

        except Exception as e:
            return f"⚠️ Error during simplify + step-by-step pipeline: {str(e)}"

    # 🔹 Short + Step-by-Step Combo
    if set(styles) == {"short", "step-by-step"}:
        print("🧠 [Short + Step-by-Step] Summary + tactile steps")

        try:
            # Step 1: Get Short Answer
            short_summary = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant. Respond in 1–2 sentences only. "
                            "Avoid greetings, empathy, or metaphors. "
                            "Focus on the most likely causes and simplest solutions."
                        )
                    },
                    {"role": "user", "content": query}
                ],
                temperature=0.2,
                max_tokens=150
            ).choices[0].message.content.strip()

            print("🔹 Short summary:", short_summary)

            # Step 2: Generate Step-by-Step Instructions
            stepwise_part = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You create ultra-clear guides for elderly users. Follow these rules:\n\n"
                            "1. 👣 Step Format: [Action] → [Location] → [Visual cue]\n"
                            "   Example: 'Tap the HOME button → bottom center → looks like a circle'\n\n"
                            "2. 🧠 Why (Optional): Add only if needed.\n"
                            "3. ⚠️ WARNING (Optional): If a step is risky.\n"
                            "4. ✅ Guidelines:\n"
                            "- Max 6 steps\n"
                            "- Max 10 words per step\n"
                            "- Use plain English, no jokes/metaphors\n"
                            "- Use physical cues ('top right', 'blue button')"
                        )
                    },
                    {"role": "user", "content": f"Break this down for a first-time user: {query}"}
                ],
                temperature=0.4,
                max_tokens=400
            ).choices[0].message.content.strip()

            simplified_text = f"\n{short_summary}\n\n👣 **Step-by-Step Instructions**:\n{stepwise_part}"
            return add_confidence_cue(simplified_text)

        except Exception as e:
            return f"⚠️ Error during short + step-by-step pipeline: {str(e)}"

    # 🔹 Short + Simplify + Step-by-Step Combo
    if set(styles) == {"short", "simplify", "step-by-step"}:
        print("🧠 [Short + Simplify + Step-by-Step] Unified response with tone layering.")

        try:
            # Step 1: Generate Short Answer
            short_summary = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant. Respond in 1–2 sentences only. "
                            "Avoid greetings, empathy, or metaphors. "
                            "Focus on the most likely causes and simplest solutions."
                        )
                    },
                    {"role": "user", "content": query}
                ],
                temperature=0.2,
                max_tokens=150
            ).choices[0].message.content.strip()

            print("🔹 Short summary:", short_summary)

            # Step 2: Simplify It Briefly
            hobby_clause = (
                f"Use one metaphor from {hobby.lower()} if clearly helpful."
                if hobby and hobby.lower() != "none"
                else "Use at most one short metaphor if it helps clarity."
            )

            simplified_summary = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a simplifier for elderly users. Rephrase the explanation in plain, friendly language. "
                            "Keep it 2–3 sentences max. Avoid jargon. "
                            f"{hobby_clause}"
                        )
                    },
                    {"role": "user", "content": short_summary}
                ],
                temperature=0.4,
                max_tokens=250
            ).choices[0].message.content.strip()

            # Step 3: Step-by-Step Instructions
            stepwise_part = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You create ultra-clear guides for elderly users. Follow these rules:\n\n"
                            "1. 👣 Step Format: [Action] → [Location] → [Visual cue]\n"
                            "   Example: 'Tap the HOME button → bottom center → looks like a circle'\n\n"
                            "2. 🧠 Why (Optional): Add only if needed.\n"
                            "3. ⚠️ WARNING (Optional): If a step is risky.\n"
                            "4. ✅ Guidelines:\n"
                            "- Max 6 steps\n"
                            "- Max 10 words per step\n"
                            "- Use plain English\n"
                            "- Use physical cues ('top right', 'blue button')\n"
                            "- No metaphors or jokes"
                        )
                    },
                    {"role": "user", "content": f"Break this down for a first-time user: {query}"}
                ],
                temperature=0.4,
                max_tokens=400
            ).choices[0].message.content.strip()

            simplified_text = f"{simplified_summary}\n\n👣 **Step-by-Step Instructions**:\n{stepwise_part}"
            return add_confidence_cue(simplified_text)

        except Exception as e:
            return f"⚠️ Error during short + simplify + step-by-step pipeline: {str(e)}"

    # 🔁 Else: use GPT-4 for other styles
    full_prompt = build_prompt(user_name, query, styles, hobby)
    print("📋 GPT Prompt:", full_prompt)

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant that explains things clearly for older and non-technical users."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )

        simplified_text = response.choices[0].message.content.strip()
        return add_confidence_cue(simplified_text)

    except Exception as e:
        return f"Error: {str(e)}"
