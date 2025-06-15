import streamlit as st
from openai import OpenAI
import random

# Load OpenAI API key
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

st.set_page_config(page_title="Infinity Recipe Game", layout="centered")
st.title("🥄 Infinity Recipe Game")

if "round" not in st.session_state:
    st.session_state.round = 1
    st.session_state.history = []
    st.session_state.current_base = random.choice([
        "tomato", "chicken", "miso", "egg", "rice", "potato", "spinach", "banana", "lentils", "bread"
    ])
    st.session_state.active = True

# GPT-based evaluation function
def evaluate_combo_with_gpt(base, additions):
    combo = f"{base}, {additions[0]}, and {additions[1]}"
    prompt = (
        f"You are a culinary expert judging an ingredient game. The player has combined {combo}.\n"
        f"1. Does this combination work in a real, plausible dish? Answer 'Yes' or 'No'.\n"
        f"2. If 'Yes', describe a dish that could use these ingredients in 1–2 sentences.\n"
        f"3. If 'No', explain briefly why the combination doesn't work and say 'Game Over'."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

# Round UI
st.markdown(f"### Round {st.session_state.round}")
st.markdown(f"**Base ingredient:** `{st.session_state.current_base}`")

if st.session_state.active:
    with st.form("ingredient_form"):
        ing1 = st.text_input("Ingredient 1")
        ing2 = st.text_input("Ingredient 2")
        submitted = st.form_submit_button("Submit")

    if submitted and ing1 and ing2:
        base = st.session_state.current_base
        response = evaluate_combo_with_gpt(base, [ing1, ing2])

        if response.lower().startswith("yes"):
            st.success(response)
            st.session_state.history.append((base, ing1, ing2, "✅", response))
            st.session_state.round += 1
            st.session_state.current_base = random.choice([ing1, ing2])
        elif response.lower().startswith("no") or "game over" in response.lower():
            st.error(response)
            st.session_state.history.append((base, ing1, ing2, "❌", response))
            st.session_state.active = False
        else:
            st.warning("GPT gave an unexpected response. Try again.")
else:
    st.button("Restart Game", on_click=lambda: st.session_state.clear())

# History
st.markdown("---")
st.markdown("### Game History")
for i, (b, i1, i2, result, feedback) in enumerate(st.session_state.history):
    st.markdown(f"**Round {i+1}:** `{b}`, `{i1}`, `{i2}` → {result} — {feedback}")
