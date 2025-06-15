import streamlit as st
from openai import OpenAI
import re
import random
from difflib import SequenceMatcher

# --- Load API Key ---
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- App Config ---
st.set_page_config(page_title="Infinite Cook", layout="centered")
st.title("Infinity Recipe Game")
st.caption("Start with a base ingredient. Keep building dishes until it won’t work.")
st.markdown("---")

# --- Initialize State ---
if "round" not in st.session_state:
    st.session_state.round = 1
    st.session_state.history = []
    st.session_state.current_base = random.choice([
        "tomato", "chicken", "miso", "egg", "rice", "potato", "spinach", "banana", "lentils", "bread"
    ])
    st.session_state.active = True
    st.session_state.awaiting_next = False
    st.session_state.last_user_inputs = []
    st.session_state.used_ingredients = set()

# --- GPT Judge Function ---
def evaluate_combo_with_gpt(base, additions):
    ingredients = ", ".join([base] + additions)
    prompt = (
        f"You are a cooking judge in a text-based game. The user combined these ingredients and only these ingredients: {ingredients}.\n\n"
        f"Respond only in this format:\n"
        f"Answer: Yes or No\n"
        f"Explanation: [exactly one or two sentences]\n\n"
        f"If 'No', say why it's unpalatable (expand on this with extra sentences as needed, drawing on food science and culinary expertise). If 'Yes', describe a plausible dish. "
        f"No extra text."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        text = response.choices[0].message.content.strip()

        answer_match = re.search(r"(?im)^answer:\s*(yes|no)\s*$", text)
        explanation_match = re.search(r"(?im)^explanation:\s*(.+)$", text, re.DOTALL)

        if answer_match and explanation_match:
            is_viable = answer_match.group(1).strip().lower() == "yes"
            explanation = explanation_match.group(1).strip().strip('"')
            return is_viable, explanation
        else:
            return None, f"❌ Parsing failed. GPT said:\n{text}"

    except Exception as e:
        return None, f"❌ API Error: {e}"

# --- Round Display ---
st.markdown(f"### Round {st.session_state.round}")
st.markdown(f"**Current base ingredient:** `{st.session_state.current_base}`")

# --- Helper for Similarity Check ---
def are_too_similar(words, threshold=0.85):
    for i in range(len(words)):
        for j in range(i+1, len(words)):
            ratio = SequenceMatcher(None, words[i].lower().strip(), words[j].lower().strip()).ratio()
            if ratio >= threshold:
                return True, (words[i], words[j])
    return False, ()

# --- Active Game Logic ---
if st.session_state.active and not st.session_state.awaiting_next:
    num_inputs = st.session_state.round + 1
    with st.form("ingredient_form"):
        input_fields = [
            st.text_input(f"Add Ingredient {i + 1}", key=f"input_{st.session_state.round}_{i}")
            for i in range(num_inputs)
        ]
        submitted = st.form_submit_button("Submit")

    if submitted and all(input_fields):
        base = st.session_state.current_base

        # --- Gather all used ingredients (historical + current base) ---
        used = set(i.lower().strip() for i in st.session_state.used_ingredients)
        used.add(base.lower().strip())

        repeated = [i for i in input_fields if i.lower().strip() in used]
        too_similar, similar_pair = are_too_similar(input_fields)

        if repeated:
            repeated_clean = ", ".join(f"`{r}`" for r in repeated)
            st.warning(f"You’ve already used: {repeated_clean}. Try different ingredients.")

        elif too_similar:
            st.warning(f"Ingredients `{similar_pair[0]}` and `{similar_pair[1]}` are too similar. Try more distinct ideas.")

        else:
            is_viable, feedback = evaluate_combo_with_gpt(base, input_fields)

            if is_viable is not None:
                if is_viable:
                    st.success(feedback)
                    st.session_state.history.append((base, input_fields, "✅", feedback))
                    st.session_state.last_user_inputs = input_fields
                    st.session_state.awaiting_next = True
                    st.session_state.used_ingredients.update(i.lower().strip() for i in input_fields)
                else:
                    st.error("❌ " + feedback)
                    st.session_state.history.append((base, input_fields, "❌", feedback))
                    st.session_state.active = False
            else:
                st.warning(feedback)

# --- Next Round Button ---
if st.session_state.awaiting_next:
    if st.button("Next Round"):
        st.session_state.round += 1
        st.session_state.current_base = random.choice(st.session_state.last_user_inputs)
        st.session_state.awaiting_next = False

# --- Restart Game + Statistics ---
if not st.session_state.active:
    st.subheader("Game Over!")
    total_rounds = len(st.session_state.history)
    all_ingredients = set()
    for _, inputs, _, _ in st.session_state.history:
        all_ingredients.update(inputs)
    st.markdown(f"- **Rounds completed:** {total_rounds}")
    st.markdown(f"- **Total unique ingredients used:** {len(all_ingredients)}")
    st.markdown(f"- **All ingredients:** {', '.join(sorted(all_ingredients))}")

    # --- Ramsay Quote Based on Performance ---
    def gordon_ramsay_quote(score):
        top_quotes = [
            "“Finally, some bloody passion in the kitchen!”",
            "“That’s what I call a proper dish!”",
            "“Congratulations, you cooked your way out of hell’s kitchen!”"
        ]
        average_quotes = [
            "“Not bad, but don’t get cocky, yeah?”",
            "“Decent effort. Still raw in places.”",
            "“You’re not useless, but I wouldn’t eat that.”"
        ]
        poor_quotes = [
            "“This isn’t cooking, it’s a catastrophe!”",
            "“My gran could do better—and she’s dead!”",
            "“Did you season it with disappointment?”"
        ]

        if score >= 8:
            return random.choice(top_quotes)
        elif score >= 5:
            return random.choice(average_quotes)
        else:
            return random.choice(poor_quotes)

    st.markdown(f"**Gordon Ramsay says:** _{gordon_ramsay_quote(total_rounds)}_")

    st.button("Restart Game", on_click=lambda: st.session_state.clear())


# --- Game History ---
st.markdown("---")
st.markdown("### Game History")
for i, (base, ingredients, result, feedback) in enumerate(st.session_state.history):
    ing_list = ", ".join(f"`{ing}`" for ing in ingredients)
    st.markdown(f"**Round {i+1}:** `{base}`, {ing_list} → {result}<br/>{feedback}", unsafe_allow_html=True)
