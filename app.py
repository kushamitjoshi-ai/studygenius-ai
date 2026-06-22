import streamlit as st
import os
from google import genai
from google.genai import types

# Page Configurations
st.set_page_config(
    page_title="StudyGenius AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set your Gemini API Key here
os.environ["GEMINI_API_KEY"] = "AIzaSyCQVwPb5HTh0ZwXbgH1gxfR1v7GP6s1F2Y"

# Initialize Google GenAI Client
try:
    client = genai.Client()
except Exception as e:
    st.error("API Client initialization failed. Please check your API Key configuration.")

# Sidebar UI (User Profile & Configuration)
with st.sidebar:
    st.title("🎓 StudyGenius AI")
    st.markdown("---")
    st.subheader("👤 Student Profile")
    
    student_name = st.text_input("Name", value="Kushgra Joshi")
    grade = st.selectbox("Class/Grade", ["Class 11", "Class 12", "Class 10", "College", "Competitive Exams"])
    stream = st.selectbox("Stream/Target", ["PCM (Science)", "PCB (Science)", "Commerce", "Arts", "JEE/NEET Aspirant"])
    study_hours = st.slider("Daily Study Commitment (Hours)", 1, 8, 4)
    
    st.markdown("---")
    st.caption("Powered by Gemini 2.5 Flash")

# Main Application Layout
st.title("📚 StudyGenius AI Dashboard")
st.write(f"##### Welcome back, **{student_name}**! Let's make learning smarter today. 🚀")

# 3-Column Quick Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Daily Streak 🔥", value="5 Days", delta="New Milestone!")
with col2:
    st.metric(label="Syllabus Tracked 📚", value="14%", delta="2% this week")
with col3:
    st.metric(label="Target Status 🎯", value="Active Mode")

st.markdown("---")

# Feature Tabs
tab1, tab2, tab3 = st.tabs(["💬 Instant AI Doubt Solver", "📅 Dynamic Study Planner", "📈 Analytics & Score Predictor"])

# TAB 1: AI Doubt Solver
with tab1:
    st.subheader("💡 Ask Your Complex Doubts")
    st.write("Type your question, upload an assignment picture, or talk to the AI tutor for step-by-step concepts.")
    
    # Text input query
    user_query = st.text_input("What concept or question are you struggling with today?", 
                              placeholder="e.g., Explain standard deviation or solve: Find the zeroes of the polynomial x^2 - 5x + 6")
    
    # Image input query placeholder
    uploaded_file = st.file_uploader("📷 Upload a picture of your question/problem sheet (Optional)", type=["png", "jpg", "jpeg"])
    
    if st.button("Solve & Explain instantly"):
        if user_query:
            with st.spinner("StudyGenius AI is evaluating the query and generating clean steps..."):
                try:
                    # Construct structural prompt context based on student profile data
                    system_prompt = f"You are StudyGenius AI, an expert, encouraging academic mentor for a student named {student_name} studying in {grade} ({stream}). Break down complex topics into clear, structured, step-by-step textbook solutions using formal, premium language. Explain core logic explicitly."
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=user_query,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            temperature=0.3
                        )
                    )
                    st.markdown("### 📝 Step-by-Step Resolution:")
                    st.write(response.text)
                    st.success("Doubt solved successfully! Read through the breakdown carefully.")
                except Exception as e:
                    st.error("Could not reach Gemini API server. Make sure your key is active.")
        else:
            st.warning("Please type a question or enter academic text to initiate the solver loop.")

# TAB 2: Study Planner
with tab2:
    st.subheader("📆 AI Generated Active Recall Timetable")
    st.write(f"Based on your daily target of **{study_hours} Hours**, here is your optimized roadmap:")
    
    # Simple Mock dynamic Schedule Output based on Input Hours
    st.markdown(f"""
    * **06:00 AM - 07:30 AM:** High Cognitive Tasks — Hard Concepts Review (Physics/Math derivations or Chemistry structures)
    * **04:00 PM - 05:30 PM:** Active Recall Problem Solving & Assignment Sheet Backlogs
    * **08:30 PM - 09:30 PM:** Revision Blocks & Mock Test Analytics Tracking with StudyGenius Portal
    """)
    st.info("Tip: Stick to the regular timetable routines to keep your 5-day daily streak active!")

# TAB 3: Score Tracker
with tab3:
    st.subheader("📊 Performance Metrics & Predicted Marks")
    st.write("Real-time data insights mapping student test scores and accuracy curves.")
    
    # Mock data layout representing backend storage data metrics
    st.progress(0.73, text="Current Baseline Accuracy Index: 73%")
    st.markdown("""
    * **Strong Modules:** Coordinate Geometry, Topics in Mechanics, General Vocabulary.
    * **Needs Improvement Loop:** Calculus, Multi-step Thermodynamic problems, Organic Conversions.
    * **Predicted Next Assessment Score:** **73 / 80** (Maintain active consistency to bump this scale up).
    """)
