import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from backend.app.core.config import settings
import json
import re

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def scrape_job_from_url(url: str):
    """
    Fetches URL content and uses AI to extract job details.
    """
    try:
        # 1. Fetch HTML
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {"error": f"Failed to fetch URL. Status code: {response.status_code}"}
        
        # 2. Parse and Clean Text
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        text = soup.get_text()
        
        # Collapse whitespace
        clean_text = re.sub(r'\s+', ' ', text).strip()
        
        # Truncate to fit context window reasonable limit (e.g., 4000 chars)
        # We focus on the middle/start as main content is usually there.
        content_sample = clean_text[:6000]
        
        # 3. AI Extraction
        prompt = f"""
        Extract job posting details from the following text scraped from a webpage.
        
        URL: {url}
        Text:
        {content_sample}
        
        Extract:
        - role_title
        - company_name
        - location (City, State, Remote, etc)
        - job_description (Summarize if too long, keep key technical details)
        
        Output JSON:
        {{
            "role_title": "...",
            "company_name": "...",
            "location": "...",
            "job_description": "..."
        }}
        """
        
        ai_resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        
        content = ai_resp.choices[0].message.content
        data = json.loads(content)
        data["source"] = url
        return data

    except Exception as e:
        print(f"Scraping error: {e}")
        return {"error": str(e)}
