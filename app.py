import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests # Used to simulate calls to the FastAPI backend
from pydantic import BaseModel
from typing import List, Optional
import time
import random

# --- Pydantic Models for Frontend Data Validation (Mirroring Backend) ---
# These models ensure the data received from the FastAPI service is correctly structured.
class PrepTipsResponse(BaseModel):
    key_topics_to_revise: List[str]
    likely_behavioral_questions: List[str]
    likely_technical_questions: List[str]
    match_confidence: float
    match_feedback: str

# --- Configuration and Setup ---
st.set_page_config(layout="wide", page_title="Smart Job Tracker & AI Prep")

# Define the base URL for the running FastAPI backend
FASTAPI_URL = "http://127.0.0.1:8000"
# Hardcode a MOCK_USER_ID for demo purposes, bypassing full authentication
MOCK_USER_ID = "MOCK_USER_ID" 

# --- Utility Functions (API Calls to FastAPI Backend) ---

def fetch_schedule_data():
    """Fetches scheduled interviews from the FastAPI backend."""
    try:
        # Call the FastAPI endpoint defined in gmail_calendar.py
        response = requests.get(f"{FASTAPI_URL}/api/scheduler/applications/{MOCK_USER_ID}")
        response.raise_for_status() 
        data = response.json()
        
        if data.get('applications'):
            df = pd.DataFrame(data['applications'])
            # Convert date string (ISO format) to pandas datetime object
            df['Date'] = pd.to_datetime(df['date'], errors='coerce') 
            df = df.dropna(subset=['Date'])
            df['Date_Str'] = df['Date'].dt.strftime('%A, %B %d at %I:%M %p')
            return df
        return pd.DataFrame()

    except requests.exceptions.ConnectionError:
        # Handle case where the backend server is not running
        st.error(f"⚠️ Could not connect to FastAPI Backend at {FASTAPI_URL}. Please ensure the backend is running (uvicorn main:app --reload --port 8000).")
        return pd.DataFrame()
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP Error fetching schedule: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return pd.DataFrame()

def trigger_ai_analysis(app_id: str) -> Optional[PrepTipsResponse]:
    """Triggers the AI analysis endpoint in the FastAPI backend."""
    # The backend handles the logic of pairing the app_id (JD) with the user_id (Resume)
    payload = {
        "app_id": app_id,
        "user_id": MOCK_USER_ID
    }
    
    try:
        # Call the AI preparation endpoint defined in ai_prep.py
        response = requests.post(f"{FASTAPI_URL}/api/ai/prep", json=payload)
        response.raise_for_status()
        tips_data = response.json()
        return PrepTipsResponse(**tips_data)
        
    except requests.exceptions.HTTPError as e:
        st.error(f"AI Analysis Error: Could not generate tips. Details: {response.text}")
        return None
    except Exception as e:
        st.error(f"Failed to call AI endpoint: {e}")
        return None

def trigger_resume_upload(resume_file):
    """Mocks sending the resume text to the FastAPI backend for storage."""
    
    # Simulate text extraction from the uploaded file
    dummy_text = f"Experienced Python developer with skills in FastAPI, Docker, and {random.randint(3, 6)} years of cloud experience. Led two major microservice projects. Seeking Senior Backend role."
    
    # The payload structure matches the ResumeUpload Pydantic model
    payload = {
        "user_id": MOCK_USER_ID,
        "resume_text": dummy_text
    }
    
    try:
        # Call the mock save endpoint in gmail_calendar.py
        response = requests.post(
            f"{FASTAPI_URL}/api/scheduler/mock-save-resume/{MOCK_USER_ID}",
            json=payload
        )
        response.raise_for_status()
        
        st.session_state['resume_uploaded'] = True
        st.session_state['resume_name'] = resume_file.name
        return True
    except Exception as e:
        st.error(f"Failed to save resume text: {e}")
        return False

@st.cache_data
def ensure_mock_resume_endpoint_exists():
    """Helper to ensure the FastAPI mock endpoint is called upon startup."""
    try:
        # Send a harmless POST to ensure the backend's mock logic is initialized
        requests.post(
            f"{FASTAPI_URL}/api/scheduler/mock-save-resume/{MOCK_USER_ID}",
            json={"user_id": MOCK_USER_ID, "resume_text": "SetupCheck"},
            timeout=1
        )
    except Exception:
        pass


# --- Streamlit UI Components ---

def render_calendar_dashboard(df_schedule):
    """Renders the custom designed calendar/schedule view, grouped by week."""
    
    st.subheader("🗓️ Interview Schedule (Calendar View)")
    
    # Filter and sort data
    upcoming_interviews = df_schedule[df_schedule['status'] == 'Upcoming'].sort_values('Date')
    completed_interviews = df_schedule[df_schedule['status'] == 'Completed']

    st.info(f"You have **{len(upcoming_interviews)}** interviews scheduled in the system.")
    
    # Explanation of the automatic reminder feature
    st.markdown("""
        <small style='color: #4CAF50;'>✅ **Reminder Automation:** Events are automatically pushed to Google Calendar with server-side email/pop-up reminders (24h and 1h prior).</small>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if upcoming_interviews.empty:
        st.success("No upcoming interviews. Keep applying!")
        return

    # --- Calendar Grouping Logic (Custom Visual Calendar) ---
    upcoming_interviews['Week'] = upcoming_interviews['Date'].apply(lambda x: x.isocalendar()[1])
    
    def get_week_start_date(date_obj):
        # Calculate the Monday of the given week
        start_of_week = date_obj - timedelta(days=date_obj.weekday())
        return start_of_week.strftime("%b %d")

    grouped_weeks = upcoming_interviews.groupby('Week')

    for week_num, week_data in grouped_weeks:
        # Use .to_pydatetime() for accurate timedelta calculations
        first_date_of_week = week_data['Date'].min().to_pydatetime()
        week_start_str = get_week_start_date(first_date_of_week)
        
        # Expand current or next week automatically
        is_current_or_next_week = (first_date_of_week - datetime.now()).days <= 14
        
        with st.expander(f"📅 **Week of {week_start_str}** ({len(week_data)} Events)", expanded=is_current_or_next_week):
            
            week_data_sorted = week_data.sort_values('Date')

            for index, row in week_data_sorted.iterrows():
                days_until = (row['Date'].to_pydatetime() - datetime.now()).days
                
                # Conditional styling for urgency
                if days_until < 3:
                    color = "#f44336" # Red for urgent
                    emoji = "🚨"
                elif days_until < 7:
                    color = "#ff9800" # Orange for soon
                    emoji = "⚠️"
                else:
                    color = "#4CAF50" # Green for future
                    emoji = "✅"
                
                # Custom HTML/Markdown card for visual appeal
                card_html = f"""
                <div style="
                    border-left: 5px solid {color};
                    padding: 10px;
                    margin: 8px 0;
                    border-radius: 6px;
                    box-shadow: 0 2px 4px 0 rgba(0,0,0,0.1);
                    background-color: #2e3037; 
                ">
                    <h6 style='margin-top: 0px; margin-bottom: 5px; font-weight: bold;'>{row['company']} - {row['role']}</h6>
                    <p style='font-size: 14px; margin: 0;'>{emoji} **{row['Date'].strftime('%a, %b %d at %I:%M %p')}**</p>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
    st.markdown("---")
    
    # Display completed applications
    with st.expander("View Completed Applications"):
        if not completed_interviews.empty:
            st.dataframe(completed_interviews[['company', 'role', 'Date_Str', 'status']].rename(columns={'Date_Str': 'Interview Date', 'company': 'Company', 'role': 'Role'}), use_container_width=True)
        else:
            st.markdown("No completed interviews tracked yet.")


def render_ai_assistant(df_schedule): 
    """Renders the AI Prep Assistant interface (Right Column)."""
    
    st.subheader("🧠 AI Interview Prep Assistant")
    
    # --- 1. Resume Upload Section ---
    st.markdown("##### 1. Upload Your Resume")
    uploaded_file = st.file_uploader(
        "Upload your latest resume (PDF, DOCX, TXT)", 
        type=["pdf", "docx", "txt"], 
        key="resume_uploader"
    )

    if uploaded_file is not None and not st.session_state.get('resume_uploaded'):
        if trigger_resume_upload(uploaded_file):
            st.success(f"Resume uploaded and processed: **{uploaded_file.name}**")
    
    if st.session_state.get('resume_uploaded'):
        st.success(f"Active Resume: **{st.session_state.get('resume_name')}**")
    else:
        st.warning("Please upload a resume to activate personalized tips.")

    st.markdown("---")
    
    # --- 2. Automated Job Description Selection ---
    st.markdown("##### 2. Select Job for Analysis (JD is pre-filled from Tracker)")
    
    job_options = ['--- Select an Application ---'] + [
        f"{row['company']} - {row['role']}" 
        for index, row in df_schedule.iterrows()
        if row['status'] == 'Upcoming'
    ]
    
    selected_job_title = st.selectbox(
        "Choose an upcoming interview from your tracker:",
        options=job_options,
        key="job_selector"
    )
    
    job_description = ""
    app_id = None
    
    if selected_job_title != '--- Select an Application ---':
        selected_job = df_schedule[
            (df_schedule['company'] + ' - ' + df_schedule['role']) == selected_job_title
        ].iloc[0]
        
        job_description = selected_job['jd_text']
        app_id = selected_job['app_id']
        
        st.text_area(
            "Job Description (Automatically Extracted by Gmail API):",
            value=job_description,
            height=150,
            disabled=True 
        )
    
    st.markdown("---")
    
    # --- 3. Generate Tips Button ---
    button_disabled = not (st.session_state.get('resume_uploaded') and selected_job_title != '--- Select an Application ---')

    if st.button("Generate Personalized Prep Tips", use_container_width=True, disabled=button_disabled):
        if job_description:
            with st.spinner("Analyzing JD and Resume... Calling FastAPI/OpenAI Service..."):
                tips = trigger_ai_analysis(app_id)
            
            if tips:
                st.session_state['prep_tips'] = tips
                st.session_state['jd_analyzed'] = job_description
                st.balloons()
        
    st.markdown("---")
    
    # --- 4. Display AI Generated Tips ---
    if 'prep_tips' in st.session_state:
        st.markdown("##### ✨ Your Personalized Interview Prep Guidance")
        
        tips: PrepTipsResponse = st.session_state['prep_tips']
        match_confidence = tips.match_confidence
        
        # --- CONDITIONAL MISMATCH NOTIFICATION LOGIC ---
        if match_confidence < 0.6: 
            st.error(f"⚠️ **LOW MATCH WARNING (Compatibility Score: {match_confidence*100:.0f}%)**")
            st.markdown(f"The AI detected a significant mismatch between your resume and the core requirements of this Job Description.")
            st.warning(f"**Action Required:** {tips.match_feedback}")
            st.markdown("---")
        else:
            st.success(f"✅ **HIGH MATCH (Compatibility Score: {match_confidence*100:.0f}%)**")
            # Display positive feedback, using the first sentence of the match_feedback for emphasis
            st.info(f"The AI suggests your profile is strong. Focus on reinforcing {tips.match_feedback.split('.')[0]}.")
            st.markdown("---")
        # --- END CONDITIONAL MISMATCH NOTIFICATION LOGIC ---

        
        with st.expander("💡 Key Topics to Revise", expanded=True):
            st.markdown("Based on the **JD vs. your Resume**, focus on these technical and project areas:")
            st.markdown("\n".join([f"- **{topic}**" for topic in tips.key_topics_to_revise]))
            
        with st.expander("👥 Likely Behavioral Questions"):
            st.markdown("Be ready with **STAR** examples for these scenarios:")
            st.markdown("\n".join([f"- *{q}*" for q in tips.likely_behavioral_questions]))
            
        with st.expander("💻 Likely Technical Questions"):
            st.markdown("Prepare concise answers for these core technical challenges:")
            st.markdown("\n".join([f"- `{q}`" for q in tips.likely_technical_questions]))


# --- Main Application Logic ---

def main():
    """Main function to orchestrate the Streamlit application."""
    
    st.title("Smart Job Application Tracker & AI Prep Assistant")
    st.caption("Automating Logistics, Powering Intelligence")
    
    # Initialize session state 
    if 'resume_uploaded' not in st.session_state:
        st.session_state['resume_uploaded'] = False
        st.session_state['resume_name'] = ""
        
    # Attempt to initialize the mock data in the backend
    ensure_mock_resume_endpoint_exists()
    
    df_schedule = fetch_schedule_data()

    if df_schedule.empty:
        # Stop if the backend isn't running and data cannot be fetched
        st.warning("Cannot retrieve data. Please ensure the FastAPI backend is running and check the error message above.")
        st.stop()

    # Define the two columns for the main layout
    col1, col2 = st.columns([1, 1.2], gap="large") 

    with col1:
        render_calendar_dashboard(df_schedule)

    with col2:
        render_ai_assistant(df_schedule)

if __name__ == "__main__":
    # Note: The mock router inclusion for the resume endpoint is handled 
    # outside the `if __name__ == "__main__":` block in the Canvas for simplicity, 
    # but for pure execution, it must be ensured.
    main()
