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
    print("\n" + "="*80)
    print("===== /rank ENDPOINT CALLED =====")
    print("="*80)
    
    # --- Load config and mappings ---
    try:
        config = json.loads(config)
        mappings = json.loads(mappings)
        print("✓ Config loaded successfully:")
        print(f"  Weights: {config.get('weights', {})}")
        print(f"✓ Mappings loaded successfully:")
        print(f"  Degree levels: {list(mappings.get('degree_levels', {}).keys())}")
        print(f"  University tiers: {list(mappings.get('university_tiers', {}).keys())}")
    except Exception as e:
        print(f"✗ Error loading config/mappings: {e}")
        raise HTTPException(400, f"Invalid config/mappings: {e}")

    cvs = []

    try:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, cvs_zip.filename)
            with open(zip_path, "wb") as f:
                f.write(await cvs_zip.read())
            print(f"\n✓ Zip file uploaded: {cvs_zip.filename}")
            print(f"  Saved to: {zip_path}")

            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(tmp)
                file_list = z.namelist()
            print(f"✓ Zip extracted successfully")
            print(f"  Files found: {file_list}")

            # --- Extract CVs from files ---
            print(f"\n{'='*80}")
            print("EXTRACTING CVs FROM FILES")
            print(f"{'='*80}")
            
            file_count = 0
            for root, _, files in os.walk(tmp):
                for file in files:
                    if file.lower().endswith((".pdf", ".docx")):
                        file_count += 1
                        file_path = os.path.join(root, file)
                        print(f"\n[{file_count}] Processing: {file}")
                        print("-" * 60)
                        
                        try:
                            # Extract raw text
                            print("  → Extracting text from file...")
                            text = extract_cv_from_file(file_path)
                            text_preview = text[:300].replace('\n', ' ')
                            print(f"  ✓ Text extracted ({len(text)} chars)")
                            print(f"  Preview: {text_preview}...")
                            
                            # Extract structured JSON via Gemini
                            print("  → Calling LLM for structured extraction...")
                            cv_json = extract_structured_cv(text, file)
                            print(f"  ✓ Structured data extracted:")
                            print(f"     Name: {cv_json.get('name', 'N/A')}")
                            print(f"     Education entries: {len(cv_json.get('education', []))}")
                            print(f"     Experience entries: {len(cv_json.get('experience', []))}")
                            print(f"     Publications: {len(cv_json.get('publications', []))}")
                            print(f"     Awards: {len(cv_json.get('awards', []))}")
                            
                            cvs.append(cv_json)
                            print(f"  ✓ CV added to list (Total: {len(cvs)})")
                            
                        except Exception as e:
                            print(f"  ✗ Error processing {file}: {e}")
                            import traceback
                            traceback.print_exc()
                            continue

        print(f"\n{'='*80}")
        print(f"EXTRACTION COMPLETE: {len(cvs)} CVs processed successfully")
        print(f"{'='*80}")

        if len(cvs) < 1:
            print("✗ ERROR: No CVs were successfully processed!")
            raise HTTPException(400, "At least 1 CV required for processing")

        # --- Scoring ---
        print(f"\n{'='*80}")
        print("SCORING CVs")
        print(f"{'='*80}")
        
        ranked = []
        for idx, cv in enumerate(cvs, 1):
            try:
                print(f"\n[{idx}] Scoring: {cv.get('name', 'Unknown')}")
                print("-" * 60)
                
                score = score_cv(cv, config, mappings)
                
                candidate_data = {
                    "name": cv.get("name", "Unknown"),
                    "sys_score": score,
                    "subscores": {
                        "education": cv.get("education_score", 0),
                        "experience": cv.get("experience_score", 0),
                        "publications": cv.get("publications_score", 0),
                        "coherence": cv.get("coherence_score", 0),
                        "awards": cv.get("awards_score", 0),
                    },
                    "explanation": {
                        "summary": f"Candidate with {score:.2f} overall score",
                        "reasons": ["Well-qualified candidate based on assessment criteria"]
                    }
                }
                
                ranked.append(candidate_data)
                print(f"  ✓ Score calculated: {score:.2f}")
                print(f"     Education: {candidate_data['subscores']['education']:.2f}")
                print(f"     Experience: {candidate_data['subscores']['experience']:.2f}")
                print(f"     Publications: {candidate_data['subscores']['publications']:.2f}")
                
            except Exception as e:
                print(f"  ✗ Error scoring CV: {e}")
                import traceback
                traceback.print_exc()
                continue

        # --- Ranking ---
        print(f"\n{'='*80}")
        print("FINAL RANKING")
        print(f"{'='*80}")
        
        ranked.sort(key=lambda x: x["sys_score"], reverse=True)
        
        for i, c in enumerate(ranked, 1):
            print(f"  {i}. {c['name']:<30} Score: {c['sys_score']:.2f}")

        print(f"\n{'='*80}")
        print(f"✓ RANKING COMPLETE - Returning {len(ranked)} candidates")
        print(f"{'='*80}\n")

        response_data = {"ranked_candidates": ranked}
        print(f"Response JSON preview:")
        print(json.dumps(response_data, indent=2)[:500] + "...")
        
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in /rank: {e}")
        raise HTTPException(500, f"Internal server error: {str(e)}")
