from datetime import datetime

def calculate_months(start=None, end=None):
    try:
        if not start: return 0
        s_dt = datetime.strptime(start[:7], "%Y-%m") if start else datetime.now()
        e_dt = datetime.strptime(end[:7], "%Y-%m") if end else datetime.now()
        return max((e_dt.year - s_dt.year) * 12 + (e_dt.month - s_dt.month), 0)
    except:
        return 0

def score_cv(cv, config, mappings):
    w = config["weights"]
    sw = config["subweights"]
    p = config["policies"]

    # EDUCATION
    best_edu = 0
    for e in cv.get("education", []):
        deg = str(e.get("degree","")).lower()
        d_val = next((v for k,v in mappings["degree_levels"].items() if k in deg), 0.4)
        t_val = mappings["university_tiers"].get(e.get("university","Unknown"), 0.5)
        g_val = e.get("gpa", p.get("missing_values_penalty",0.5))
        best_edu = max(best_edu, d_val*sw["education"]["degree_level"] + t_val*sw["education"]["university_tier"] + g_val*sw["education"]["gpa"])

    # EXPERIENCE
    months, domain = 0, 0
    for exp in cv.get("experience", []):
        months += calculate_months(exp.get("start"), exp.get("end"))
        if p["domain"].lower() in exp.get("domain","").lower():
            domain = 1
    dur_score = min(months / p["min_months_experience_for_bonus"], 1)
    # Handle missing experience subweights
    if "experience" in sw and "duration_months" in sw["experience"]:
        exp_val = dur_score*sw["experience"]["duration_months"] + domain*sw["experience"].get("domain_match", 0.3)
    else:
        # Fallback if no experience subweights defined
        exp_val = dur_score * 0.7 + (domain * 0.3 if domain else 0)

    # PUBLICATIONS
    best_pub = 0
    for pub in cv.get("publications", []):
        venue = pub.get("venue","Unknown")
        best_pub = max(best_pub, next((v for k,v in mappings["journal_impact"].items() if k in venue), 0.1))

    # AWARDS
    awards = min(len(cv.get("awards",[]))*0.5, 1.0)

    # FINAL SCORE
    final = (
        best_edu*10*w["education"] +
        exp_val*10*w["experience"] +
        best_pub*10*w["publications"] +
        awards*10*w.get("awards_other",0) +
        8.0*w.get("coherence",0)
    )
    return round(final, 2)
