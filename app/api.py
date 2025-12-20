from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import zipfile, tempfile, os, json
from app.scoring import score_cv
from app.llm import generate_explanation
from app.pdf_parser import parse_pdf_to_cv

router = APIRouter()

@router.post("/rank")
async def rank_cvs(
    cvs_zip: UploadFile = File(...),
    config: str = Form(...),
    mappings: str = Form(...)
):
    print("===== /rank endpoint called =====")

    # --- Load config/mappings ---
    try:
        config = json.loads(config)
        mappings = json.loads(mappings)
        print("Config and mappings loaded")
    except Exception as e:
        print("Error parsing config/mappings:", e)
        raise HTTPException(400, f"Invalid config or mappings JSON: {e}")

    cvs = []

    # --- Extract zip ---
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = os.path.join(tmp, cvs_zip.filename)
        with open(zip_path, "wb") as f:
            f.write(await cvs_zip.read())
        print(f"Zip uploaded to: {zip_path}")

        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(tmp)
        print(f"Zip extracted to: {tmp}")

        # --- Parse PDFs to JSON ---
        for root, _, files in os.walk(tmp):
            for file in files:
                if file.lower().endswith(".pdf"):
                    file_path = os.path.join(root, file)
                    cv_dict = parse_pdf_to_cv(file_path)
                    cvs.append(cv_dict)
                    print(f"Parsed PDF CV: {file_path}")

    if len(cvs) < 2:
        print("Error: less than 2 CVs found")
        raise HTTPException(400, "At least 2 CVs required")

    # --- Score and rank ---
    ranked = []
    for cv in cvs:
        score = score_cv(cv, config, mappings)
        ranked.append({"name": cv.get("name"), "sys_score": score, "raw_data": cv})
        print(f"Scored CV: {cv.get('name')} - {score}")

    ranked.sort(key=lambda x: x["sys_score"], reverse=True)

    # --- Explanation ---
    explanation = generate_explanation(ranked[0], ranked[1])
    print("Explanation generated")

    # --- Terminal printing ---
    print("\n========== CV RANKING ==========")
    for i, candidate in enumerate(ranked, 1):
        print(f"{i}. {candidate['name']} - Score: {candidate['sys_score']}")
    print("\n--- Explanation (Top 1 vs Top 2) ---")
    print(explanation)
    print("===================================\n")

    return {"ranked_candidates": ranked, "explanation": explanation}
