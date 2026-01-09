from openai import OpenAI
from backend.app.core.config import settings
import json

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_interview_prep(role_title: str, company: str, job_description: str, resume_test: str):
    prompt = f"""
    You are an expert Interview Coach.
    
    Role: {role_title}
    Company: {company}
    
    Job Description:
    {job_description}
    
    Candidate Resume:
    {resume_test}
    
    Format your response as a valid JSON object with the following structure:
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
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error generating prep: {e}")
        return None

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
    - confidence: A score 0-1 of how confident you are this is a job application email.
    
    Output JSON:
    {{
        "role_title": "...",
        "company_name": "...",
        "status": "...",
        "confidence": 0.95
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Use 3.5 for speed and lower cost on batch ops
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error extracting details: {e}")
        # Return fallback
        return {
            "role_title": "Unknown Role",
            "company_name": "Unknown Company",
            "status": "Unknown",
            "confidence": 0.0
        }
