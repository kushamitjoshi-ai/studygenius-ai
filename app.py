import streamlit as st
import google.generativeai as genai
import time
from PIL import Image

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="StudyGenius AI", page_icon="🎓", layout="wide")

# API Key Config from Streamlit Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key missing! Please configure GEMINI_API_KEY in Streamlit Secrets.")

# 2. DYNAMIC USER PROFILE SIDEBAR (Multi-device and multi-user support)
st.sidebar.title("👤 User Profile")
user_name = st.sidebar.text_input("Enter Your Name:", value="Guest Student")
educational_domain = st.sidebar.selectbox(
    "Select Educational Focus:",
    ["General Education", "Class 11 Science", "Class 12 Science", "Competitive Exams (JEE/NEET)", "Other"]
)

# 3. MULTIMODAL FEATURE (Image/Diagram Upload or Paste Support)
st.sidebar.markdown("---")
st.sidebar.subheader("📸 Visual Query Support")
uploaded_image = st.sidebar.file_uploader("Upload or Paste image/diagram", type=["png", "jpg", "jpeg"])

if uploaded_image:
    st.sidebar.image(uploaded_image, caption="Uploaded Preview", use_container_width=True)

# Clear History Button
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.chat_history = []
    st.rerun()

# 4. INITIALIZE CHAT HISTORY (With type-checking to prevent crashes)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Main App Header (Dynamically personalized)
st.title("🚀 StudyGenius AI")
st.caption(f"Logged in as: **{user_name}** | Focus: **{educational_domain}**")

# 5. DISPLAY PAST CONVERSATION (Handles text and images safely)
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        if message["type"] == "text":
            st.markdown(message["content"])
        elif message["type"] == "image":
            st.image(message["content"], caption="Analyzed Visual Context")

# =========================================================================
# 6. INTERACTIVE STREAMING MODE (A TO Z FEATURE EXECUTION)
# =========================================================================
if user_prompt := st.chat_input("Ask StudyGenius anything..."):
    
    # Payload pipeline create karna jo multimodal content pass kar sake
    current_payload = []
    
    # A. Agar user ne image upload ki hai, toh use handle aur display karo
    if uploaded_image:
        img = Image.open(uploaded_image)
        current_payload.append(img)
        
        with st.chat_message("user"):
            st.image(img, caption="Sent Image Analysis Request")
        st.session_state.chat_history.append({"role": "user", "type": "image", "content": img})

    # B. User ka text message display aur save karo
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.chat_history.append({"role": "user", "type": "text", "content": user_prompt})
    
    current_payload.append(user_prompt)

    # C. AI Response Streaming Generator
    with st.chat_message("assistant"):
        try:
            # Customized dynamic persona injection
            system_instruction = f"You are StudyGenius AI, a top-tier educational assistant mentoring a student named {user_name} focusing on {educational_domain}. Respond in a helpful, structured, and easy-to-understand educational tone."
            
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=system_instruction
            )
            
            # Format clean text history for Gemini context chain
            formatted_history = []
            for msg in st.session_state.chat_history[:-1]:
                if msg["type"] == "text":
                    formatted_history.append({
                        "role": "user" if msg["role"] == "user" else "model",
                        "parts": [msg["content"]]
                    })
            
            # Start conversational chat session
            chat = model.start_chat(history=formatted_history)
            
            # Request token streaming payload from Gemini
            response = chat.send_message(current_payload, stream=True)
            
            # Real-time fluid text rendering generator function
            def response_generator():
                for chunk in response:
                    yield chunk.text
                    time.sleep(0.01) # Perfect typing effect pace
            
            full_response = st.write_stream(response_generator())
            
            # Save the generated final text response to session history
            st.session_state.chat_history.append({"role": "assistant", "type": "text", "content": full_response})
            
        except Exception as e:
            st.error(f"Error generating response: {e}")
