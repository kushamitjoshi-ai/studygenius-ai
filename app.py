import streamlit as st
import google.generativeai as genai
import time
from PIL import Image
from streamlit_paste_button import paste_image_button  # 🌟 Clipboard paste ke liye library

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="StudyGenius AI", page_icon="🎓", layout="wide")

# API Key Config from Streamlit Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key missing! Please configure GEMINI_API_KEY in Streamlit Secrets.")

# 2. DYNAMIC USER PROFILE SIDEBAR
st.sidebar.title("👤 User Profile")
user_name = st.sidebar.text_input("Enter Your Name:", value="Guest Student")
educational_domain = st.sidebar.selectbox(
    "Select Educational Focus:",
    ["General Education", "Class 11 Science", "Class 12 Science", "Competitive Exams (JEE/NEET)", "Other"]
)

# 3. ADVANCED MULTIMODAL: CLIPBOARD PASTE & FILE UPLOADER
st.sidebar.markdown("---")
st.sidebar.subheader("📸 Visual Query Support")

# Option A: Direct Clipboard Paste (Ctrl + V)
st.sidebar.write("Click below & paste (`Ctrl+V`) your screenshot:")
paste_result = paste_image_button(
    label="📋 Paste Image from Clipboard",
    text_color="#ffffff",
    background_color="#FF4B4B",
    hover_background_color="#E03A3A",
    errors="ignore"
)

# Option B: Standard File Uploader (Backup tool)
uploaded_file = st.sidebar.file_uploader("Or upload image file manually", type=["png", "jpg", "jpeg"])

# Variable to hold the active image payload
active_image = None

# Prioritize paste button data, if empty check uploader
if paste_result and paste_result.image_data is not None:
    active_image = paste_result.image_data
    st.sidebar.image(active_image, caption="📋 Clipboard Image Detected", use_container_width=True)
elif uploaded_file is not None:
    active_image = Image.open(uploaded_file)
    st.sidebar.image(active_image, caption="📁 File Uploaded Successfully", use_container_width=True)

# Clear History Button
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.chat_history = []
    st.rerun()

# 4. INITIALIZE CHAT HISTORY
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Main App Header
st.title("🚀 StudyGenius AI")
st.caption(f"Logged in as: **{user_name}** | Focus: **{educational_domain}**")

# 5. DISPLAY PAST CONVERSATION
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        if message["type"] == "text":
            st.markdown(message["content"])
        elif message["type"] == "image":
            st.image(message["content"], caption="Analyzed Visual Context")

# =========================================================================
# 6. INTERACTIVE STREAMING MODE (With Clipboard Image Injection)
# =========================================================================
if user_prompt := st.chat_input("Ask StudyGenius anything..."):
    
    # Multimodal payload setup
    current_payload = []
    
    # Check if there is an active image (either pasted or uploaded)
    if active_image is not None:
        current_payload.append(active_image)
        with st.chat_message("user"):
            st.image(active_image, caption="Sent Image Analysis Request")
        st.session_state.chat_history.append({"role": "user", "type": "image", "content": active_image})

    # Append and log User Text
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.chat_history.append({"role": "user", "type": "text", "content": user_prompt})
    
    current_payload.append(user_prompt)

    # AI Response Streaming Engine
    with st.chat_message("assistant"):
        try:
            system_instruction = f"You are StudyGenius AI, a top-tier educational assistant mentoring a student named {user_name} focusing on {educational_domain}. Respond in a helpful, structured, and easy-to-understand educational tone."
            
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=system_instruction
            )
            
            # Extract clean context string for conversation flow
            formatted_history = []
            for msg in st.session_state.chat_history[:-1]:
                if msg["type"] == "text":
                    formatted_history.append({
                        "role": "user" if msg["role"] == "user" else "model",
                        "parts": [msg["content"]]
                    })
            
            chat = model.start_chat(history=formatted_history)
            response = chat.send_message(current_payload, stream=True)
            
            def response_generator():
                for chunk in response:
                    yield chunk.text
                    time.sleep(0.01)
            
            full_response = st.write_stream(response_generator())
            
            # Save AI's response to history
            st.session_state.chat_history.append({"role": "assistant", "type": "text", "content": full_response})
            
        except Exception as e:
            st.error(f"Error generating response: {e}")
