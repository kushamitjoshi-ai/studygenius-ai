import streamlit as st
import google.generativeai as genai
import time
from PIL import Image
import streamlit.components.v1 as components
import streamlit_authenticator as stauth
from streamlit_mic_recorder import speech_to_text
from gtts import gTTS
import io

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="StudyGenius AI", page_icon="🎓", layout="wide")

# API Key Secrets Pull
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key missing! Please configure GEMINI_API_KEY in Streamlit Secrets.")

# =========================================================================
# 🔐 MULTI-USER CONFIGURATION
# =========================================================================
config = {
    "credentials": {
        "usernames": {
            "kushagra": {
                "email": "kushagra@example.com",
                "name": "Kushagra Joshi",
                "password": "123"
            },
            "student2": {
                "email": "friend@example.com",
                "name": "Classmate",
                "password": "456"
            }
        }
    },
    "cookie": {
        "expiry_days": 30,
        "key": "signature_cookie_key",
        "name": "auth_cookie"
    }
}

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login('main')

if authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
elif authentication_status:
    
    user_chat_key = f"chat_history_{username}"
    if user_chat_key not in st.session_state:
        st.session_state[user_chat_key] = []

    # Global Ctrl+V Trigger for Clipboard Images
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

    # 2. SIDEBAR CONFIGURATION
    st.sidebar.title(f"👋 Welcome, {name}!")
    st.sidebar.caption(f"Connected Email: {config['credentials']['usernames'][username]['email']}")
    
    domain_focus = st.sidebar.selectbox(
        "Select Educational Focus:",
        ["General Education", "Class 11 Science", "Class 12 Science", "Competitive Exams (JEE/NEET)", "Other"]
    )

    # 🌟 NEW NO-CRINGE EXCLUSIVE 3.5 & 3.1 ENERGY SWITCHER PANEL
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

    # Backend Stealth Mapping according to API architecture
    if "Low Battery" in selected_model_display:
        chosen_model_id = "gemini-2.5-flash-lite" # Auto fallback for high-speed free tier channels
    elif "Final Boss" in selected_model_display:
        chosen_model_id = "gemini-2.5-pro"
    else:
        chosen_model_id = "gemini-2.5-flash"

    # MULTIMODAL CAPTURE PANEL
    st.sidebar.markdown("---")
    st.sidebar.subheader("📸 Visual Query Support")
    uploaded_visual_file = st.sidebar.file_uploader("Upload or Paste image file", type=["png", "jpg", "jpeg"])

    processed_image_payload = None
    if uploaded_visual_file is not None:
        processed_image_payload = Image.open(uploaded_visual_file)
        st.sidebar.image(processed_image_payload, caption="⚡ Image Processed", use_container_width=True)

    # 🎙️ VOICE ASSISTANT CONTROL CENTER IN SIDEBAR
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

    authenticator.logout('Logout', 'sidebar')

    # APPLICATION MAIN STREAM
    st.title("🚀 StudyGenius Multi-User AI")
    st.caption(f"User Active: **{name}** | Focus: **{domain_focus}**")

    # 5. RENDER EXCLUSIVE HISTORY
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
    # 6. STREAM ENGINE PIPELINE
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
                
                # 🔊 VOICE RESPONSE GENERATION
                with st.spinner("🔊 Tuning Voice Response..."):
                    clean_speech_text = rendered_final_response.replace("**", "").replace("*", "").replace("`", "")
                    tts_object = gTTS(text=clean_speech_text, lang='en', slow=False)
                    audio_buffer = io.BytesIO()
                    tts_object.write_to_fp(audio_buffer)
                    audio_buffer.seek(0)
                    st.audio(audio_buffer, format="audio/mp3", autoplay=True)
                
            except Exception as runtime_error:
                st.error(f"Error handling query pipeline: {runtime_error}")
