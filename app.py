import streamlit as st
import google.generativeai as genai
import time
from PIL import Image
import streamlit.components.v1 as components  # 🌟 Custom JS inject karne ke liye
from streamlit_paste_button import paste_image_button

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="StudyGenius AI", page_icon="🎓", layout="wide")

# API Key Config from Streamlit Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key missing! Please configure GEMINI_API_KEY in Streamlit Secrets.")

# =========================================================================
# 🌟 GLOBAL CTRL + V KEYBOARD SHORTCUT INJECTION (JavaScript Magic)
# =========================================================================
# Yeh script tumhare pure webpage par Ctrl+V bypass activate kar degi
components.html(
    """
    <script>
    const doc = window.parent.document;
    doc.addEventListener('paste', async (e) => {
        const items = (e.clipboardData || e.originalEvent.clipboardData).items;
        for (const item of items) {
            if (item.type.indexOf('image') !== -1) {
                const blob = item.getAsFile();
                // Streamlit ke default file uploader component ko target karke file drop trigger karna
                const fileUploader = doc.querySelector('input[type="file"]');
                if (fileUploader) {
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(blob);
                    fileUploader.files = dataTransfer.files;
                    fileUploader.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        }
    });
    </script>
    """,
    height=0, # Isko hidden rakhenge taaki UI kharab na ho
)

# 2. DYNAMIC USER PROFILE SIDEBAR
st.sidebar.title("👤 User Profile")
user_name = st.sidebar.text_input("Enter Your Name:", value="Guest Student")
educational_domain = st.sidebar.selectbox(
    "Select Educational Focus:",
    ["General Education", "Class 11 Science", "Class 12 Science", "Competitive Exams (JEE/NEET)", "Other"]
)

# 3. MULTIMODAL FEATURE (Handles Click & Global Ctrl+V)
st.sidebar.markdown("---")
st.sidebar.subheader("📸 Visual Query Support")
st.sidebar.info("💡 Tip: You can now press **Ctrl + V** anywhere on this page to paste a screenshot instantly!")

# Native file uploader jiske andar humara JavaScript data push karega
uploaded_file = st.sidebar.file_uploader("Upload or Paste image file", type=["png", "jpg", "jpeg"])

# Backup Paste Button (Just in case browser permissions blocks JS)
paste_result = paste_image_button(
    label="📋 Click to Paste from Clipboard",
    text_color="#ffffff",
    background_color="#FF4B4B",
    hover_background_color="#E03A3A",
    errors="ignore"
)

active_image = None

# Checking inputs priority
if uploaded_file is not None:
    active_image = Image.open(uploaded_file)
    st.sidebar.image(active_image, caption="📁 Image Processed Successfully", use_container_width=True)
elif paste_result and paste_result.image_data is not None:
    active_image = paste_result.image_data
    st.sidebar.image(active_image, caption="📋 Clipboard Data Detected", use_container_width=True)

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
# 6. INTERACTIVE STREAMING MODE
# =========================================================================
if user_prompt := st.chat_input("Ask StudyGenius anything..."):
    
    current_payload = []
    
    if active_image is not None:
        current_payload.append(active_image)
        with st.chat_message("user"):
            st.image(active_image, caption="Sent Image Analysis Request")
        st.session_state.chat_history.append({"role": "user", "type": "image", "content": active_image})

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
            
            st.session_state.chat_history.append({"role": "assistant", "type": "text", "content": full_response})
            
        except Exception as e:
            st.error(f"Error generating response: {e}")
