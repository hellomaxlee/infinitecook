import streamlit as st
import random
import openai

st.set_page_config(page_title="Infinity Recipe Game", layout="centered")
st.title("🥄 Infinity Recipe Game")

openai.api_key = st.secrets["OPENAI_API_KEY"]

if "round" not in st.session_state:
    st.session_state.round = 1
    st.session_state.history = []
    st.session_state.current_base = random.choice([
        "tomato", "chicken", "miso", "egg", "rice", "potato", "spinach", "banana", "lentils", "bread"
    ])
    st.session_state.active = True

def evaluate_combo_with_gpt(base, additions):
    combo = f"{base}, {additions[0]}, and {additions[1]}"
    prompt = (
        f"You're a culinary expert. A player in a game has proposed combining {combo}.\n"
        f"1. Is this combination likely to work well in a dish? Answer 'Yes' or 'No'.\n"
        f"2. If 'Yes', describe a plausible dish that could be made using these ingredients in 1–2 sentences.\n"
        f"3. If 'No', explain briefly why it wouldn't work and say 'Game Over'."
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()

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
        elif response.lower().startswith("no"):
            st.error(response)
            st.session_state.history.append((base, ing1, ing2, "❌", response))
            st.session_state.active = False
else:
    st.button("Restart Game", on_click=lambda: st.session_state.clear())

st.markdown("---")
st.markdown("### Game History")
for i, (b, i1, i2, result, feedback) in enumerate(st.session_state.history):
    st.markdown(f"**Round {i+1}:** `{b}`, `{i1}`, `{i2}` → {result} — {feedback}")
