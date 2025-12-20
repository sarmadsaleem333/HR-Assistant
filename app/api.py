from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import tempfile, zipfile, os, json
from app.parser import extract_cv_from_file
from app.scoring import score_cv
from app.llm import extract_structured_cv, generate_explanation

router = APIRouter()

@router.post("/rank")
async def rank_cvs(
    cvs_zip: UploadFile = File(...),
    config: str = Form(...),
    mappings: str = Form(...)
):
    print("===== /rank endpoint called =====")
    
    # --- Load config and mappings ---
    try:
        config = json.loads(config)
        mappings = json.loads(mappings)
        print("Config & mappings loaded successfully")
    except Exception as e:
        raise HTTPException(400, f"Invalid config/mappings: {e}")

    cvs = []

    with tempfile.TemporaryDirectory() as tmp:
        zip_path = os.path.join(tmp, cvs_zip.filename)
        with open(zip_path, "wb") as f:
            f.write(await cvs_zip.read())
        print(f"Zip uploaded to {zip_path}")

        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(tmp)
        print(f"Zip extracted to: {tmp}")

        # --- Extract CVs from files ---
        for root, _, files in os.walk(tmp):
            for file in files:
                if file.lower().endswith((".pdf", ".docx")):
                    file_path = os.path.join(root, file)
                    print(f"\n--- Parsing file: {file_path} ---")
                    
                    # Extract raw text
                    text = extract_cv_from_file(file_path)
                    print(f"Raw text extracted (first 500 chars):\n{text[:500]}...\n")
                    
                    # Extract structured JSON via Gemini
                    cv_json = extract_structured_cv(text, file)
                    print(f"Structured JSON returned:\n{json.dumps(cv_json, indent=2)}\n")
                    
                    cvs.append(cv_json)

    if len(cvs) < 2:
        raise HTTPException(400, "At least 2 CVs required")

    # --- Scoring ---
    ranked = []
    for cv in cvs:
        score = score_cv(cv, config, mappings)
        ranked.append({"name": cv.get("name", "Unknown"), "sys_score": score, "raw_data": cv})
        print(f"CV scored: {cv.get('name', 'Unknown')} -> {score}")

    # --- Ranking ---
    ranked.sort(key=lambda x: x["sys_score"], reverse=True)
    print("\nCVs sorted by score:")
    for i, c in enumerate(ranked, 1):
        print(f"{i}. {c['name']} - Score: {c['sys_score']}")

    # --- Explanation ---
    explanation = generate_explanation(ranked[0], ranked[1])
    print("\nExplanation (Top 1 vs Top 2):")
    print(explanation)

    print("\n===== /rank endpoint completed =====")

    return {"ranked_candidates": ranked, "explanation": explanation}
