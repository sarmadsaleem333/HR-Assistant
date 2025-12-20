import PyPDF2
import re
import os

def parse_pdf_to_cv(file_path):
    # Extract raw text from PDF
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    # Basic parsing (simple heuristics, can improve)
    education = re.findall(r"(B\.Sc|M\.Sc|PhD|Bachelor|Master).*?\n", text, re.I)
    experience = re.findall(r"(?:Worked|Experience|Internship).*?\n", text, re.I)
    publications = re.findall(r"(?:Publication|Paper).*?\n", text, re.I)
    awards = re.findall(r"(?:Award|Honour).*?\n", text, re.I)

    cv_dict = {
        "name": os.path.basename(file_path),
        "education": [{"degree": e.strip(), "university": "Unknown"} for e in education],
        "experience": [{"title": x.strip(), "org": "Unknown"} for x in experience],
        "publications": [{"title": p.strip(), "venue": "Unknown"} for p in publications],
        "awards": [{"title": a.strip()} for a in awards],
    }
    return cv_dict
