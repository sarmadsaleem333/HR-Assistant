import pytesseract
from pdf2image import convert_from_path
import docx
import os

def extract_text_from_pdf(file_path):
    text = ""
    try:
        # Convert PDF pages to images for OCR
        images = convert_from_path(file_path)
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"
    except:
        # fallback: text-based PDF parsing (if not scanned)
        import PyPDF2
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    return text

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = "\n".join([p.text for p in doc.paragraphs])
    return text

def extract_cv_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    else:
        return ""
