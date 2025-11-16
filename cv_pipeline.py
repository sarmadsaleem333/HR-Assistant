import os
import re
from pathlib import Path
from langdetect import detect
from docx import Document
from PIL import Image
import pytesseract
import fitz
import json
from google import genai
from google.genai import types
import dotenv
import unicodedata
from datetime import datetime
import time
from tqdm import tqdm  

dotenv.load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

RAW_DIR = "cvs_data/raw_cvs"
FINAL_JSON = "cvs_data/final/all_cvs.json"
LOG_FILE = "logs/logs.txt"


for d in [RAW_DIR, "cvs_data/final", "logs"]:
    Path(d).mkdir(parents=True, exist_ok=True)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def log_step(message: str):
    """Append message with timestamp to log file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def redact_pii(text):
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[REDACTED_EMAIL]', text)
    text = re.sub(r'\b\d{10,}\b', '[REDACTED_PHONE]', text)
    return text

def normalize_text(text):
    text = unicodedata.normalize("NFKC", text)
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def clean_whitespace(text):
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def extract_text_pdf(path):
    try:
        doc = fitz.open(path)
        full_text = ""
        for page in doc:
            t = page.get_text()
            if t.strip():
                full_text += t
            else:
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                full_text += pytesseract.image_to_string(img, lang="eng")
        return full_text
    except Exception as e:
        return f"ERROR: {e}"

def extract_text_docx(path):
    try:
        doc = Document(path)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        return f"ERROR: {e}"

def detect_language_safe(text):
    try:
        return detect(text)
    except:
        return "unknown"

def calculate_duration_months(start, end):
    try:
        start_date = datetime.strptime(start, "%Y-%m")
        end_date = datetime.now() if end == "currently working" else datetime.strptime(end, "%Y-%m")
        delta = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        return max(delta, 0)
    except:
        return None

# ---------------------- GEMINI PARSING ----------------------
client = genai.Client(api_key=GOOGLE_API_KEY)

def call_gemini_with_retry(prompt, model_primary="gemini-2.0-flash-lite", max_retries=3, wait_times=[1, 2, 4]):
    attempts = 0
    while attempts < max_retries:
        try:
            resp = client.models.generate_content(
                model=model_primary,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0)
            )
            return resp.text.strip()
        except Exception as e:
            if "503" in str(e) or "overloaded" in str(e):
                wait = wait_times[min(attempts, len(wait_times)-1)]
                time.sleep(wait)
                attempts += 1
            else:
                raise e
    try:
        resp = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0)
        )
        return resp.text.strip()
    except:
        return None

def parse_cv_with_gemini(text):
    prompt = f"""
Extract structured CV information in this JSON format:

{{
  "education": [{{"degree":"","field":"","university":"","country":"","start":null,"end":null,"gpa":null,"scale":null}}],
  "experience": [{{"title":"","org":"","start":null,"end":null,"duration_months":null,"domain":""}}],
  "publications": [{{"title":"","venue":"","year":null,"type":"","authors":[],"author_position":null,"journal_if":null,"domain":""}}],
  "awards": [{{"title":"","issuer":"","year":null,"type":""}}]
}}

RULES:
1. For experience, if end date missing, set "end": "currently working".
2. For education, include only Bachelor's or university-level degree or higher.
3. Return ONLY valid JSON.
"""
    raw = call_gemini_with_retry(prompt + text)
    if not raw:
        return {"education": [], "experience": [], "publications": [], "awards": []}
    try:
        return json.loads(raw)
    except:
        c = raw[raw.find("{"): raw.rfind("}")+1]
        c = re.sub(r',\s*([}\]])', r'\1', c)
        try:
            return json.loads(c)
        except:
            return {"education": [], "experience": [], "publications": [], "awards": []}

# ---------------------- MAIN PIPELINE ----------------------
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)  # start fresh

final_data = []
files = os.listdir(RAW_DIR)

for filename in tqdm(files, desc="Processing CVs", ncols=100):
    path = os.path.join(RAW_DIR, filename)
    text = ""

    if filename.endswith(".pdf"):
        text = extract_text_pdf(path)
    elif filename.endswith(".docx"):
        text = extract_text_docx(path)
    else:
        log_step(f"{filename}: unsupported format")
        continue
    log_step(f"{filename}: extraction done")

    if not text.strip() or text.startswith("ERROR"):
        log_step(f"{filename}: extraction failed")
        continue

    if detect_language_safe(text) != "en":
        log_step(f"{filename}: non-English, skipped")
        continue
    log_step(f"{filename}: language check passed")

    text = redact_pii(text)
    text = normalize_text(text)
    text = clean_whitespace(text)
    log_step(f"{filename}: cleaning done")

    structured = parse_cv_with_gemini(text)
    log_step(f"{filename}: parsing done")

    for exp in structured.get("experience", []):
        if exp.get("end") == "currently working" and exp.get("start"):
            exp["duration_months"] = calculate_duration_months(exp["start"], exp["end"])
    log_step(f"{filename}: duration calculation done")

    final_data.append({
        "name": filename,
        **structured
    })
    log_step(f"{filename}: added to final JSON")

with open(FINAL_JSON, "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=2, ensure_ascii=False)
log_step(f"Final JSON saved: {FINAL_JSON}")
log_step(" Pipeline completed successfully!")
