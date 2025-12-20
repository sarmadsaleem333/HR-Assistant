import os, json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def extract_structured_cv(text, filename):
    """
    Use Gemini to extract structured CV data according to target JSON schema.
    """
    prompt = f"""
Extract structured CV metadata from the following text.
Output JSON in the format:
{{"name": "...", "education":[{{"degree":"", "field":"", "university":"", "country":"", "start":"", "end":"", "gpa":null, "scale":null}}],
"experience":[{{"title":"", "org":"", "start":"", "end":"", "duration_months":null, "domain":""}}],
"publications":[{{"title":"", "venue":"", "year":null, "type":"", "authors":[], "author_position":null, "journal_if":null, "domain":""}}],
"awards":[{{"title":"", "issuer":"", "year":null, "type":""}}]
}}

CV Filename: {filename}

Text:
{text}
"""
    try:
        resp = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0)
        )
        return json.loads(resp.text)
    except Exception as e:
        print(f"Error extracting CV {filename}: {e}")
        return {"name": filename, "education": [], "experience": [], "publications": [], "awards": []}

def generate_explanation(winner, runner):
    def ev(cv):
        edu = ", ".join(f"{e.get('degree')} from {e.get('university')}" for e in cv.get("education", []))
        exp = ", ".join(f"{x.get('title')} at {x.get('org')}" for x in cv.get("experience", [])[:3])
        return f"Education: {edu} | Experience: {exp}"

    prompt = f"""
WINNER: {winner['name']} (Score: {winner['sys_score']})
{ev(winner['raw_data'])}

RUNNER-UP: {runner['name']} (Score: {runner['sys_score']})
{ev(runner['raw_data'])}

Provide 3 bullet points explaining why the winner ranks higher.
Each bullet should cite specific text from the CVs.
Output as plain text.
"""
    try:
        resp = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0)
        )
        return resp.text.strip()
    except Exception as e:
        return str(e)
