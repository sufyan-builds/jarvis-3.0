"""J.A.R.V.I.S. Streamlit interface.

A polished browser front end for Jarvis. It shares the same CommandHandler as
the terminal engine (jarvis.py), so both interfaces behave identically -- only
the input and presentation layers differ.
"""

from __future__ import annotations

import streamlit as st
from streamlit_mic_recorder import speech_to_text

from config import Config
from core.ai import GroqAssistant
from core.command_handler import CommandHandler
from core.speak import TextToSpeech


st.set_page_config(page_title="J.A.R.V.I.S. AI Interface", page_icon="🤖", layout="wide")


@st.cache_resource
def load_modules():
    config = Config()
    tts = TextToSpeech()
    ai = GroqAssistant(
        api_key=config.groq_api_key,
        model_name=config.groq_model,
        max_memory_turns=config.max_memory_turns,
        temperature=config.ai_temperature,
    )
    handler = CommandHandler(tts, ai)
    return config, tts, ai, handler


def get_theme_tokens(theme_mode: str) -> dict[str, str]:
    if theme_mode == "Light":
        return {
            "bg": "#f4f8fc",
            "panel": "rgba(255,255,255,0.82)",
            "panel_border": "rgba(13, 35, 58, 0.10)",
            "text": "#0b1f33",
            "muted": "#4f647a",
            "accent": "#0ea5e9",
            "accent_soft": "rgba(14,165,233,0.12)",
            "user_bg": "linear-gradient(135deg, rgba(14,165,233,0.16), rgba(2,132,199,0.10))",
            "assistant_bg": "linear-gradient(135deg, rgba(255,255,255,0.88), rgba(231,240,249,0.92))",
            "shadow": "0 18px 40px rgba(15, 23, 42, 0.08)",
        }
    return {
        "bg": "#050b14",
        "panel": "rgba(8,14,26,0.72)",
        "panel_border": "rgba(99, 179, 237, 0.16)",
        "text": "#e7f3ff",
        "muted": "#8da7c3",
        "accent": "#2dd4ff",
        "accent_soft": "rgba(45,212,255,0.10)",
        "user_bg": "linear-gradient(135deg, rgba(45,212,255,0.18), rgba(14,165,233,0.10))",
        "assistant_bg": "linear-gradient(135deg, rgba(8,14,26,0.88), rgba(12,20,34,0.90))",
        "shadow": "0 24px 60px rgba(0, 0, 0, 0.35)",
    }


def apply_theme(theme_mode: str) -> None:
    colors = get_theme_tokens(theme_mode)
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(45,212,255,0.10), transparent 32%),
                radial-gradient(circle at bottom right, rgba(14,165,233,0.08), transparent 28%),
                linear-gradient(180deg, {colors['bg']} 0%, {colors['bg']} 100%);
            color: {colors['text']};
            font-family: "Segoe UI Variable", "Segoe UI", "Helvetica Neue", sans-serif;
        }}
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(6, 12, 22, 0.96), rgba(9, 18, 31, 0.92));
            border-right: 1px solid {colors['panel_border']};
        }}
        .jarvis-shell {{
            background: {colors['panel']};
            border: 1px solid {colors['panel_border']};
            box-shadow: {colors['shadow']};
            backdrop-filter: blur(18px);
            border-radius: 24px;
            padding: 1.25rem 1.35rem;
        }}
        .jarvis-hero {{
            display: grid;
            grid-template-columns: 110px 1fr;
            gap: 1rem;
            align-items: center;
            margin-bottom: 1rem;
        }}
        .jarvis-orb {{
            width: 110px;
            height: 110px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(45,212,255,0.88) 0%, rgba(14,165,233,0.34) 48%, rgba(2,6,23,0) 72%);
            box-shadow: 0 0 28px rgba(45,212,255,0.45), inset 0 0 28px rgba(255,255,255,0.12);
            animation: jarvisPulse 2.6s ease-in-out infinite;
        }}
        @keyframes jarvisPulse {{
            0% {{ transform: scale(0.94); opacity: 0.80; }}
            50% {{ transform: scale(1.03); opacity: 1; }}
            100% {{ transform: scale(0.94); opacity: 0.80; }}
        }}
        .jarvis-title {{ font-size: 2.3rem; font-weight: 800; letter-spacing: 0.12em; margin: 0; color: {colors['text']}; }}
        .jarvis-subtitle {{ color: {colors['muted']}; margin-top: 0.15rem; margin-bottom: 0; font-size: 0.98rem; }}
        .status-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.75rem; margin: 1rem 0 1.2rem; }}
        .status-card {{
            background: {colors['panel']};
            border: 1px solid {colors['panel_border']};
            border-radius: 18px;
            padding: 0.95rem 1rem;
            box-shadow: {colors['shadow']};
        }}
        .status-label {{ color: {colors['muted']}; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.16em; margin-bottom: 0.25rem; }}
        .status-value {{ color: {colors['text']}; font-size: 0.98rem; font-weight: 600; }}
        div[data-testid="stChatMessage"] {{
            border: 1px solid {colors['panel_border']};
            border-radius: 18px;
            background: {colors['assistant_bg']};
            box-shadow: {colors['shadow']};
            padding: 0.25rem 0.35rem;
            margin-bottom: 0.7rem;
        }}
        div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {{
            color: {colors['text']};
            line-height: 1.55;
        }}
        div[data-testid="stChatMessage"] .st-emotion-cache-janbn0 {{ color: {colors['muted']}; }}
        button[kind="secondary"] {{
            border-radius: 999px !important;
            border: 1px solid {colors['panel_border']} !important;
            background: {colors['accent_soft']} !important;
            color: {colors['text']} !important;
        }}
        .stChatInput input {{
            border-radius: 18px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


config, tts_engine, ai_model, command_handler = load_modules()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark"

with st.sidebar:
    st.markdown("### J.A.R.V.I.S. Controls")
    st.session_state.theme_mode = st.radio("Theme", ["Dark", "Light"], index=0 if st.session_state.theme_mode == "Dark" else 1)
    st.caption("Theme choice stays in this session for a consistent look.")
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("**System status**")
    st.write(f"AI: {'Online' if ai_model.is_available else 'Unavailable'}")
    st.write(f"Voice: {'Ready' if tts_engine.engine is not None else 'Unavailable'}")
    st.write(f"Model: {config.groq_model}")


apply_theme(st.session_state.theme_mode)
theme_colors = get_theme_tokens(st.session_state.theme_mode)

st.markdown(
    f"""
    <div class="jarvis-shell">
      <div class="jarvis-hero">
        <div class="jarvis-orb"></div>
        <div>
          <h1 class="jarvis-title">J.A.R.V.I.S.</h1>
          <p class="jarvis-subtitle">A polished desktop assistant for voice, chat, and Windows automation.</p>
        </div>
      </div>
      <div class="status-grid">
        <div class="status-card"><div class="status-label">AI Core</div><div class="status-value">{'Groq online' if ai_model.is_available else 'Groq unavailable'}</div></div>
        <div class="status-card"><div class="status-label">Speech</div><div class="status-value">{'Voice ready' if tts_engine.engine is not None else 'Voice unavailable'}</div></div>
        <div class="status-card"><div class="status-label">Theme</div><div class="status-value">{st.session_state.theme_mode} mode</div></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


def process_command(text: str) -> None:
    st.session_state.messages.append({"role": "user", "content": text})
    with st.spinner("Jarvis is thinking..."):
        try:
            response_text = command_handler.handle_command(text)
        except Exception as exc:
            response_text = f"Sorry, I ran into an unexpected problem: {exc}"

    if response_text is None:
        response_text = "Goodbye, sir."

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    tts_engine.speak_async(response_text)


st.markdown("#### Voice input")
captured_text = speech_to_text(
    language="en",
    start_prompt="Activate microphone",
    stop_prompt="Listening...",
    just_once=True,
    use_container_width=True,
    key=f"speech_input_{st.session_state.theme_mode.lower()}",
)

if captured_text:
    process_command(captured_text)

st.markdown("#### Conversation")
if st.session_state.messages:
    for message in st.session_state.messages:
        role = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(message["content"])
else:
    st.info("Say something or type a command to start the conversation.")


typed_command = st.chat_input("Type a command or ask Jarvis a question...")
if typed_command:
    process_command(typed_command)
    st.rerun()
