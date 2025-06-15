import streamlit as st
from openai import OpenAI
import re
import random

# --- Load OpenAI API key ---
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- App Setup ---
st.set_page_config(page_title="Infinity Recipe Game", layout="centered")
st.title("🥄 Infinity Recipe Game")
st.caption("Start with a base ingredient. Keep building dishes until GPT says it won't work.")

# --- Debug Mode ---
DEBUG = st.checkbox("Show raw GPT response")

# --- Initialize Session State ---
if "round" not in st.session_state:
    st.session_state.round = 1
    st.session_state.history = []
    st.session_state.current_base = random.choice([
        "tomato", "chicken", "miso", "egg", "rice", "potato", "spinach", "banana", "lentils", "bread"
    ])
    st.session_state.active = True

# --- Function to Evaluate Combo via GPT ---
def evaluate_combo_with_gpt(base, additions):
    combo = f"{base}, {additions[0]}, and {additions[1]}"
    prompt = (
        f"You are a cooking judge in a text-based game. The user combined these three ingredients: {combo}.\n\n"
        f"Respond only in this strict format — no extra words:\n"
        f"Answer: Yes or No\n"
        f"Explanation: [exactly one or two sentences]\n\n"
        f"If you say 'No', your explanation must say why the combination is unpalatable or doesn't work in a real dish.\n"
        f"If you say 'Yes', explain how these ingredients could work in a plausible dish.\n\n"
        f"Only reply in this format. Do not include any commentary, greetings, or summaries."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        text = response.choices[0].message.content.strip()

        if DEBUG:
            st.markdown("#### Raw GPT Response")
            st.code(text)

        answer_match = re.search(r"(?i)^answer:\s*(yes|no)", text)
        explanation_match = re.search(r"(?i)^explanation:\s*(.+)", text, re.DOTALL)

        if answer_match and explanation_match:
            is_viable = answer_match.group(1).strip().lower() == "yes"
            explanation = explanation_match.group(1).strip().strip('\"')
            return is_viable, explanation
        else:
            return None, f"Unexpected format:\n{text}"

    except Exception as e:
        return None, f"Error: {e}"

# --- Editable Base Ingredient ---
st.markdown(f"### Round {st.session_state.round}")
st.text_input("Current base ingredient", key="current_base", disabled=not st.session_state.active)

# --- Input Form ---
if st.session_state.active:
    with st.form("ingredient_form"):
        ing1 = st.text_input("Add Ingredient 1")
        ing2 = st.text_input("Add Ingredient 2")
        submitted = st.form_submit_button("Submit")

    if submitted and ing1 and ing2:
        base = st.session_state.current_base
        is_viable, feedback = evaluate_combo_with_gpt(base, [ing1, ing2])

        if is_viable is True:
            st.success(feedback)
            st.session_state.history.append((base, ing1, ing2, "✅", feedback))
            st.session_state.round += 1
            st.session_state.current_base = random.choice([ing1, ing2])
        elif is_viable is False:
            st.error("❌ " + feedback)
            st.session_state.history.append((base, ing1, ing2, "❌", feedback))
            st.session_state.active = False
        else:
            st.warning("⚠️ GPT gave an unexpected response. Try again.")
else:
    st.button("Restart Game", on_click=lambda: st.session_state.clear())

# --- History ---
st.markdown("---")
st.markdown("### Game History")
for i, (b, i1, i2, result, feedback) in enumerate(st.session_state.history):
    st.markdown(f"**Round {i+1}:** `{b}`, `{i1}`, `{i2}` → {result}<br/>{feedback}", unsafe_allow_html=True)
