import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests 
from pydantic import BaseModel
from typing import List, Optional
import time
import random
import urllib.parse 

# --- Pydantic Models for Frontend Data Validation (Mirroring Backend) ---
# ... (PrepTipsResponse remains unchanged)
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

# --- Session State Initialization ---
# Setting the default MOCK_USER_ID here ensures the app loads data when not logged in.
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = "MOCK_USER_ID" 
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = "Guest"
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'resume_uploaded' not in st.session_state:
    st.session_state['resume_uploaded'] = False
if 'resume_name' not in st.session_state:
    st.session_state['resume_name'] = ""
if 'messages' not in st.session_state:
    st.session_state.messages = []
        
# --- API Calls to FastAPI Backend ---

def check_auth_status():
    """Checks the authentication status and token existence for the current user."""
    user_id = st.session_state['user_id']
    
    # Only check if we are not already authenticated
    if st.session_state['authenticated']:
        return True

    try:
        # Check if the current user_id (either MOCK or previously logged in) has a token
        # Note: We must ensure we are not checking the 'Guest' state unless we fall back to it.
        if user_id == "MOCK_USER_ID" and not st.session_state['authenticated']:
             return False
             
        response = requests.get(f"{FASTAPI_URL}/auth/user/status?user_id={user_id}")
        response.raise_for_status()
        data = response.json()
        
        if data.get('authenticated'):
            # If the backend confirms a token exists for this user_id, update state
            st.session_state['authenticated'] = True
            # Note: We rely on the callback or local state for the name, as the status endpoint doesn't return it.
            return True
        
        return False

    except requests.exceptions.ConnectionError:
        st.error(f"⚠️ Could not connect to FastAPI Backend at {FASTAPI_URL}.")
        return False
    except Exception:
        return False

@st.cache_data
def handle_oauth_callback():
    """
    Processes the redirection from the FastAPI callback endpoint.
    This runs once per page load to check the URL parameters.
    """
    query_params = st.query_params
    
    # 1. Check for the authentication success flag sent by FastAPI
    if query_params.get('auth_success') == 'true':
        
        user_id = query_params.get('user_id')
        user_name = query_params.get('user_name', 'Authenticated User')
        
        if user_id:
            # Update the session state with the real authenticated user data
            st.session_state['user_id'] = user_id
            st.session_state['user_name'] = user_name
            st.session_state['authenticated'] = True
            st.success(f"Authentication successful for {user_name}!")
        else:
            st.error("OAuth Callback failed: No user ID returned from backend redirect.")
        
        # --- CRITICAL FIX APPLIED HERE ---
        # 2. Clear the URL parameters and force a full Streamlit re-run.
        # This ensures the new session state (user_id, authenticated=True) is applied 
        # to the entire dashboard instantly, removing the "Sign In" button.
        st.query_params = {}
        st.experimental_rerun()
        # --- END CRITICAL FIX ---
        
    # Check status if no redirect parameters were found (i.e., a normal load/rerun)
    # On subsequent runs, this checks if a token exists for the current user_id.
    check_auth_status()


def fetch_schedule_data():
    """Fetches scheduled interviews from the FastAPI backend."""
    user_id = st.session_state['user_id']
    
    try:
        response = requests.get(f"{FASTAPI_URL}/api/scheduler/applications/{user_id}")
        response.raise_for_status() 
        data = response.json()
        
        if data.get('applications'):
            df = pd.DataFrame(data['applications'])
            df['Date'] = pd.to_datetime(df['date'], errors='coerce') 
            df = df.dropna(subset=['Date'])
            df['Date_Str'] = df['Date'].dt.strftime('%A, %B %d at %I:%M %p')
            return df
        return pd.DataFrame()

    except requests.exceptions.ConnectionError:
        st.error(f"⚠️ Could not connect to FastAPI Backend at {FASTAPI_URL}.")
        return pd.DataFrame()
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP Error fetching schedule: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return pd.DataFrame()


def trigger_ai_analysis(app_id: str) -> Optional[PrepTipsResponse]:
    """Triggers the AI analysis endpoint in the FastAPI backend."""
    user_id = st.session_state['user_id']
    
    payload = {
        "app_id": app_id,
        "user_id": user_id
    }
    
    try:
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
    user_id = st.session_state['user_id']
    
    # Simulate text extraction from the uploaded file
    dummy_text = f"Experienced Python developer with skills in FastAPI, Docker, and {random.randint(3, 6)} years of cloud experience. Led two major microservice projects. Seeking Senior Backend role."
    
    payload = {
        "user_id": user_id,
        "resume_text": dummy_text
    }
    
    try:
        response = requests.post(
            f"{FASTAPI_URL}/api/scheduler/mock-save-resume/{user_id}",
            json=payload
        )
        response.raise_for_status()
        
        st.session_state['resume_uploaded'] = True
        st.session_state['resume_name'] = resume_file.name
        return True
    except Exception as e:
        st.error(f"Failed to save resume text: {e}")
        return False

def trigger_gmail_check(user_id: str):
    """Triggers the background task for the Gmail/Calendar check."""
    try:
        # Note: The FastAPI endpoint expects a User model with 'id', 'email', 'name'
        # Since we only have user_id and name, we mock the email
        payload = {
            "id": user_id,
            "email": f"{user_id}@mockuser.com",
            "name": st.session_state['user_name']
        }
        response = requests.post(f"{FASTAPI_URL}/api/scheduler/start-check", json=payload)
        response.raise_for_status()
        st.success("Background Gmail check initiated! Check your calendar for new events (simulated).")
    except requests.exceptions.HTTPError as e:
        st.error(f"Gmail Check Error: The server could not start the check. Details: {response.text}")
    except Exception as e:
        st.error(f"Failed to start background check: {e}")

# --- NEW: Function to simulate chat interaction ---
def simulate_chat(prompt, app_id=None):
    """Mocks calling an AI endpoint for real-time interview practice."""
    # In a real app, this would call a FastAPI endpoint that uses OpenAI/Gemini
    # to maintain a conversation history and generate context-aware questions/feedback.
    
    if "hello" in prompt.lower() or "start" in prompt.lower():
        # Use a random JD to start the mock interview context
        jd_context = "Data Scientist role focusing on statistical modeling and Python."
        return f"Hello, {st.session_state['user_name']}! Welcome to your Mock Interview for the **{jd_context}**. Let's start. \n\n**Question 1:** *Tell me about a time you used data visualization to solve a complex business problem.*"
    
    elif "star" in prompt.lower() or "problem" in prompt.lower():
        return "That's a good structured answer! Now, can you dive deeper into the **Action** part? Specifically, how did you handle the data cleaning process?"
    
    else:
        return "Thank you. Let's move to a behavioral question: *How do you handle disagreements with stakeholders regarding model assumptions?*"
# --------------------------------------------------

def render_header_and_auth():
    """Renders the title and the login/logout button logic."""
    
    # --- CHANGE: Use st.columns to position the user info neatly ---
    title_col, spacer, auth_col = st.columns([4, 2, 2])
    
    with title_col:
        st.title("Smart Job Application Tracker & AI Prep Assistant")
        st.caption("Automating Logistics, Powering Intelligence")
    
    with auth_col:
        st.markdown("<div style='text-align: right; margin-top: 15px;'>", unsafe_allow_html=True)
        
        if st.session_state['authenticated']:
            # Authenticated State with User Icon and Name
            user_name_display = st.session_state['user_name'].split(' ')[0] # First name only
            
            st.markdown(f"""
                <span style='font-size: 16px; font-weight: bold; color: #4CAF50;'>
                    👋 Logged in as: {user_name_display}
                </span>
                <br>
                <div style='display: flex; justify-content: flex-end;'>
                    <span style='font-size: 12px; color: grey; margin-right: 10px;'>{st.session_state['user_id']}</span>
                    {'<span style="cursor: pointer;">' if not st.session_state['authenticated'] else ''}
                    <span style='font-size: 24px;'>&#128100;</span>
                    {'</span>' if not st.session_state['authenticated'] else ''}
                </div>
            """, unsafe_allow_html=True)
            
            # Use two smaller columns for the action buttons
            btn_col1, btn_col2 = st.columns([1, 1])
            with btn_col1:
                 if st.button("Check Gmail (Sim)", type="secondary", use_container_width=True):
                    trigger_gmail_check(st.session_state['user_id'])
            with btn_col2:
                 if st.button("Logout", key="logout_btn", type="primary", use_container_width=True):
                    st.session_state['user_id'] = "MOCK_USER_ID"
                    st.session_state['user_name'] = "Guest"
                    st.session_state['authenticated'] = False
                    st.experimental_rerun()
            
        else:
            # Unauthenticated State
            if st.button("Sign In with Google", key="login_btn", type="primary", use_container_width=True):
                login_url = f"{FASTAPI_URL}/auth/google/login"
                st.markdown(f'<meta http-equiv="refresh" content="0; url={login_url}">', unsafe_allow_html=True)
                st.stop() 
            st.markdown(f"<small>Using **{st.session_state['user_id']}**</small>", unsafe_allow_html=True)

            if st.button("Use Mock Data", key="mock_load_btn", use_container_width=True):
                 st.session_state['user_id'] = "MOCK_USER_ID"
                 st.session_state['user_name'] = "Guest"
                 st.session_state['authenticated'] = False
                 st.experimental_rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
# --- The remaining rendering functions remain the same ---

def render_calendar_dashboard(df_schedule):
    """Renders the custom designed calendar/schedule view, grouped by week."""
    
    user_id_display = st.session_state['user_id']
    st.subheader(f"🗓️ Interview Schedule ({st.session_state['user_name']}'s Data)")
    
    # Filter and sort data
    upcoming_interviews = df_schedule[df_schedule['status'] == 'Upcoming'].sort_values('Date')
    completed_interviews = df_schedule[df_schedule['status'] == 'Completed']

    st.info(f"You have **{len(upcoming_interviews)}** interviews scheduled in the system.")
    
    # The reminder feature relies on the successful OAuth flow
    if st.session_state['authenticated']:
        st.markdown("""
            <small style='color: #4CAF50;'>✅ **Reminder Automation:** Events are automatically pushed to Google Calendar with reminders.</small>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <small style='color: #ff9800;'>⚠️ **Sign In Required:** Sign in with Google to enable automatic Gmail checking and Calendar scheduling.</small>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    if upcoming_interviews.empty:
        st.success("No upcoming interviews. Keep applying!")
        return

    # --- Calendar Grouping Logic (Custom Visual Calendar) ---
    upcoming_interviews['Week'] = upcoming_interviews['Date'].apply(lambda x: x.isocalendar()[1])
    
    def get_week_start_date(date_obj):
        start_of_week = date_obj - timedelta(days=date_obj.weekday())
        return start_of_week.strftime("%b %d")

    grouped_weeks = upcoming_interviews.groupby('Week')

    for week_num, week_data in grouped_weeks:
        first_date_of_week = week_data['Date'].min().to_pydatetime()
        week_start_str = get_week_start_date(first_date_of_week)
        
        is_current_or_next_week = (first_date_of_week - datetime.now()).days <= 14
        
        with st.expander(f"📅 **Week of {week_start_str}** ({len(week_data)} Events)", expanded=is_current_or_next_week):
            
            week_data_sorted = week_data.sort_values('Date')

            for index, row in week_data_sorted.iterrows():
                days_until = (row['Date'].to_pydatetime() - datetime.now()).days
                
                if days_until < 3:
                    color = "#f44336" # Red for urgent
                    emoji = "🚨"
                elif days_until < 7:
                    color = "#ff9800" # Orange for soon
                    emoji = "⚠️"
                else:
                    color = "#4CAF50" # Green for future
                    emoji = "✅"
                
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
    
    tab1, tab2 = st.tabs(["📝 Prep Notes & Match Score", "💬 Mock Interview Chatbot"])

    with tab1:
        st.subheader("📝 Personalized Interview Prep Notes")
        
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

    with tab2:
        st.subheader("💬 AI Interview Chatbot (Mock Practice)")
        
        # Display chat messages from history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input logic
        if prompt := st.chat_input("Start a mock interview or ask a question (e.g., 'Hello' or 'My answer is...')"):
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Simulate AI response
            with st.spinner("AI is analyzing your response..."):
                response = simulate_chat(prompt, app_id=app_id) # Use the selected app_id for context
                
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})


# --- Main Application Logic ---

def main():
    """Main function to orchestrate the Streamlit application."""
    
    # 1. Handle OAuth Callback before rendering anything else
    handle_oauth_callback()
    
    # 2. Render Header and Auth Buttons (User Icon placement)
    render_header_and_auth()
    
    # 3. Determine the User ID for data fetching
    current_user_id = st.session_state['user_id']
    
    # If the user is neither authenticated nor in mock mode, stop here and wait for login/mock load
    # This logic is now handled by checking if current_user_id is the default MOCK_USER_ID or a real ID
    if current_user_id == "MOCK_USER_ID" and not st.session_state['authenticated']:
        st.warning("Please click 'Sign In with Google' or 'Use Mock Data' to continue.")
        # If we are using MOCK_USER_ID, proceed, otherwise stop if it's unset (which it shouldn't be).
        if st.session_state['user_id'] == "MOCK_USER_ID":
             pass
        else:
             st.stop()
        
    # 4. Fetch data using the determined user ID
    df_schedule = fetch_schedule_data()

    if df_schedule.empty:
        st.warning("Cannot retrieve data. Please ensure the FastAPI backend is running.")
        st.stop()

    # 5. Define the two columns for the main layout
    col1, col2 = st.columns([1, 1.2], gap="large") 

    with col1:
        render_calendar_dashboard(df_schedule)

    with col2:
        render_ai_assistant(df_schedule)

if __name__ == "__main__":
    main()
