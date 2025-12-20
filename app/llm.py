import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def generate_explanation(winner, runner):
    def ev(cv):
        edu = ", ".join(f"{e.get('degree')} from {e.get('university')}" for e in cv.get("education", []))
        exp = ", ".join(f"{x.get('title')} at {x.get('org')}" for x in cv.get("experience", [])[:2])
        return f"Education: {edu} | Experience: {exp}"

    prompt = f"""
WINNER: {winner['name']} (Score: {winner['sys_score']})
{ev(winner['raw_data'])}

RUNNER-UP: {runner['name']} (Score: {runner['sys_score']})
{ev(runner['raw_data'])}

Explain clearly why Winner > Runner-up using evidence.
"""

    try:
        r = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0)
        )
        return r.text.strip()
    except Exception as e:
        return str(e)
