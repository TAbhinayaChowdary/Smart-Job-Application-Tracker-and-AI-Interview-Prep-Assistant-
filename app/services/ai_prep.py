from fastapi import APIRouter, HTTPException, status
from app.models.schemas import AIPrepRequest, PrepTipsResponse
from app.core.config import settings
from app.core.database import mock_get_user_resume, MOCK_DB_STORE 
import json
import random

# --- MOCK OPENAI CLIENT ---
class MockOpenAIClient:
    """
    Simulates the OpenAI API call, returning structured JSON response based on JD analysis.
    In a real app, this would instantiate the official OpenAI client.
    """
    
    def analyze_documents(self, jd_text: str, resume_text: str) -> dict:
        """Mocks the LLM call that performs the Semantic Cross-Document Analysis."""
        
        # Determine the simulated score based on the JD content for demonstration
        if "Senior Backend Engineer" in jd_text:
            # Low match simulation (high requirements, assumed mid-level resume)
            confidence = round(random.uniform(0.40, 0.55), 2) 
            feedback = "The JD requires 5+ years experience and deep AWS expertise, which is lightly documented in your 3-year resume. Focus heavily on quantifying project results and proving cloud proficiency."
        elif "Junior Data Scientist" in jd_text:
            # High match simulation
            confidence = round(random.uniform(0.80, 0.95), 2)
            feedback = "Your profile is highly compatible with this role's statistical modeling focus. Ensure you have clear STAR examples for data cleaning and visualization challenges."
        else:
            confidence = round(random.uniform(0.60, 0.75), 2)
            feedback = "Good compatibility. Focus on demonstrating transferable skills in Git workflows and problem-solving scenarios during the interview."

        return {
            "key_topics_to_revise": [
                "Reviewing the difference between synchronous and asynchronous architectures.",
                "Deep dive into multi-threading and concurrency concepts in Python.",
                "Practice explaining the CI/CD pipeline used in Project X (from your resume)."
            ],
            "likely_behavioral_questions": [
                "Tell me about a time you handled a critical deployment failure.",
                "Describe a complex system bug you solved, and how you tracked it.",
                "How do you handle disagreements with a senior developer on a technical design choice?"
            ],
            "likely_technical_questions": [
                "Explain the CAP theorem and its relevance to database design.",
                "Walk me through the design of a resilient microservice.",
                "What are the benefits of using FastAPI over Flask in a large-scale project?"
            ],
            "match_confidence": confidence,
            "match_feedback": feedback
        }

mock_ai_client = MockOpenAIClient()

# --- API ENDPOINTS ---

router = APIRouter()

@router.post("/prep", response_model=PrepTipsResponse)
async def generate_prep_tips(request: AIPrepRequest):
    """
    Triggers the OpenAI analysis using the JD text associated with the app_id 
    and the user's stored resume text.
    """
    # 1. Retrieve Stored Resume Text
    resume_text = mock_get_user_resume(request.user_id)
    if not resume_text:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User resume not found. Please upload it via the dashboard.")

    # 2. Retrieve Stored JD Text
    app_data = MOCK_DB_STORE['applications'].get(request.app_id)
    if not app_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Application data not found for ID: {request.app_id}.")
    
    jd_text = app_data['jd_text']
    
    # 3. Call the Mocked AI Client
    try:
        raw_tips = mock_ai_client.analyze_documents(jd_text, resume_text)
    except Exception as e:
        # In a real app, this would catch OpenAI client errors (API key invalid, rate limit)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI Service Error during analysis: {e}")

    # 4. Return structured Pydantic response
    return PrepTipsResponse(**raw_tips)
