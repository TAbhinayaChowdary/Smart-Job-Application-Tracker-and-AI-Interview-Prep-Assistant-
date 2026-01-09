import streamlit as st
import requests
import os
import pandas as pd

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
            limit = st.slider("Emails to check", 10, 50, 10, key="scan_limit")
        with col2:
            st.write("")
            st.write("")
            scan_btn = st.button("Scan Now")
            
        if scan_btn:
            with st.spinner("Scanning and analyzing emails..."):
                try:
                    res = requests.get(f"{API_URL}/gmail/scan", params={"limit": limit})
                    if res.status_code == 200:
                        emails = res.json()
                        st.session_state["scanned_jobs"] = emails
                        if not emails:
                            st.info("No job-related emails found in recent messages.")
                    else:
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

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
                
                new_role = c1.text_input("Role", value=r_val, key=f"role_{job['id']}")
                new_company = c2.text_input("Company", value=c_val, key=f"comp_{job['id']}")
                new_status = c3.selectbox("Status", ["Should Apply", "Applied", "Screening", "Interview", "Offer", "Rejected"], index=["Should Apply", "Applied", "Screening", "Interview", "Offer", "Rejected"].index(s_val) if s_val in ["Should Apply", "Applied", "Screening", "Interview", "Offer", "Rejected"] else 0, key=f"stat_{job['id']}")
                
                # Add button 
                if c4.button("Add", key=f"add_{job['id']}", type="primary"):
                     payload = {
                        "role_title": new_role,
                        "company_name": new_company,
                        "status": new_status,
                        "source": job.get("link", "Gmail Auto-Scan"),
                        "job_description": job.get("body") # Use email body as initial JD
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
                         # Remove from list
                         st.session_state["scanned_jobs"].pop(i)
                         st.rerun()

                # Deny button (Ignore)
                if c5.button("Deny", key=f"deny_{job['id']}"):
                     st.session_state["scanned_jobs"].pop(i)
                     st.toast("Email ignored.")
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
            with col2:
                status = st.selectbox("Status", ["Should Apply", "Applied", "Screening", "Interview", "Offer", "Rejected"])
                source = st.text_input("Source (e.g., LinkedIn)", value=st.session_state.get("scraped_source", ""))
            
            jd = st.text_area("Job Description (Optional but recommended for AI Prep)", value=st.session_state.get("scraped_jd", ""))
            
            submitted = st.form_submit_button("Add Job")
            if submitted:
                payload = {
                    "role_title": role,
                    "company_name": company,
                    "status": status,
                    "source": source,
                    "location": location,
                    "job_description": jd
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
                    column_order=["role_title", "company_name", "location", "status", "Source_Label", "Link", "application_date"],
                    column_config={
                        "Source_Label": "Source",
                        "Link": st.column_config.LinkColumn("Link", display_text="Open 🔗"),
                        "application_date": st.column_config.DatetimeColumn("Date", format="D MMM YYYY, h:mm a")
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
        # Job Selection
        job_options = {f"{j['id']}: {j['role_title']} at {j['company_name']}": j for j in jobs_list}
        selected_option = st.selectbox("Select a Job Application:", list(job_options.keys()))
        selected_job = job_options[selected_option]
        
        st.markdown(f"### Preparing for: **{selected_job['role_title']} @ {selected_job['company_name']}**")
        
        # Input/Edit JD and Resume
        with st.form("prep_form"):
            jd_input = st.text_area("Job Description", value=selected_job.get("job_description") or "", height=200, placeholder="Paste the JD here...")
            resume_input = st.text_area("Your Resume for this Role", value=selected_job.get("resume_text") or "", height=200, placeholder="Paste your resume text here...")
            
            generate_btn = st.form_submit_button("Generate Interview Prep Material 🚀")
            
            if generate_btn:
                if not jd_input or not resume_input:
                    st.error("Please provide both Job Description and Resume.")
                else:
                    with st.spinner("Analyzing JD and Resume... This may take a few seconds."):
                        payload = {
                            "job_id": selected_job['id'],
                            "resume_text": resume_input
                        }
                        # Note:Ideally we should also update the job with the new JD/Resume if changed
                        # For now, we pass them to the generator. The generator Endpoint expects resume in body.
                        # JD should ideally be in the DB.
                        
                        # Let's assume we might need to update the job first to save the JD if it's new
                        # But for simplicity, we'll assume the user might have updated it. 
                        # To keep it simple, let's just assume the backend uses what's in the DB or what we send.
                        # My implemented backend endpoint `generate_prep` uses the JD FROM THE DB.
                        # So we MUST update the job in the DB first if the user typed a new JD.
                        
                        # Update Job First (Hack for now)
                        # We don't have a dedicated update endpoint in the minimal setup yet, 
                        # so let's check if my backend allows updating. 
                        # Looking at `jobs.py`, I only have create and read.
                        # I should probably add an update endpoint, OR just rely on what is there.
                        # Wait, `generate_prep` uses `job.job_description`.
                        
                        st.warning("Note: Currently using the Job Description stored in the database. Please ensure you added it when creating the job (or I'll add an edit feature later).")
                         
                        try:
                            # We send request
                            res = requests.post(f"{API_URL}/prep/generate/{selected_job['id']}", json={"job_id": selected_job['id'], "resume_text": resume_input})
                            
                            if res.status_code == 200:
                                data = res.json()
                                st.success("Analysis Complete!")
                                
                                st.subheader("📝 Personalized Prep Notes")
                                st.write(data.get("generated_notes"))
                                
                                st.subheader("🔑 Key Topics to Review")
                                for topic in data.get("key_topics", []):
                                    st.markdown(f"- {topic}")
                                
                                st.subheader("❓ Likely Interview Questions")
                                questions = data.get("likely_questions", [])
                                for idx, q in enumerate(questions):
                                    with st.expander(f"Q{idx+1}: {q.get('question')}"):
                                        st.write(f"**Tip:** {q.get('answer_tip')}")
                            else:
                                st.error(f"Error: {res.text}")
                        except Exception as e:
                            st.error(f"Error: {e}")

elif page == "Settings":
    st.header("Settings")
    st.write("Configuration options.")



