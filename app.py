import streamlit as st
import requests
import os
import time

st.set_page_config(page_title="🐾 Instructions For Birdies", page_icon="🐾")

st.title("🐾 Instructions For Birdies")
st.caption("Ask anything about instructions and it will tell you.")

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
# EDIT YOUR PET INSTRUCTIONS BELOW
# ------------------------------------------------------------------
PET_INSTRUCTIONS = """
You are a helpful assistant for a pet sitter staying in the owner's home.
Answer using ONLY the information below. If the answer is not here, say you 
don't know and suggest contacting the owner.

--- PETS ---
Max: Dog, 5 years, Labrador mix. Friendly, food-motivated, pulls on leash.
Bella: Cat, 3 years. Shy at first, hides under the bed.

--- FEEDING ---
Max: 1.5 cups dry kibble at 8:00 AM and 6:00 PM. Refill water bowl twice daily.
Bella: 1/2 cup wet food at 8:00 AM and 8:00 PM. Dry food available all day.
Treats: Max gets 2 small treats after walks. No table scraps.

--- WALKING / PLAY ---
Max: Two walks daily (7:00 AM and 5:30 PM), 20–30 minutes. Use blue leash.
Bella: Feather wand play around 9:00 PM.

--- MEDICATIONS ---
Max: One joint supplement chew with dinner.
Bella: None.

--- HOUSE RULES ---
- Do not let Bella outside.
- Max is allowed on the couch but not on the bed.
- Take out trash on Tuesday and Friday nights.
- Wi-Fi: HomeWiFi_5G, password: PetSitter2026!

--- EMERGENCY CONTACTS ---
Owner: +1 (555) 123-4567
Backup: Mrs. Chen, +1 (555) 987-6543 (spare key under front flower pot)
Vet: Happy Paws Clinic, +1 (555) 222-3344, 123 Main St.
Emergency vet: City Animal ER, +1 (555) 333-9999 (open 24 hrs)

--- OTHER ---
Collect mail daily and stack on hallway table. Water the living-room fern every 3 days.
"""

# ------------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": PET_INSTRUCTIONS}]
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
if prompt := st.chat_input("e.g., When does Max eat? Where is the vet?"):
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