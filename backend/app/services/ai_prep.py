import google.generativeai as genai
from backend.app.core.config import settings
import json
import os
import time
import random

# Configure Gemini
# Fallback to os.getenv if not in settings, just in case
api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY") or settings.OPENAI_API_KEY
genai.configure(api_key=api_key)

generation_config = {
  "temperature": 0.7,
  "top_p": 1,
  "top_k": 32,
  "max_output_tokens": 4096,
  "response_mime_type": "application/json",
}

# Models to try in order of preference/likelihood of free tier access
MODELS_TO_TRY = [
    "models/gemini-2.0-flash-lite", 
    "models/gemini-2.0-flash-exp", 
    "models/gemini-flash-latest",
    "models/gemini-1.5-flash",
    "models/gemini-pro"
]

def generate_with_retry(model, prompt, retries=3, initial_delay=2):
    for i in range(retries):
        try:
            return model.generate_content(prompt)
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                if i == retries - 1:
                    raise e
                wait_time = initial_delay * (2 ** i) + random.uniform(0, 1)
                print(f"Rate limit hit for {model.model_name}. Retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)
            else:
                raise e

def generate_content_safe(prompt):
    last_exception = None
    for model_name in MODELS_TO_TRY:
        print(f"Trying model: {model_name}...")
        try:
            model = genai.GenerativeModel(
                model_name=model_name, 
                generation_config=generation_config
            )
            # Try generation with retries for transient issues
            response = generate_with_retry(model, prompt, retries=2)
            
            # Check for safety blocks
            if not response.text:
                print(f"Model {model_name} blocked response.")
                continue
                
            return json.loads(response.text)
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            last_exception = e
            # Continue to next model
            
    # If all fail
    if last_exception:
        raise last_exception
    return None

def generate_interview_prep(role_title: str, company: str, job_description: str, resume_text: str):
    prompt = f"""
    You are an expert Interview Coach.
    
    Role: {role_title}
    Company: {company}
    
    Job Description:
    {job_description}
    
    Candidate Resume:
    {resume_text}
    
    Generate interview preparation material in strict JSON format with this structure:
    {{
        "generated_notes": "A summary of how the candidate fits the role and what to emphasize.",
        "key_topics": ["Topic 1", "Topic 2", "Topic 3"],
        "likely_questions": [
            {{
                "question": "Question text?",
                "answer_tip": "Advice on how to answer."
            }}
        ]
    }}
    """
    
    return generate_content_safe(prompt)

def extract_job_details(email_subject: str, email_body: str):
    prompt = f"""
    Analyze the following email and extract job application details.
    
    Email Subject: {email_subject}
    Email Body:
    {email_body[:3000]}
    
    Extract the following fields in JSON format:
    - role_title: The job position (e.g., Software Engineer, Product Manager). If unknown, use "Unknown Role".
    - company_name: The company name. If unknown, use "Unknown Company".
    - status: One of ["Applied", "Screening", "Interview", "Offer", "Rejected", "Unknown"]. Infer from the text.
    - interview_date: If an interview is mentioned, extract the date in ISO 8601 format (YYYY-MM-DD). If no specific date found, or if it's just "schedule a time", return null.
    - deadline_date: If a deadline to apply or complete a task is mentioned, extract the date in ISO 8601 format (YYYY-MM-DD). If none, return null.
    - confidence: A score 0-1 of how confident you are this is a job application email.
    
    Output JSON:
    {{
        "role_title": "...",
        "company_name": "...",
        "status": "...",
        "interview_date": "2024-01-01" or null,
        "deadline_date": "2024-01-01" or null,
        "confidence": 0.95
    }}
    """
    
    try:
        result = generate_content_safe(prompt)
        if result:
            return result
    except:
        pass
        
    # Return fallback if all fail
    return {
        "role_title": "Unknown Role",
        "company_name": "Unknown Company",
        "status": "Unknown",
        "interview_date": None,
        "deadline_date": None,
        "confidence": 0.0
    }
