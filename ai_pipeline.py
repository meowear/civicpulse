import json
from google import genai
from models import ExtractedIssues

# Initialize Gemini Client (Ensure GEMINI_API_KEY is in your environment variables)
client = genai.Client()

SYSTEM_PROMPT = """
You are an expert AI data analyst for the Greater Hyderabad Municipal Corporation (GHMC).
Your task is to analyze unstructured text from news articles and social media and extract actionable civic issues.

For each distinct issue you find in the text, extract the required fields.
Use the following logic for the 0-10 scoring parameters:
- S (Severity): High if it poses immediate physical danger (e.g., open manhole).
- F (Frequency): High if the text mentions multiple complaints or it's a known recurring issue.
- R (Compounding Risk): High if weather or timing makes it worse (e.g., waterlogging before rain).
- D (Duration): High if the text implies it's been ignored for weeks/months.
- P (Population Density): High for crowded areas like Kukatpally, Ameerpet, Secunderabad.

Be precise and objective.
"""

def extract_and_score_issues(scraped_text: str) -> list[dict]:
    print("Sending data to LLM for extraction and scoring...")
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[SYSTEM_PROMPT, f"Analyze the following data and extract civic issues:\n\n{scraped_text}"],
        config={
            'response_mime_type': 'application/json',
            'response_schema': ExtractedIssues,
            'temperature': 0.1, # Keep it deterministic
        },
    )
    
    # Parse the validated JSON output
    data = json.loads(response.text)
    issues = data.get("issues", [])
    
    # Process the final scores and add IDs for the frontend
    processed_issues = []
    for idx, issue in enumerate(issues, start=1):
        # Apply the CivicPulse formula: (S*0.3) + (F*0.25) + (R*0.2) + (D*0.15) + (P*0.1)
        final_score = (
            (issue["S"] * 0.30) + 
            (issue["F"] * 0.25) + 
            (issue["R"] * 0.20) + 
            (issue["D"] * 0.15) + 
            (issue["P"] * 0.10)
        )
        
        issue_dict = issue
        issue_dict["id"] = idx
        issue_dict["impact_score"] = round(final_score, 2)
        processed_issues.append(issue_dict)
        
    return processed_issues
