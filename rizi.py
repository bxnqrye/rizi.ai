import os
import json
import uuid
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from google import genai

import auth

# ==================================================
# CONFIGURATION
# ==================================================

MODEL = "gemini-3.8-flash"

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path, override=True)

API_KEY = os.getenv("GEMINI_API_KEY")

st.set_page_config(
    page_title="Gemini Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.session_state.setdefault("page", "home")  # home | signin | signup | app
st.session_state.setdefault("user", None)


def go(page: str):
    st.session_state.page = page
    st.rerun()


# ==================================================
# DARK THEME + ACCENTS (your original CSS, unchanged)
# ==================================================

def inject_css():
    css_path = Path(__file__).resolve().parent / "theme.css"
    css = css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def hide_sidebar():
    st.markdown(
        "<style>[data-testid='stSidebar'],"
        "[data-testid='collapsedControl']{display:none}</style>",
        unsafe_allow_html=True,
    )

# ==================================================
# HOME (landing)
# ==================================================

def home_page():
    
    st.markdown(
        '<div class="h1">Jarvis</div>',
        unsafe_allow_html=True,
        )

    st.write("")
    _, col1, col2, _ = st.columns([2, 1, 1, 2])
    if col1.button("Sign up", type="primary", use_container_width=True):
        go("signup")
    if col2.button("Sign in", use_container_width=True):
        go("signin")

    st.markdown(
        '<div class="subtle" style="text-align:center;margin-top:1rem">'
        "Powered by Google Gemini</div>",
        unsafe_allow_html=True,
    )


# ==================================================
# AUTH PAGES
# ==================================================

def signin_page():
    hide_sidebar()
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown(
            '<div class="brand">Jarvis</div>',
            unsafe_allow_html=True,
        )
        st.title("Sign in")
        with st.form("signin_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Sign in", type="primary", use_container_width=True
            )
        if submitted:
            user = auth.verify_user(email, password)
            if user:
                st.session_state.user = user
                go("app")
            else:
                st.error("Incorrect email or password.")

        c1, c2 = st.columns(2)
        if c1.button("Create an account", use_container_width=True):
            go("signup")
        if c2.button("← Back", use_container_width=True):
            go("home")


def signup_page():
    hide_sidebar()
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown(
            '<div class="brand">Jarvis</div>',
            unsafe_allow_html=True,
        )
        st.title("Create your account")
        with st.form("signup_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button(
                "Sign up", type="primary", use_container_width=True
            )
        if submitted:
            if password != confirm:
                st.error("Passwords do not match.")
            else:
                ok, err = auth.create_user(name, email, password)
                if ok:
                    st.session_state.user = auth.verify_user(email, password)
                    go("app")
                else:
                    st.error(err)

        c1, c2 = st.columns(2)
        if c1.button("I already have an account", use_container_width=True):
            go("signin")
        if c2.button("← Back", use_container_width=True):
            go("home")


# ==================================================
# CHAT (your original app)
# ==================================================

def chat_page():
    if not API_KEY:
        st.error(
            "GEMINI_API_KEY was not found. "
            "Check your .env file."
        )
        st.stop()

    # Keep one client per Streamlit browser session.
    if "gemini_client" not in st.session_state:
        st.session_state.gemini_client = genai.Client(api_key=API_KEY)

    client = st.session_state.gemini_client

    # ---------- conversation management ----------

    def create_conversation():
        chat = st.session_state.gemini_client.chats.create(model=MODEL)

        return {
            "id": str(uuid.uuid4()),
            "title": "New chat",
            "messages": [],
            "chat": chat,
        }

    if "conversations" not in st.session_state:
        first_chat = create_conversation()
        st.session_state.conversations = [first_chat]
        st.session_state.current_id = first_chat["id"]

    def get_current_chat():
        for conversation in st.session_state.conversations:
            if conversation["id"] == st.session_state.current_id:
                return conversation

        new_chat = create_conversation()
        st.session_state.conversations.append(new_chat)
        st.session_state.current_id = new_chat["id"]
        return new_chat

    def start_new_chat():
        conversation = create_conversation()
        st.session_state.conversations.insert(0, conversation)
        st.session_state.current_id = conversation["id"]

    def clear_current_chat():
        conversation = get_current_chat()
        conversation["messages"] = []
        conversation["title"] = "New chat"
        conversation["chat"] = (
            st.session_state.gemini_client.chats.create(model=MODEL)
        )

    # ---------- sidebar ----------

    with st.sidebar:
        st.markdown(
            '<div class="brand">Jarvis</div>',
            unsafe_allow_html=True,
        )
        st.caption("Your personal AI assistant")

        if st.button(
            "＋   New chat",
            type="primary",
            use_container_width=True,
        ):
            start_new_chat()
            st.rerun()

        st.divider()

        st.markdown("**Chats**")

        for conversation in st.session_state.conversations:
            selected = (
                conversation["id"] == st.session_state.current_id
            )

            label = conversation["title"]
            if len(label) > 30:
                label = label[:27] + "..."

            prefix = "● " if selected else "  "

            if st.button(
                prefix + label,
                key="history_" + conversation["id"],
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state.current_id = conversation["id"]
                st.rerun()

        st.divider()

        if st.button("♲   Clear current chat", use_container_width=True):
            clear_current_chat()
            st.rerun()

        st.caption(f"Signed in as {st.session_state.user['name']}")
        if st.button("Sign out", use_container_width=True):
            for key in (
                "user", "conversations", "current_id", "gemini_client"
            ):
                st.session_state.pop(key, None)
            go("home")

        st.markdown(
            '<div class="subtle">Powered by Google Gemini</div>',
            unsafe_allow_html=True,
        )

    # ---------- main chat ----------

    conversation = get_current_chat()

    st.title("How can I help you?")
    st.caption("Ask questions, explore ideas, or work through a problem.")

    for index, message in enumerate(conversation["messages"]):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                safe_text = json.dumps(
                    message["content"]
                ).replace("<", "\\u003c")

                components.html(
                    f"""
                    <button id="copy"
                        style="
                            background:#141a16;
                            color:#45f58a;
                            border:1px solid #28372d;
                            border-radius:7px;
                            padding:5px 12px;
                            cursor:pointer;
                            font-size:12px;
                        ">
                        Copy response
                    </button>
                    <span id="status"
                        style="color:#87958b;font-size:12px;margin-left:8px">
                    </span>
                    <script>
                        const btn = document.getElementById("copy");
                        const status = document.getElementById("status");
                        const text = {safe_text};

                        btn.addEventListener("click", async () => {{
                            try {{
                                await navigator.clipboard.writeText(text);
                                status.textContent = "Copied!";
                            }} catch (err) {{
                                status.textContent =
                                    "Clipboard unavailable in this browser.";
                            }}
                        }});
                    </script>
                    """,
                    height=42,
                )

    prompt = st.chat_input("Message Gemini...")

    if prompt:
        if not conversation["messages"]:
            conversation["title"] = prompt.strip().replace("\n", " ")
            if len(conversation["title"]) > 40:
                conversation["title"] = (
                    conversation["title"][:37] + "..."
                )

        conversation["messages"].append({
            "role": "user",
            "content": prompt,
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Gemini is thinking..."):
                try:
                    response = conversation["chat"].send_message(prompt)

                    answer = (
                        response.text
                        or "Gemini returned no text response."
                    )

                    st.markdown(answer)

                    conversation["messages"].append({
                        "role": "assistant",
                        "content": answer,
                    })

                except Exception as error:
                    error_message = str(error)

                    # Recover if the SDK client was closed.
                    if "client has been closed" in error_message.lower():
                        try:
                            new_client = genai.Client(api_key=API_KEY)
                            st.session_state.gemini_client = new_client

                            new_chat = new_client.chats.create(
                                model=MODEL
                            )

                            for old_message in conversation["messages"]:
                                new_chat.send_message(
                                    old_message["content"]
                                )

                            conversation["chat"] = new_chat
                            response = new_chat.send_message(prompt)

                            answer = (
                                response.text
                                or "Gemini returned no text response."
                            )

                            st.markdown(answer)

                            conversation["messages"].append({
                                "role": "assistant",
                                "content": answer,
                            })

                        except Exception as retry_error:
                            st.error(f"Request failed: {retry_error}")
                    else:
                        st.error(f"Request failed: {error}")


# ==================================================
# ROUTER
# ==================================================

inject_css()

page = st.session_state.page

# The chat is only reachable when signed in.
if page == "app" and not st.session_state.user:
    page = "signin"

{
    "home": home_page,
    "signin": signin_page,
    "signup": signup_page,
    "app": chat_page,
}[page]()