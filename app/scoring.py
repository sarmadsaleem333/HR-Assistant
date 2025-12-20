from datetime import datetime

def calculate_months(start=None, end=None):
    try:
        if not start: return 0
        s_dt = datetime.strptime(start[:7], "%Y-%m") if '-' in start else datetime.strptime(start, "%m/%Y")
        if not end or end.lower() in ["present", "now", "current", "currently working"]:
            e_dt = datetime.now()
        else:
            e_dt = datetime.strptime(end[:7], "%Y-%m") if '-' in end else datetime.strptime(end, "%m/%Y")
        return max((e_dt.year - s_dt.year) * 12 + (e_dt.month - s_dt.month), 0)
    except:
        return 0

def score_cv(cv, config, mappings):
    w = config["weights"]
    sw = config["subweights"]
    p = config["policies"]

    # Education
    best_edu = 0
    for e in cv.get("education", []):
        deg = str(e.get("degree", "")).lower()
        d_val = next((v for k, v in mappings["degree_levels"].items() if k in deg), 0.4)
        t_val = mappings["university_tiers"].get(e.get("university"), 0.5)
        g_val = 1.0  # PDF parser has no GPA
        best_edu = max(best_edu, d_val*sw["education"]["degree_level"] + t_val*sw["education"]["university_tier"] + g_val*sw["education"]["gpa"])

    # Experience
    months, domain = 0, 0
    for exp in cv.get("experience", []):
        months += calculate_months()
        if p["target_domain"].lower() in exp.get("title","").lower():
            domain = 1
    dur_score = min(months / p["min_months_experience"], 1)
    exp_val = dur_score*sw["experience"]["duration_months"] + domain*sw["experience"]["domain_match"]

    # Publications
    best_pub = 0
    for pub in cv.get("publications", []):
        venue = pub.get("venue","Unknown")
        best_pub = max(best_pub, next((v for k,v in mappings["journal_impact"].items() if k in venue), 0.1))

    # Awards
    awards = min(len(cv.get("awards", []))*0.5, 1.0)

    final = (
        best_edu*10*w["education"] +
        exp_val*10*w["experience"] +
        best_pub*10*w["publications"] +
        awards*10*w["awards"] +
        8.0*w["coherence"]
    )
    return round(final, 2)
