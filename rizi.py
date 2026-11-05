import os
import json
import uuid
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from google import genai

import auth

MODEL = "gemini-3.8-flash"

PROJECT_DIR = Path(__file__).resolve().parent
ENV_PATH = PROJECT_DIR / ".env"

load_dotenv(ENV_PATH, override=True)

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    try:
        API_KEY = st.secrets["GEMINI_API_KEY"]
    except (KeyError, FileNotFoundError):
        API_KEY = None

st.set_page_config(
    page_title="Rizi.ai",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.session_state.setdefault("page", "home")
st.session_state.setdefault("user", None)


def go(page: str):
    st.session_state.page = page
    st.rerun()

def inject_css():
    css_path = PROJECT_DIR / "theme.css"

    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def hide_sidebar():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def home_page():
    hide_sidebar()

    logo_path = PROJECT_DIR / "assets" / "logo.png"

    if logo_path.exists():
        _, logo_col, _ = st.columns([1, 2, 1])
        with logo_col:
            st.image(str(logo_path), width=500)

    st.markdown(
        '<div class="h1">Rizi</div>',
        unsafe_allow_html=True,
    )

    st.write("")

    _, col1, col2, _ = st.columns([2, 1, 1, 2])

    with col1:
        if st.button(
            "Sign up",
            type="primary",
            use_container_width=True,
            key="home_signup_button",
        ):
            go("signup")

    with col2:
        if st.button(
            "Sign in",
            use_container_width=True,
            key="home_signin_button",
        ):
            go("signin")

    st.markdown(
        """
        <div class="subtle" style="text-align:center;margin-top:1rem">
            Powered by Google Gemini
        </div>
        """,
        unsafe_allow_html=True,
    )

def signin_page():
    hide_sidebar()

    _, mid, _ = st.columns([1, 2, 1])

    with mid:
        st.markdown(
            '<div class="brand">Rizi</div>',
            unsafe_allow_html=True,
        )
        st.title("Sign in")

        with st.form("signin_form"):
            email = st.text_input(
                "Email",
                key="signin_email",
            )
            password = st.text_input(
                "Password",
                type="password",
                key="signin_password",
            )
            submitted = st.form_submit_button(
                "Sign in",
                type="primary",
                use_container_width=True,
                key="signin_submit",
            )

        if submitted:
            user = auth.verify_user(email, password)

            if user:
                st.session_state.user = user
                go("app")
            else:
                st.error("Incorrect email or password.")

        c1, c2 = st.columns(2)

        with c1:
            if st.button(
                "Create an account",
                use_container_width=True,
                key="signin_to_signup_button",
            ):
                go("signup")

        with c2:
            if st.button(
                "← Back",
                use_container_width=True,
                key="signin_back_button",
            ):
                go("home")

def process_signup(name, email, password, confirm_password):
    if not name.strip():
        return False, "Please enter your name."

    if not email.strip():
        return False, "Please enter your email."

    if password != confirm_password:
        return False, "Passwords do not match."

    success, error_message = auth.create_user(
        name,
        email,
        password,
    )

    if not success:
        return False, error_message

    user = auth.verify_user(email, password)

    if not user:
        return False, "Account created. Please sign in."

    st.session_state.user = user
    return True, None

def signup_page():
    hide_sidebar()

    _, mid, _ = st.columns([1, 2, 1])

    with mid:
        st.markdown(
            '<div class="brand">Rizi</div>',
            unsafe_allow_html=True,
        )
        st.title("Create your account")

        with st.form("signup_form"):
            name = st.text_input("Name", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input(
                "Password",
                type="password",
                key="signup_password",
            )
            confirm_password = st.text_input(
                "Confirm password",
                type="password",
                key="signup_confirm_password",
            )

            submitted = st.form_submit_button(
                "Sign up",
                type="primary",
                use_container_width=True,
                key="signup_submit",
            )

        if submitted:
            success, message = process_signup(
                name,
                email,
                password,
                confirm_password,
            )

            if success:
                go("app")

            st.error(message) if message else None

        c1, c2 = st.columns(2)

        with c1:
            if st.button(
                "I already have an account",
                use_container_width=True,
                key="signup_to_signin_button",
            ):
                go("signin")

        with c2:
            if st.button(
                "← Back",
                use_container_width=True,
                key="signup_back_button",
            ):
                go("home")


# ==================================================
# CHAT HELPERS
# ==================================================

def create_gemini_client():
    if not API_KEY:
        return None

    return genai.Client(api_key=API_KEY)


def create_conversation():
    chat = st.session_state.gemini_client.chats.create(model=MODEL)

    return {
        "id": str(uuid.uuid4()),
        "title": "New chat",
        "messages": [],
        "chat": chat,
    }


def get_current_chat():
    for conversation in st.session_state.conversations:
        if conversation["id"] == st.session_state.current_id:
            return conversation

    conversation = create_conversation()
    st.session_state.conversations.insert(0, conversation)
    st.session_state.current_id = conversation["id"]
    return conversation


def start_new_chat():
    conversation = create_conversation()
    st.session_state.conversations.insert(0, conversation)
    st.session_state.current_id = conversation["id"]


def clear_current_chat():
    conversation = get_current_chat()
    conversation["messages"] = []
    conversation["title"] = "New chat"
    conversation["chat"] = st.session_state.gemini_client.chats.create(
        model=MODEL
    )

def sign_out():
    for key in (
        "user",
        "conversations",
        "current_id",
        "gemini_client",
    ):
        st.session_state.pop(key, None)

    st.session_state.page = "home"
    st.rerun()

def render_copy_button(message_text: str, index: int):
    safe_text = json.dumps(message_text).replace("<", "\\u003c")
    component_key = f"copy_response_{index}_{uuid.uuid4().hex}"

    components.html(
        f"""
        <button id="{component_key}"
            style="
                background:#141a16;
                color:#FC0000;
                border:1px solid #FC0000;
                border-radius:7px;
                padding:5px 12px;
                cursor:pointer;
                font-size:12px;
            ">
            Copy response
        </button>
        <span id="{component_key}_status"
            style="color:#FC0000;font-size:12px;margin-left:8px">
        </span>
        <script>
            const btn = document.getElementById("{component_key}");
            const status = document.getElementById("{component_key}_status");
            const text = {safe_text};

            btn.addEventListener("click", async () => {{
                try {{
                    await navigator.clipboard.writeText(text);
                    status.textContent = "Copied!";
                }} catch (err) {{
                    status.textContent = "Clipboard unavailable in this browser.";
                }}
            }});
        </script>
        """,
        height=42,
    )

def chat_page():
    if not API_KEY:
        st.error(
            "GEMINI_API_KEY was not found. Add it to your .env file "
            "or Streamlit secrets."
        )
        st.stop()

    if "gemini_client" not in st.session_state:
        st.session_state.gemini_client = create_gemini_client()

    if "conversations" not in st.session_state:
        first_conversation = create_conversation()
        st.session_state.conversations = [first_conversation]
        st.session_state.current_id = first_conversation["id"]

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
            key="sidebar_new_chat_button",
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

            prefix = "● " if selected else "   "

            if st.button(
                prefix + label,
                key=f"history_{conversation['id']}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state.current_id = conversation["id"]
                st.rerun()

        st.divider()

        if st.button(
            "♲   Clear current chat",
            use_container_width=True,
            key="sidebar_clear_chat_button",
        ):
            clear_current_chat()
            st.rerun()

        st.caption(f"Signed in as {st.session_state.user['name']}")

        if st.button(
            "Sign out",
            use_container_width=True,
            key="sidebar_signout_button",
        ):
            sign_out()

        st.markdown(
            '<div class="subtle">Powered by Google Gemini</div>',
            unsafe_allow_html=True,
        )

    conversation = get_current_chat()

    st.title("How can I help you?")
    st.caption("Ask questions, explore ideas, or work through a problem.")

    for index, message in enumerate(conversation["messages"]):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                render_copy_button(message["content"], index)

    prompt = st.chat_input("Message Gemini...")

    if prompt:
        if not conversation["messages"]:
            title = prompt.strip().replace("\n", " ")
            conversation["title"] = (
                title if len(title) <= 40 else title[:37] + "..."
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
                    st.error(f"Request failed: {error}")

inject_css()

page = st.session_state.page

if page == "app" and not st.session_state.user:
    page = "signin"
    st.session_state.page = "signin"

pages = {
    "home": home_page,
    "signin": signin_page,
    "signup": signup_page,
    "app": chat_page,
}

pages.get(page, home_page)()