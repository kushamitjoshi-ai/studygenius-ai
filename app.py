import streamlit as st
import google.generativeai as genai
import time
from PIL import Image
import streamlit.components.v1 as components
from streamlit_mic_recorder import speech_to_text
from gtts import gTTS
import io
import json
import os
import random

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="StudyGenius AI", page_icon="🎓", layout="wide")

# =========================================================================
# ⚙️ INITIALIZE ALL SESSION STATES FIRST (Crash Prevention)
# =========================================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "is_guest" not in st.session_state:
    st.session_state.is_guest = False
if "reset_step" not in st.session_state:
    st.session_state.reset_step = 1
if "generated_code" not in st.session_state:
    st.session_state.generated_code = None
if "target_username" not in st.session_state:
    st.session_state.target_username = None

# API Key Secrets Pull
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key missing! Please configure GEMINI_API_KEY in Streamlit Secrets.")

# =========================================================================
# 💾 PERSISTENT LOCAL DATABASE LOGIC
# =========================================================================
DB_FILE = "users_db.json"

def load_users():
    default_records = {
        "kushagra joshi": {"password": "Amidhi#11", "name": "Kushagra Joshi", "email": "kushagra@example.com"},
        "kushagra": {"password": "123", "name": "Kushagra Joshi", "email": "kushagra@example.com"},
        "student2": {"password": "456", "name": "Classmate", "email": "friend@example.com"}
    }
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                saved_data = json.load(f)
                for k, v in default_records.items():
                    if k not in saved_data:
                        saved_data[k] = v
                return saved_data
        except:
            return default_records
    return default_records

def save_user(username, password, name, email):
    users = load_users()
    users[username.lower().strip()] = {"password": password, "name": name, "email": email}
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=4)

# =========================================================================
# 🔐 GATEWAY SYSTEM: SIGN UP, LOGIN, GUEST & FORGOT PASSWORD
# =========================================================================
if not st.session_state.logged_in and not st.session_state.is_guest:
    st.title("🎓 Welcome to StudyGenius Portal")
    
    auth_action = st.radio(
        "Select Access Type:", 
        ["Login to Existing Account", "Create New Account (Sign Up)", "Continue as Guest 👤", "Forgot Password 🔑"], 
        horizontal=True
    )
    
    users_db = load_users()

    if auth_action == "Continue as Guest 👤":
        st.subheader("👤 Guest Sandbox Access")
        st.info("You can use the AI freely in Guest mode, but history won't be saved permanently.")
        if st.button("Enter AI Dashboard as Guest 🚀"):
            st.session_state.is_guest = True
            st.session_state.logged_in = False
            st.session_state.current_user = "guest_user"
            st.rerun()

    elif auth_action == "Create New Account (Sign Up)":
        st.subheader("✨ Register New Student Account")
        with st.form("signup_form"):
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email Address")
            new_username = st.text_input("Choose Username").lower().strip()
            new_password = st.text_input("Set Password", type="password")
            signup_submit = st.form_submit_button("Sign Up & Register")
            
            if signup_submit:
                if not new_username or not new_password or not new_name or not new_email:
                    st.error("All fields are required!")
                elif new_username in users_db:
                    st.error("Username already taken! Try another one.")
                else:
                    save_user(new_username, new_password, new_name, new_email)
                    st.success("Account created successfully! Shift to 'Login to Existing Account' above.")
                    
    elif auth_action == "Login to Existing Account":
        st.subheader("🔐 Student Login Gate")
        with st.form("login_form"):
            input_username = st.text_input("Username").lower().strip()
            input_password = st.text_input("Password", type="password")
            login_submit = st.form_submit_button("Login")
            
            if login_submit:
                if input_username in users_db and users_db[input_username]["password"] == input_password:
                    st.session_state.logged_in = True
                    st.session_state.is_guest = False
                    st.session_state.current_user = input_username
                    st.rerun()
                else:
                    st.error("Invalid Username or Password! Double check spelling.")

    elif auth_action == "Forgot Password 🔑":
        st.subheader("🔑 Secure Password Recovery Engine")
        
        if st.session_state.reset_step == 1:
            with st.form("verify_user_form"):
                forget_user = st.text_input("Enter Username").lower().strip()
                forget_email = st.text_input("Enter Registered Email")
                submit_verification = st.form_submit_button("Generate Dynamic Security Code")
                
                if submit_verification:
                    if forget_user in users_db and users_db[forget_user]["email"] == forget_email:
                        secure_code = str(random.randint(100000, 999999))
                        st.session_state.generated_code = secure_code
                        st.session_state.target_username = forget_user
                        st.session_state.reset_step = 2
                        st.rerun()
                    else:
                        st.error("Match failed! Username and email do not sync in database.")
                        
        if st.session_state.reset_step == 2:
            st.warning(f"🔒 AUTHORIZATION CODE GENERATED: `{st.session_state.generated_code}`")
            with st.form("code_and_reset_form"):
                entered_code = st.text_input("Enter the Authorization Code shown above").strip()
                new_pass_input = st.text_input("Set New Password", type="password")
                submit_final_reset = st.form_submit_button("Overwrite Password & Update System")
                
                if submit_final_reset:
                    if entered_code == st.session_state.generated_code:
                        tgt = st.session_state.target_username
                        save_user(tgt, new_pass_input, users_db[tgt]["name"], users_db[tgt]["email"])
                        st.success("Password verified and updated successfully! Switch to 'Login to Existing Account'.")
                        st.session_state.reset_step = 1
                        st.session_state.generated_code = None
                        st.session_state.target_username = None
                        st.rerun()
                    else:
                        st.error("Invalid dynamic code! Verification aborted.")

# =========================================================================
# 🚀 MAIN APPLICATION DASHBOARD (Accessed via valid Auth or Guest)
# =========================================================================
if st.session_state.logged_in or st.session_state.is_guest:
    if st.session_state.is_guest:
        username = "guest"
        name = "Guest Student"
        user_email = "None (Guest Session)"
        user_chat_key = "chat_history_guest"
    else:
        users_db = load_users()
        username = st.session_state.current_user
        name = users_db[username]["name"]
        user_email = users_db[username]["email"]
        user_chat_key = f"chat_history_{username}"

    if user_chat_key not in st.session_state:
        st.session_state[user_chat_key] = []

    # Global Clipboard Image Injection script
    components.html(
        """
        <script>
        const parentDoc = window.parent.document;
        parentDoc.addEventListener('paste', async (e) => {
            const clipboardItems = (e.clipboardData || e.originalEvent.clipboardData).items;
            for (const item of clipboardItems) {
                if (item.type.indexOf('image') !== -1) {
                    const imageBlob = item.getAsFile();
                    const uploaderInput = parentDoc.querySelector('input[type="file"]');
                    if (uploaderInput) {
                        const fileTransferCarrier = new DataTransfer();
                        fileTransferCarrier.items.add(imageBlob);
                        uploaderInput.files = fileTransferCarrier.files;
                        uploaderInput.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }
            }
        });
        </script>
        """,
        height=0,
    )

    # SIDEBAR CONFIGURATION
    st.sidebar.title(f"👋 Welcome, {name}!")
    st.sidebar.caption(f"Connected Email: {user_email}")
    
    domain_focus = st.sidebar.selectbox(
        "Select Educational Focus:",
        ["General Education", "Class 11 Science", "Class 12 Science", "Competitive Exams (JEE/NEET)", "Other"]
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔥 Select Your AI Energy")
    selected_model_display = st.sidebar.selectbox(
        "Choose Brain Power:",
        [
            "Main Character Vibe ⚡ (3.5 Flash — All-Around Help)", 
            "Low Battery Mode 🥱 (3.1 Flash-Lite — Fastest Answers)",
            "Final Boss Mode 🧠 (3.1 Pro — Hardcore Logic/Maths)"
        ]
    )

    if "Low Battery" in selected_model_display:
        chosen_model_id = "gemini-2.5-flash-lite"
    elif "Final Boss" in selected_model_display:
        chosen_model_id = "gemini-2.5-pro"
    else:
        chosen_model_id = "gemini-2.5-flash"

    st.sidebar.markdown("---")
    st.sidebar.subheader("📸 Visual Query Support")
    uploaded_visual_file = st.sidebar.file_uploader("Upload or Paste image file", type=["png", "jpg", "jpeg"])

    processed_image_payload = None
    if uploaded_visual_file is not None:
        processed_image_payload = Image.open(uploaded_visual_file)
        st.sidebar.image(processed_image_payload, caption="⚡ Image Processed", use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎙️ Voice Assistant Mode")
    
    voice_text_input = speech_to_text(
        start_prompt="🎤 Start Listening",
        stop_prompt="🛑 Stop Recording",
        language='en',
        use_container_width=True,
        key='speech'
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Clear My Chat History"):
        st.session_state[user_chat_key] = []
        st.rerun()

    if st.sidebar.button("🚪 Logout / Exit Portal"):
        st.session_state.logged_in = False
        st.session_state.is_guest = False
        st.session_state.current_user = None
        st.rerun()

    # APPLICATION MAIN STREAM
    st.title("🚀 StudyGenius Multi-User AI")
    st.caption(f"User Active: **{name}** | Focus: **{domain_focus}**")

    for chat_node in st.session_state[user_chat_key]:
        with st.chat_message(chat_node["role"]):
            if chat_node["type"] == "text":
                st.markdown(chat_node["content"])
            elif chat_node["type"] == "image":
                st.image(chat_node["content"], caption="Injected Structural Reference")

    current_user_query = st.chat_input("Ask StudyGenius anything...")
    if voice_text_input:
        current_user_query = voice_text_input

    # =========================================================================
    # STREAM ENGINE PIPELINE
    # =========================================================================
    if current_user_query:
        execution_payload_package = []
        
        if processed_image_payload is not None:
            execution_payload_package.append(processed_image_payload)
            with st.chat_message("user"):
                st.image(processed_image_payload, caption="User Attached Visual")
            st.session_state[user_chat_key].append({"role": "user", "type": "image", "content": processed_image_payload})

        with st.chat_message("user"):
            st.markdown(current_user_query)
        st.session_state[user_chat_key].append({"role": "user", "type": "text", "content": current_user_query})
        
        execution_payload_package.append(current_user_query)

        with st.chat_message("assistant"):
            try:
                curated_persona_matrix = f"You are StudyGenius AI, mentoring a student named {name} focusing on {domain_focus}. Respond in a structured, clean, helpful educational tone."
                
                ai_model_instance = genai.GenerativeModel(
                    model_name=chosen_model_id,
                    system_instruction=curated_persona_matrix
                )
                
                clean_historical_context = []
                for node in st.session_state[user_chat_key][:-1]:
                    if node["type"] == "text":
                        clean_historical_context.append({
                            "role": "user" if node["role"] == "user" else "model",
                            "parts": [node["content"]]
                        })
                
                active_chat_thread = ai_model_instance.start_chat(history=clean_historical_context)
                stream_response_chunks = active_chat_thread.send_message(execution_payload_package, stream=True)
                
                def text_stream_unroller():
                    for piece in stream_response_chunks:
                        yield piece.text
                        time.sleep(0.005)
                
                rendered_final_response = st.write_stream(text_stream_unroller())
                st.session_state[user_chat_key].append({"role": "assistant", "type": "text", "content": rendered_final_response})
                
                st.markdown("---")
                play_voice_response = st.checkbox("🔊 Play Voice Response for this answer", key=f"voice_choice_{len(st.session_state[user_chat_key])}")
                
                if play_voice_response:
                    with st.spinner("🔊 Tuning Voice Response..."):
                        clean_speech_text = rendered_final_response.replace("**", "").replace("*", "").replace("`", "")
                        tts_object = gTTS(text=clean_speech_text, lang='en', slow=False)
                        audio_buffer = io.BytesIO()
                        tts_object.write_to_fp(audio_buffer)
                        audio_buffer.seek(0)
                        st.audio(audio_buffer, format="audio/mp3", autoplay=True)
                
            except Exception as runtime_error:
                st.error(f"Error handling query pipeline: {runtime_error}")
