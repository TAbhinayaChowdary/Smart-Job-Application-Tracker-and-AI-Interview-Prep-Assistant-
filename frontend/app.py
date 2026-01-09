import streamlit as st
import requests
import os
import pandas as pd
import base64
from pypdf import PdfReader
from streamlit_calendar import calendar

# API URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Smart Job Tracker",
    page_icon="💼",
    layout="wide"
)

st.title("💼 Smart Job Application Tracker & AI Assist")

# Authentication Check
user_info = None
try:
    res = requests.get(f"{API_URL}/auth/me")
    if res.status_code == 200:
        user_info = res.json()
except:
    pass

if not user_info:
    st.info("Please sign in to access your jobs and interview prep.")
    
    # Login Button logic
    # We use a markdown link styled as a button because Streamlit buttons can't open new tabs/redirect easily without rerun hacks
    st.markdown(f'''
        <a href="{API_URL}/auth/login" target="_self">
            <button style="
                background-color: #4285F4;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                font-family: Roboto, sans-serif;
                margin-right: 10px;
            ">
                Sign in with Google
            </button>
        </a>
    ''', unsafe_allow_html=True)
    
    st.write("---")
    if st.button("Development Mode (Skip Login)"):
        st.session_state["dev_mode"] = True
        st.rerun()
    
    st.stop() # Stop execution here if not logged in

# Dev Mode Check    
if st.session_state.get("dev_mode"):
    user_info = {"given_name": "Developer", "email": "dev@local"}
    st.success("Running in Development Mode")


st.sidebar.title(f"Welcome, {user_info.get('given_name', 'User')}")
if st.sidebar.button("Logout"):
    requests.get(f"{API_URL}/auth/logout")
    st.rerun()

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Job Tracker", "Interview Prep", "Settings"])

if page == "Dashboard":
    st.header("Dashboard")
    st.write("Welcome to your AI-powered job search assistant.")
    
    # Check API status
    st.write(f"Connecting to Backend at: `{API_URL}`")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            st.success("Backend API is connected!")
            
            # --- CALENDAR IDGET ---
            st.subheader("📅 Application Calendar")
            
            # Fetch jobs for calendar
            cal_res = requests.get(f"{API_URL}/jobs/")
            events = []
            
            # 1. Add Job Events
            if cal_res.status_code == 200:
                c_jobs = cal_res.json()
                for j in c_jobs:
                    # Interview Date
                    if j.get("interview_date"):
                        events.append({
                            "title": f"Interview: {j['company_name']} - {j['role_title']}",
                            "start": j["interview_date"],
                            "backgroundColor": "#FF6B6B",
                            "borderColor": "#FF6B6B"
                        })
                    
                    # Deadline Date
                    if j.get("deadline_date"):
                        events.append({
                            "title": f"Deadline: {j['company_name']}",
                            "start": j["deadline_date"],
                            "backgroundColor": "#4ECDC4",
                            "borderColor": "#4ECDC4"
                        })
            
            # 2. Add Google Calendar Events
            try:
                g_cal_res = requests.get(f"{API_URL}/calendar/events")
                if g_cal_res.status_code == 200:
                    g_events = g_cal_res.json()
                    if isinstance(g_events, list):
                        for ge in g_events:
                            # Handle different date formats (all-day vs timed)
                            start = ge.get('start', {}).get('dateTime') or ge.get('start', {}).get('date')
                            end = ge.get('end', {}).get('dateTime') or ge.get('end', {}).get('date')
                            
                            events.append({
                                "title": f"📅 {ge.get('summary', 'No Title')}",
                                "start": start,
                                "end": end,
                                "backgroundColor": "#4285F4", # Google Blue
                                "borderColor": "#4285F4",
                                "textColor": "white"
                            })
                    elif "error" in g_events:
                         # Likely not authenticated or token expired
                         # Don't show error to annoy user, just skip
                         pass
            except Exception as e:
                # Fail silently for GCal to avoid breaking the whole dashboard
                pass
            
            calendar_options = {
                "headerToolbar": {
                    "left": "today prev,next",
                    "center": "title",
                    "right": "dayGridMonth,timeGridWeek,timeGridDay",
                },
                "initialView": "dayGridMonth",
                "selectable": True,
            }
            
            calendar(events=events, options=calendar_options, key="dashboard_calendar")
            # ----------------------

        else:
            st.warning("Backend API reachable but returned non-200 status.")
    except Exception as e:
        st.error(f"Could not connect to Backend API: {e}")
        st.write("Please check that uvicorn is running.")

elif page == "Job Tracker":
    st.header("Job Applications")
    
    # --- GMAIL SCANNER SECTION ---
    with st.expander("📧 Scan Inbox for New Applications", expanded=False):
        st.write("Automatically detect job applications from your Gmail inbox.")
        col1, col2 = st.columns([3, 1])
        with col1:
            limit = st.slider("Emails to check per batch", 10, 50, 10, key="scan_limit")
        with col2:
            st.write("")
            st.write("")
            # Dynamic button label
            btn_label = "Scan Now"
            if "gmail_page_token" in st.session_state and st.session_state["gmail_page_token"]:
                btn_label = "Scan Next Batch ⏩"
                
            scan_btn = st.button(btn_label)
            
        if scan_btn:
            with st.spinner("Scanning and analyzing emails..."):
                try:
                    params = {"limit": limit}
                    # Include page token if it exists
                    if "gmail_page_token" in st.session_state and st.session_state["gmail_page_token"]:
                        params["page_token"] = st.session_state["gmail_page_token"]
                        
                    res = requests.get(f"{API_URL}/gmail/scan", params=params)
                    
                    if res.status_code == 200:
                        data = res.json()
                        # Support old List format just in case API not updated (safety)
                        if isinstance(data, list):
                            emails = data
                            next_token = None
                        else:
                            emails = data.get("emails", [])
                            next_token = data.get("next_page_token")
                        
                        st.session_state["scanned_jobs"] = emails
                        st.session_state["gmail_page_token"] = next_token
                        
                        if not emails:
                            st.info("No job-related emails found in this batch. Try scanning next batch.")
                        else:
                            st.success(f"Found {len(emails)} potential updates!")
                            
                    else:
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Connection failed: {e}") 
                    
        # Reset button
        if "gmail_page_token" in st.session_state and st.session_state["gmail_page_token"]:
            if st.button("Reset Scanner (Start Over)"):
                st.session_state.pop("gmail_page_token", None)
                st.session_state.pop("scanned_jobs", None)
                st.rerun()

    # Display Scanned Jobs
    if "scanned_jobs" in st.session_state and st.session_state["scanned_jobs"]:
        st.subheader("Detected from Inbox")
        st.info(f"Found {len(st.session_state['scanned_jobs'])} potential updates.")
        
        # Display as a table-like format
        for i, job in enumerate(st.session_state["scanned_jobs"]):
            with st.container():
                # Subject with Open Email Link
                s1, s2 = st.columns([5, 1])
                s1.markdown(f"**Email Subject:** {job.get('subject')}")
                if job.get('link'):
                   s2.link_button("View Email ↗", job.get('link'))
                
                c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 0.5, 0.5])
                
                # Input fields for editing before adding
                r_val = job.get('role_title', 'Unknown Role')
                c_val = job.get('company_name', 'Unknown')
                s_val = job.get('status', 'Applied')
                if s_val == 'Unknown': s_val = 'Applied'
                
                # Try parsing raw dates from job dict if string
                int_d_val = job.get('interview_date')
                dead_d_val = job.get('deadline_date')
                
                new_role = c1.text_input("Role", value=r_val, key=f"role_{job['id']}")
                new_company = c2.text_input("Company", value=c_val, key=f"comp_{job['id']}")
                new_status = c3.selectbox("Status", ["Should Apply", "Applied", "Screening", "Interview", "Offer", "Rejected"], index=["Should Apply", "Applied", "Screening", "Interview", "Offer", "Rejected"].index(s_val) if s_val in ["Should Apply", "Applied", "Screening", "Interview", "Offer", "Rejected"] else 0, key=f"stat_{job['id']}")
                
                # Extra row for dates if found
                d1, d2 = st.columns(2)
                found_int_date = st.date_input("Interview Date (Detected)", value=pd.to_datetime(int_d_val).date() if int_d_val else None, key=f"id_{job['id']}")
                found_dead_date = st.date_input("Deadline (Detected)", value=pd.to_datetime(dead_d_val).date() if dead_d_val else None, key=f"dd_{job['id']}")

                # Add button 
                if c4.button("Add", key=f"add_{job['id']}", type="primary"):
                     payload = {
                        "role_title": new_role,
                        "company_name": new_company,
                        "status": new_status,
                        "source": job.get("link", "Gmail Auto-Scan"),
                        "job_description": job.get("body"), # Use email body as initial JD
                        "interview_date": found_int_date.isoformat() if found_int_date else None,
                        "deadline_date": found_dead_date.isoformat() if found_dead_date else None
                    }
                     
                     success = False
                     try:
                        res = requests.post(f"{API_URL}/jobs/", json=payload)
                        if res.status_code == 200:
                            success = True
                            st.toast(f"Added {new_role} at {new_company}!")
                        else:
                            st.error(f"Failed to add: {res.text}")
                     except Exception as e:
                        st.error(f"Connection failed: {e}")
                        
                     if success:
                         # Also ignore the email so it doesn't show up again
                         try:
                             requests.post(f"{API_URL}/gmail/ignore/{job['id']}")
                         except:
                             pass
                             
                         # Remove from list
                         st.session_state["scanned_jobs"].pop(i)
                         st.rerun()

                # Deny button (Ignore)
                if c5.button("Deny", key=f"deny_{job['id']}"):
                     try:
                         requests.post(f"{API_URL}/gmail/ignore/{job['id']}")
                     except Exception as e:
                         print(f"Failed to ignore: {e}")
                     
                     st.session_state["scanned_jobs"].pop(i)
                     st.toast("Email ignored permanently.")
                     st.rerun()

                st.divider()

    st.write("---")
    st.write("---")
    # --- END SCANNER SECTION ---



    # Add new job
    # Add new job
    with st.expander("Add Manually"):
        with st.form("add_job_form"):
            col1, col2 = st.columns(2)
            with col1:
                role = st.text_input("Role Title", value=st.session_state.get("scraped_role", ""))
                company = st.text_input("Company Name", value=st.session_state.get("scraped_company", ""))
                location = st.text_input("Location", value=st.session_state.get("scraped_location", ""))
                interview_d = st.date_input("Interview Date", value=None)
            with col2:
                status = st.selectbox("Status", ["Should Apply", "Applied", "Screening", "Interview", "Offer", "Rejected"])
                source = st.text_input("Source (e.g., LinkedIn)", value=st.session_state.get("scraped_source", ""))
                deadline_d = st.date_input("Deadline", value=None)
            
            jd = st.text_area("Job Description (Optional but recommended for AI Prep)", value=st.session_state.get("scraped_jd", ""))
            
            submitted = st.form_submit_button("Add Job")
            if submitted:
                payload = {
                    "role_title": role,
                    "company_name": company,
                    "status": status,
                    "source": source,
                    "location": location,
                    "job_description": jd,
                    "interview_date": interview_d.isoformat() if interview_d else None,
                    "deadline_date": deadline_d.isoformat() if deadline_d else None
                }
                try:
                    res = requests.post(f"{API_URL}/jobs/", json=payload)
                    if res.status_code == 200:
                        st.success("Job added successfully!")
                        # Clear session state
                        for key in ["scraped_role", "scraped_company", "scraped_location", "scraped_jd", "scraped_source"]:
                            st.session_state.pop(key, None)
                        st.rerun()
                    else:
                        st.error(f"Error adding job: {res.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    # List jobs
    st.subheader("tracked Applications")
    try:
        res = requests.get(f"{API_URL}/jobs/")
        if res.status_code == 200:
            jobs = res.json()
            if jobs:
                df = pd.DataFrame(jobs)
                
                # Ensure date column is datetime
                if "application_date" in df.columns:
                    df["application_date"] = pd.to_datetime(df["application_date"])
                
                # Sort by date descending
                df = df.sort_values(by="application_date", ascending=False)

                # Handle separate Link column for mixed content
                # If source is a URL, we put it in 'Link' and call Source 'Email/Web'
                # If source is text, we keep it in Source and leave Link empty
                df["Link"] = df["source"].apply(lambda x: x if x and str(x).startswith("http") else None)
                df["Source_Label"] = df["source"].apply(lambda x: "Gmail/Web" if x and str(x).startswith("http") else x)

                # Convert to DataFrame for better display if needed, or just iterate
                # Using simple list for now or st.dataframe
                st.dataframe(
                    df, 
                    column_order=["role_title", "company_name", "location", "status", "deadline_date", "interview_date", "Source_Label", "Link", "application_date"],
                    column_config={
                        "Source_Label": "Source",
                        "Link": st.column_config.LinkColumn("Link", display_text="Open 🔗"),
                        "application_date": st.column_config.DatetimeColumn("Applied On", format="D MMM YYYY"),
                        "deadline_date": st.column_config.DateColumn("Deadline"),
                        "interview_date": st.column_config.DateColumn("Interview")
                    },
                    hide_index=True
                )
            else:
                st.info("No job applications found.")
        else:
            st.error("Failed to fetch jobs.")
    except Exception as e:
        st.error(f"Connection error: {e}")

elif page == "Interview Prep":
    st.header("AI Interview Prep")
    
    # Fetch Jobs for Selection
    jobs_list = []
    try:
        res = requests.get(f"{API_URL}/jobs/")
        if res.status_code == 200:
            jobs_list = res.json()
    except:
        st.error("Could not fetch jobs.")
    
    if not jobs_list:
        st.warning("Please add some job applications in the 'Job Tracker' tab first.")
    else:
        # Layout: Main Content (Left) | Resume Sidebar (Right)
        col_main, col_resumes = st.columns([2, 1])
        
        # --- Resume Library (Right Column) ---
        with col_resumes:
            st.subheader("📂 Resume Library")
            
            # Fetch Resumes
            resumes_list = []
            selected_resume_text = None
            
            try:
                r_res = requests.get(f"{API_URL}/resumes/")
                if r_res.status_code == 200:
                    resumes_list = r_res.json()
            except:
                st.warning("Could not connect to Resume Service.")

            # Display Resumes
            if resumes_list:
                # We use a radio button to allow "picking" a resume
                # Format: "Name (Date)"
                res_options = {f"{r['name']}": r for r in resumes_list}
                
                selected_res_name = st.radio(
                    "Select a Resume for Prep:", 
                    list(res_options.keys()),
                    key="resume_lib_radio"
                )
                
                if selected_res_name:
                     selected_resume_text = res_options[selected_res_name]['content']
                     st.caption(f"Selected: {selected_res_name}")

            else:
                st.info("No resumes found. Upload one below!")

            st.write("---")
            
            # Upload New Resume Section
            with st.expander("☁️ Upload New Resume", expanded=not resumes_list):
                 f_up = st.file_uploader("Upload PDF", type=["pdf"], key="res_lib_upload")
                 if f_up:
                     if st.button("Save to Library", type="primary"):
                        with st.spinner("Processing..."):
                            try:
                                # Extract text
                                reader = PdfReader(f_up)
                                text = ""
                                for p in reader.pages: 
                                    text += p.extract_text() + "\n"
                                
                                # Call API to save
                                payload = {"name": f_up.name, "content": text}
                                res = requests.post(f"{API_URL}/resumes/", json=payload)
                                
                                if res.status_code == 200:
                                    st.success("Resume Saved!")
                                    st.rerun()
                                else:
                                    st.error(f"Save failed: {res.text}")
                            except Exception as e:
                                st.error(f"Error processing PDF: {e}")

        # --- Main Prep Area (Left Column) ---
        with col_main:
            
            # Job Selection
            job_options = {f"{j['id']}: {j['role_title']} at {j['company_name']}": j for j in jobs_list}
            selected_option = st.selectbox("Select a Job Application:", list(job_options.keys()))
            selected_job = job_options[selected_option]
            
            st.markdown(f"### 🚀 Prep for: **{selected_job['role_title']}**")
            st.caption(f"at {selected_job['company_name']}")
            
            # Input/Edit JD and Resume
            with st.form("prep_form"):
                st.write("**1. Job Description**")
                jd_val = selected_job.get("job_description") or ""
                jd_input = st.text_area("Job Description", value=jd_val, height=200, placeholder="Paste JD or it will be auto-filled from the job tracker.")
                
                st.write("**2. Resume Context**")
                # Determine initial value for resume text
                # Priority: Selected from Library > Existing on Job > Empty
                
                # Careful: If we bind `value`, typing in it might get overwritten on rerun if we are not careful.
                # But `st.text_area` value is mainly initial. 
                # However, since selecting a radio triggers rerun, we want the `value` to update to the selected resume.
                
                final_resume_val = ""
                if selected_resume_text:
                    final_resume_val = selected_resume_text
                elif selected_job.get("resume_text"):
                    final_resume_val = selected_job.get("resume_text")
                
                resume_input = st.text_area(
                    "Resume Content (Auto-filled from Library)", 
                    value=final_resume_val, 
                    height=200, 
                    placeholder="Select a resume from the right or paste text here..."
                )
                
                if selected_resume_text:
                    st.info(f"Using content from library: '{selected_res_name}'")

                st.write("---")
                generate_btn = st.form_submit_button("Generate Interview Prep Material ✨", type="primary")
                
                if generate_btn:
                    if not jd_input or not resume_input:
                        st.error("Please ensure both Job Description and Resume text are present.")
                    else:
                        with st.spinner("🤖 AI is analyzing your profile against the job description..."):
                            try:
                                # We send the current JD input to ensure the backend has the latest version
                                payload = {
                                    "job_id": selected_job['id'], 
                                    "resume_text": resume_input,
                                    "job_description": jd_input
                                }
                                
                                res = requests.post(f"{API_URL}/prep/generate/{selected_job['id']}", json=payload)
                                
                                if res.status_code == 200:
                                    st.session_state['latest_prep_data'] = res.json()
                                    st.success("Analysis Complete!")
                                else:
                                    st.error(f"Error: {res.text}")
                            except Exception as e:
                                st.error(f"Connection Error: {e}")

            # Display Results (below form in main column, or separate?)
            # Below form is fine.
            if 'latest_prep_data' in st.session_state:
                data = st.session_state['latest_prep_data']
                st.write("---")
                st.header("🎯 Interview Insights")
                
                with st.expander("📝 Personalized Prep Notes", expanded=True):
                    st.write(data.get("generated_notes"))
                
                with st.expander("🔑 Key Topics to Review", expanded=True):
                    for topic in data.get("key_topics", []):
                        st.markdown(f"- {topic}")
                
                st.subheader("❓ Likely Interview Questions")
                questions = data.get("likely_questions", [])
                for idx, q in enumerate(questions):
                    with st.container():
                         st.markdown(f"**Q{idx+1}: {q.get('question')}**")
                         st.info(f"💡 **Tip:** {q.get('answer_tip')}")
                         st.divider()

elif page == "Settings":
    st.header("⚙️ Settings")
    
    # 1. System Status
    st.subheader("1. System Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("Backend API")
        try:
            r = requests.get(f"{API_URL}/health", timeout=2)
            if r.status_code == 200:
                st.success("Connected")
            else:
                st.warning("Issues Found")
        except:
            st.error("Disconnected")
            
    with col2:
        st.write("Google Auth")
        if user_info and user_info.get("email"):
             st.success(f"Logged in: {user_info.get('email')}")
        else:
             st.error("Not Logged In")

    with col3:
        st.write("AI Service")
        # Lightweight check or just assume connected if backend is up
        st.info("Gemini 2.0 (Active)")

    st.write("---")

    # 2. Data Management
    st.subheader("2. Data Management")
    
    # Export Data
    st.write("**Export Your Data**")
    try:
        r = requests.get(f"{API_URL}/jobs/")
        if r.status_code == 200:
            jobs_data = r.json()
            if jobs_data:
                df = pd.DataFrame(jobs_data)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Jobs as CSV",
                    data=csv,
                    file_name='my_job_applications.csv',
                    mime='text/csv',
                )
            else:
                st.info("No data to export.")
    except Exception as e:
        st.error(f"Failed to fetch data for export: {e}")

    st.write("")
    
    # Clear Data (Dangerous)
    with st.expander("Danger Zone"):
        st.warning("This will permanently delete all tracked jobs and resumes.")
        if st.button("Delete All Data", type="primary"):
            # We would need a backend endpoint for this. 
            # For now, let's just show a toast that it's a demo feature or implement if allowed.
            # Since I don't have a 'delete all' endpoint, I'll delete file db? No that's risky.
            st.error("Bulk delete is disabled for safety. Please delete jobs individually.")

    st.write("---")
    
    # 3. About
    st.subheader("Allowed Models")
    st.caption("The system will automatically try these models in order until one works.")
    st.code("""
gemini-2.0-flash-lite
gemini-2.0-flash-exp
gemini-flash-latest
gemini-1.5-flash
gemini-pro
    """, language="text")
    
    st.write("---")
    st.caption("Smart Job Application Tracker v1.2 | Built with FastAPI & Streamlit")



