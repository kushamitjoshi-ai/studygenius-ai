import streamlit as st
import google.generativeai as genai
import time
from PIL import Image
import streamlit.components.v1 as components

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="StudyGenius AI", page_icon="🎓", layout="wide")

# API Key Secrets Pull
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key missing! Please configure GEMINI_API_KEY in Streamlit Secrets.")

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

# 2. USER PROFILE & MODEL SELECTION SIDEBAR
st.sidebar.title("👤 User Profile")
profile_user = st.sidebar.text_input("Enter Your Name:", value="Guest Student")
domain_focus = st.sidebar.selectbox(
    "Select Educational Focus:",
    ["General Education", "Class 11 Science", "Class 12 Science", "Competitive Exams (JEE/NEET)", "Other"]
)

# 🌟 DYNAMIC LATEST MODEL SWITCHER PANEL (No more 404 errors)
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 AI Brain Configuration")
selected_model_display = st.sidebar.selectbox(
    "Choose Gemini Version:",
    [
        "Gemini 2.5 Flash (Default Speed)", 
        "Gemini 2.5 Flash-Lite (Low Quota Mode)",
        "Gemini 2.5 Pro (Advanced Logic & Maths)"
    ]
)

# Technical name mapping according to latest SDK registry
if "2.5 Flash-Lite" in selected_model_display:
    chosen_model_id = "gemini-2.5-flash-lite"
elif "2.5 Pro" in selected_model_display:
    chosen_model_id = "gemini-2.5-pro"
else:
    chosen_model_id = "gemini-2.5-flash"

# 3. MULTIMODAL CAPTURE PANEL
st.sidebar.markdown("---")
st.sidebar.subheader("📸 Visual Query Support")
st.sidebar.info("💡 Pro-Tip: Press **Ctrl + V** anywhere to paste screenshots instantly!")

uploaded_visual_file = st.sidebar.file_uploader("Upload or Paste image file", type=["png", "jpg", "jpeg"])

processed_image_payload = None
if uploaded_visual_file is not None:
    processed_image_payload = Image.open(uploaded_visual_file)
    st.sidebar.image(processed_image_payload, caption="⚡ Image Processed", use_container_width=True)

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.chat_history = []
    st.rerun()

# 4. INITIALIZE HISTORY MATRIX
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("🚀 StudyGenius AI")
st.caption(f"Session Stream: **{profile_user}** | Focus: **{domain_focus}** | Active Brain: **{chosen_model_id}**")

# 5. RENDER CONVERSATION HISTORY
for chat_node in st.session_state.chat_history:
    with st.chat_message(chat_node["role"]):
        if chat_node["type"] == "text":
            st.markdown(chat_node["content"])
        elif chat_node["type"] == "image":
            st.image(chat_node["content"], caption="Injected Structural Reference")

# =========================================================================
# 6. STREAM ENGINE PIPELINE
# =========================================================================
if current_user_query := st.chat_input("Ask StudyGenius anything..."):
    
    execution_payload_package = []
    
    if processed_image_payload is not None:
        execution_payload_package.append(processed_image_payload)
        with st.chat_message("user"):
            st.image(processed_image_payload, caption="User Attached Visual")
        st.session_state.chat_history.append({"role": "user", "type": "image", "content": processed_image_payload})

    with st.chat_message("user"):
        st.markdown(current_user_query)
    st.session_state.chat_history.append({"role": "user", "type": "text", "content": current_user_query})
    
    execution_payload_package.append(current_user_query)

    with st.chat_message("assistant"):
        try:
            curated_persona_matrix = f"You are StudyGenius AI, a top-tier educational assistant mentoring a student named {profile_user} focusing on {domain_focus}. Respond in a helpful, structured, and easy-to-understand educational tone."
            
            ai_model_instance = genai.GenerativeModel(
                model_name=chosen_model_id,
                system_instruction=curated_persona_matrix
            )
            
            clean_historical_context = []
            for node in st.session_state.chat_history[:-1]:
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
            st.session_state.chat_history.append({"role": "assistant", "type": "text", "content": rendered_final_response})
            
        except Exception as runtime_error:
            st.error(f"Error handling query pipeline: {runtime_error}")
