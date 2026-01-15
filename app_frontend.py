import streamlit as st
import httpx
import pandas as pd

# Configure page
st.set_page_config(
    page_title="AI Academic Advisor",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .risk-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .high-risk {
        background-color: #fef2f2;
        border: 1px solid #fee2e2;
        color: #991b1b;
    }
    .low-risk {
        background-color: #f0fdf4;
        border: 1px solid #dcfce7;
        color: #166534;
    }
    .stChatMessage {
        background-color: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎓 AI Academic Advisor")
st.markdown("### Personalized Study Planning & Risk Analysis")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for student data
with st.sidebar:
    st.header("Academic Metrics")
    attendance = st.slider("Attendance Rate", 0.0, 1.0, 0.8, help="Percentage of classes attended")
    quiz_score = st.slider("Quiz Score", 0.0, 10.0, 7.0, help="Average quiz score (0-10)")
    assignment_score = st.slider("Assignment Score", 0.0, 10.0, 8.0, help="Average assignment score (0-10)")
    study_hours = st.slider("Current Study Hours", 0.0, 20.0, 2.0, help="Daily study hours")
    midterm_score = st.slider("Midterm Score", 0.0, 100.0, 65.0, help="Last midterm score (0-100)")
    
    if st.button("Reset Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main Chat Interface
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask me about your study plan or how to improve..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)

    # Prepare payload
    student_data = {
        "attendance": attendance,
        "quiz_score": quiz_score,
        "assignment_score": assignment_score,
        "study_hours": study_hours,
        "midterm_score": midterm_score
    }
    
    payload = {
        "messages": st.session_state.messages,
        "student_data": student_data
    }

    try:
        with st.chat_message("assistant"):
            with st.spinner("Analyzing and generating plan..."):
                response = httpx.post("http://localhost:8000/generate-study-plan", json=payload, timeout=30.0)
            
            if response.status_code == 200:
                result = response.json()
                risk_score = result["risk_score"]
                detailed_plan = result["detailed_plan"]
                
                # Show Risk Score in a nice box
                risk_class = "high-risk" if risk_score > 0.4 else "low-risk"
                risk_label = "HIGH RISK" if risk_score > 0.4 else "ON TRACK"
                
                risk_html = f"""
                <div class="risk-card {risk_class}">
                    <strong>Academic Risk: {risk_score * 100:.0f}% ({risk_label})</strong>
                </div>
                """
                st.markdown(risk_html, unsafe_allow_html=True)
                
                # Show Plan
                st.markdown(detailed_plan)
                
                # Add to history
                full_response = f"**Risk Level: {risk_score*100:.0f}% ({risk_label})**\n\n{detailed_plan}"
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                st.error(f"Error from advisor: {response.text}")
                
    except Exception as e:
        st.error(f"Connection error: {str(e)}")

# Welcome message if chat is empty
if not st.session_state.messages:
    with chat_container:
        with st.chat_message("assistant"):
            st.markdown("👋 Hello! I'm your AI Academic Advisor. Adjust your metrics in the sidebar and send me a message to get a detailed study plan tailored just for you!")
