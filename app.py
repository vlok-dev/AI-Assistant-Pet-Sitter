import streamlit as st
import requests
import os
import time
from pathlib import Path

st.set_page_config(page_title="🐾 Instructions For Birdies", page_icon="🐾")

st.title("🐥 Instructions For Birdies")
st.caption("A virtual Matt and Lee Anne assistant for anything unsure on for the birdies.")

# ------------------------------------------------------------------
# FREE MODELS (OpenRouter) - cycled automatically if one is busy
# ------------------------------------------------------------------
FREE_MODELS = [
    "minimax/minimax-m3.1-flash:free",
    "xingchen-agi/xing4.0-29b-a4b:free",
    "nvidia/nemotron-3.5-super-vl:free",
    "dots-studio/dots-3-note-preview:free",
    "liquid/lfm-2.5-2.6b:free",
    "nvidia/nemotron-3.5-lightning:free",
    "thinkingmachines/inkling-small:free",
    "poolside/laguna-s-2.1:free",
    "thinkingmachines/inkling:free",
    "poolside/laguna-xs-2.1:free",
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3.5-content-safety:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "google/gemma-4-26b-a4b-it:free",
    "google/gemma-4-31b-it:free",
    "google/lyria-3-pro-preview",
    "google/lyria-3-clip-preview",
    "nvidia/nemotron-3-super-120b-a12b:free",
]

# ------------------------------------------------------------------
# LOAD INSTRUCTIONS FROM trip-instructions.txt
# (the file must sit in the same folder as app.py)
# ------------------------------------------------------------------
INSTRUCTIONS_FILE = Path(__file__).parent / "trip-instructions.txt"

try:
    instructions_text = INSTRUCTIONS_FILE.read_text(encoding="utf-8")
except FileNotFoundError:
    st.error(f"Could not find {INSTRUCTIONS_FILE.name}. Make sure it is in the same folder as app.py.")
    st.stop()

SYSTEM_PROMPT = f"""
You are a helpful assistant for a pet sitter looking after the owners' 2 budgies
("the babies") while the owners are away.
Answer using ONLY the instructions below. If the answer is not there, say you
don't know and suggest contacting the owners. Keep answers clear and practical,
and always stress anything marked as very important (e.g. no soap residue,
washing the pestle, keeping the cage closed). Be very concise when answering. Try and summarize when answering, not a long winded answer so it is quicker to read. Always stay on the side of safety for the budgies and that the owners adore these 2 budgies and they are their life.

--- INSTRUCTIONS ---
{instructions_text}
"""

# ------------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "model_idx" not in st.session_state:
    st.session_state.model_idx = 0

# ------------------------------------------------------------------
# SHOW CHAT HISTORY
# ------------------------------------------------------------------
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------------------------------------------------------
# CHAT INPUT
# ------------------------------------------------------------------
if prompt := st.chat_input("e.g., How do I clean the food bowls? What do I do when it's cold?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        success = False
        tried = []

        api_key = st.secrets.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            st.error("No API key configured. Please ask the owner to add it to app secrets.")
        else:
            for _ in range(len(FREE_MODELS)):
                model = FREE_MODELS[st.session_state.model_idx]
                tried.append(model)

                try:
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    }
                    payload = {
                        "model": model,
                        "messages": st.session_state.messages,
                        "temperature": 0.3,
                        "max_tokens": 800,
                    }
                    r = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=30,
                    )

                    if r.status_code == 200:
                        full_response = r.json()["choices"][0]["message"]["content"]
                        success = True
                        break
                    else:
                        st.session_state.model_idx = (st.session_state.model_idx + 1) % len(FREE_MODELS)
                        time.sleep(1)
                except Exception:
                    st.session_state.model_idx = (st.session_state.model_idx + 1) % len(FREE_MODELS)
                    time.sleep(1)

            if success:
                placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                st.error(f"All free models are busy right now. Tried: {', '.join(tried)}. Please wait a minute and try again.")