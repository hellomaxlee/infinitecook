import streamlit as st
from openai import OpenAI
import re
import random

# --- Load OpenAI API key ---
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- App Setup ---
st.set_page_config(page_title="Infinity Recipe Game", layout="centered")
st.title("🥄 Infinity Recipe Game")
st.caption("Each round, you add more ingredients to a new base. GPT judges if it works.")

# --- Debug toggle ---
DEBUG = st.checkbox("Show raw GPT response")

# --- Initialize Session State ---
if "round" not in st.session_state:
    st.session_state.round = 1
    st.session_state.history = []
    st.session_state.current_base = random.choice([
        "tomato", "chicken", "miso", "egg", "rice", "potato", "spinach", "banana", "lentils", "bread"
    ])
    st.session_state.active = True
    st.session_state.last_user_inputs = []

# --- GPT Evaluation Function ---
def evaluate_combo_with_gpt(base, additions):
    ingredient_list = ", ".join([base] + additions)
    prompt = (
        f"You are a cooking judge in a text-based game. The user combined these ingredients: {ingredient_list}.\n\n"
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

        # --- Robust parsing ---
        answer_match = re.search(r"(?im)^answer:\s*(yes|no)\s*$", text)
        explanation_match = re.search(r"(?im)^explanation:\s*(.+)$", text, re.DOTALL)

        if answer_match and explanation_match:
            is_viable = answer_match.group(1).strip().lower() == "yes"
            explanation = explanation_match.group(1).strip().strip('\"')
            return is_viable, explanation
        else:
            return None, f"❌ Parsing failed. GPT said:\n{text}"

    except Exception as e:
        return None, f"❌ API Error: {e}"

# --- Round Header and Base Ingredient Display ---
st.markdown(f"### Round {st.session_state.round}")
st.markdown(f"**Current base ingredient:** `{st.session_state.current_base}`")

# --- Ingredient Form ---
if st.session_state.active:
    num_inputs = st.session_state.round + 1  # 2 in Round 1, 3 in Round 2, etc.

    with st.form("ingredient_form"):
        input_fields = []
        for i in range(num_inputs):
            field = st.text_input(f"Add Ingredient {i+1}", key=f"input_{st.session_state.round}_{i}")
            input_fields.append(field)

        submitted = st.form_submit_button("Submit")

    if submitted and all(input_fields):
        base = st.session_state.current_base
        is_viable, feedback = evaluate_combo_with_gpt(base, input_fields)

        if is_viable is not None:
            if is_viable:
                st.success(feedback)
                st.session_state.history.append((base, input_fields, "✅", feedback))
                st.session_state.round += 1
                st.session_state.last_user_inputs = input_fields
                st.session_state.current_base = random.choice(input_fields)
            else:
                st.error("❌ " + feedback)
                st.session_state.history.append((base, input_fields, "❌", feedback))
                st.session_state.active = False
        else:
            st.warning(feedback)

else:
    st.button("Restart Game", on_click=lambda: st.session_state.clear())

# --- Game History ---
st.markdown("---")
st.markdown("### Game History")
for i, (base, ingredients, result, feedback) in enumerate(st.session_state.history):
    ing_list = ", ".join(f"`{ing}`" for ing in ingredients)
    st.markdown(f"**Round {i+1}:** `{base}`, {ing_list} → {result}<br/>{feedback}", unsafe_allow_html=True)
