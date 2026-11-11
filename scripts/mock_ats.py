#!/usr/bin/env python3
"""Mock ATS (applicant tracking system) resume parser and keyword scorer.

Approximates what Workday/Greenhouse/iCIMS-style parsers do: extract contact
info, sections, positions and dates from plain text (e.g. `pdftotext -layout`
output), then score keyword coverage against one or more job profiles.

Usage:
  python3 mock_ats.py resume.txt --jd-profiles jd_profiles.json
  python3 mock_ats.py resume.txt --jd-text posting.txt [--top 25]
"""
import argparse, json, re
from collections import Counter
from datetime import date

MONTHS = {m: i for i, m in enumerate(
    "january february march april may june july august september october november december".split(), 1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
SECTION_NAMES = {"professional experience", "experience", "work experience", "employment", "education",
                 "technical skills", "skills", "projects", "summary", "certifications", "publications",
                 "awards", "languages"}
BULLETS = ("●", "•", "-", "*", "▪", "◦")

# Synonyms a modern parser normalizes before matching. Extend per discipline.
SYN = {
    "rest api": ["rest api", "restful", "api"], "api": ["api"],
    "ci/cd": ["ci/cd", "github actions", "jenkins", "gitlab ci", "azure devops", "pipeline"],
    "kubernetes": ["kubernetes", "k8s", "aks", "eks", "gke"],
    "testing": ["pytest", "testing", "unit test", "selenium", "junit", "test"],
    "observability": ["observability", "application insights", "app insights", "monitoring", "prometheus", "grafana", "datadog"],
    "mentoring": ["mentor", "intern"], "cloud": ["azure", "aws", "gcp", "cloud"],
    "system design": ["system design", "architected", "architecture"],
    "microservices": ["microservice"], "distributed systems": ["distributed system", "distributed"],
    "go": [r"\bgo\b", "golang"], "c": [r"\bc\b(?![#+])"], "c++": ["c++"],
    "incident": ["incident", "on-call", "postmortem"], "etl": ["etl", "elt", "extract"],
    "data pipeline": ["data pipeline", "pipeline"], "power systems": ["power system", "power-flow", "load flow"],
    "load flow": ["load flow", "power flow", "power-flow"], "grid": ["grid"],
    "modeling": ["model"], "bilingual": ["bilingual"], "presenting": ["present"],
    "native-level": ["native", "fluent"], "business-level": ["business-level", "business level"],
}

def has(term, text):
    for p in SYN.get(term, [re.escape(term)]):
        if re.search(p, text): return True
    return False

def parse_date(s, today):
    s = s.strip().lower()
    if s in ("present", "current", "now"): return today
    m = re.match(r"([a-z]+)\.?\s+(\d{4})", s)
    if m and m.group(1) in MONTHS: return date(int(m.group(2)), MONTHS[m.group(1)], 1)
    m = re.match(r"(\d{1,2})/(\d{4})", s)
    if m: return date(int(m.group(2)), int(m.group(1)), 1)
    m = re.match(r"(\d{4})$", s)
    if m: return date(int(m.group(1)), 1, 1)
    return None

DATE = r"(?:[A-Za-z]{3,9}\.? \d{4}|\d{1,2}/\d{4}|\d{4}|Present|Current)"
RANGE = re.compile(rf"({DATE})\s*[–—-]\s*({DATE})\s*$")

def parse(raw, today):
    issues = []
    zw = raw.count("​")
    if zw: issues.append(f"{zw} zero-width characters (usually after bullet glyphs); harmless to modern parsers.")
    lines = [l.replace("​", "").strip() for l in raw.splitlines()]
    lines = [l for l in lines if l]
    prof = {"name": lines[0] if lines else None, "sections": [], "positions": [], "education": [], "skills": []}
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", raw); prof["email"] = m.group(0) if m else None
    m = re.search(r"\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}", raw); prof["phone"] = m.group(0) if m else None
    m = re.search(r"linkedin\.com/in/[\w-]+", raw); prof["linkedin"] = m.group(0) if m else None
    m = re.search(r"\b([A-Z][A-Za-z .]+), ([A-Z]{2})\b", "\n".join(lines[:3])); prof["location"] = m.group(0) if m else None
    sec, employer = None, None
    for l in lines[1:]:
        low = l.lower().strip(" :-")
        if low in SECTION_NAMES:
            sec = low; prof["sections"].append(l); continue
        is_bullet = l.startswith(BULLETS)
        if sec and "experience" in sec or sec == "employment":
            dm = RANGE.search(l)
            if dm and not is_bullet:
                head = re.sub(r"[|,–—-]\s*$", "", l[:dm.start()]).strip(" |")
                s, e = parse_date(dm.group(1), today), parse_date(dm.group(2), today)
                parts = [p.strip() for p in re.split(r"\s*\|\s*", head) if p.strip()]
                head = parts[0] if parts else head
                if re.search(r",\s*[A-Z]{2}\b", l[:dm.start()]):  # "Company, City, ST | dates" = employer line
                    employer = head.split(",")[0]
                    prof["positions"].append({"employer": employer, "title": None, "start": s, "end": e, "bullets": 0, "hdr": True})
                else:
                    prof["positions"].append({"employer": employer, "title": head, "start": s, "end": e, "bullets": 0})
            elif is_bullet and prof["positions"]:
                prof["positions"][-1]["bullets"] += 1
            elif prof["positions"] and prof["positions"][-1].get("hdr") and prof["positions"][-1]["title"] is None:
                prof["positions"][-1]["title"] = l
        elif sec == "education":
            prof["education"].append(l)
        elif sec in ("technical skills", "skills") and ":" in l:
            prof["skills"] += [x.strip() for x in re.split(r",(?![^()]*\))", l.split(":", 1)[1]) if x.strip()]
    pos = [p for p in prof["positions"] if not (p.get("hdr") and p["title"] is None)]
    if not pos: issues.append("No positions parsed: put dates on the same line as the title or employer, e.g. 'Title | Jan 2023 – Present'.")
    prof["positions"] = pos
    rng = sorted((p["start"], p["end"]) for p in pos if p["start"] and p["end"])
    total, cur = 0, None
    for s, e in rng:
        if cur and s <= cur[1]: cur = (cur[0], max(cur[1], e))
        else:
            if cur: total += (cur[1] - cur[0]).days
            cur = (s, e)
    if cur: total += (cur[1] - cur[0]).days
    prof["years"] = round(total / 365.25, 1)
    edu = " ".join(prof["education"]).lower()
    prof["degree"] = next((d for d in ("doctor", "phd", "master", "bachelor", "associate") if d in edu), None)
    y = re.search(r"\b(19|20)\d{2}\b", edu); prof["grad_year"] = y.group(0) if y else None
    if prof["degree"] and not prof["grad_year"]:
        issues.append("No graduation year: degree captured, but 'graduated after' / years-since-degree filters can't use it.")
    bl = [l for l in lines if l.startswith(BULLETS)]
    prof["bullets_total"] = len(bl)
    prof["quantified"] = sum(1 for l in bl if re.search(r"\d|hourly|daily|weekly", l))
    if bl and prof["quantified"] / len(bl) < 0.4:
        issues.append(f"Only {prof['quantified']}/{len(bl)} bullets contain a number or outcome; aim for 40-60%+.")
    return prof, issues

STOP = set("""a an the and or of to in for with on at by from as is are be this that will you your our we
team work experience years year strong senior engineer software requirements nice to have ability skills including using plus etc must have nice role
responsibilities requirements qualifications preferred required knowledge understanding """.split())

def jd_from_text(text, top):
    t = text.lower()
    phrases = re.split(r"[,.;:()\n]|\band\b|\bor\b", t)
    grams, bigrams = Counter(), Counter()
    for ph in phrases:
        w = [x for x in re.findall(r"[a-z][a-z0-9+#/-]*", ph) if x not in STOP and len(x) > 1]
        grams.update(w)
        bigrams.update(f"{a} {b}" for a, b in zip(w, w[1:]))
    # keep bigrams that recur or are known compound terms; otherwise single words
    terms = [b for b, c in bigrams.most_common() if c > 1 or b in SYN][: top // 3]
    terms += [g for g, _ in grams.most_common() if g not in " ".join(terms)]
    terms = terms[:top]
    half = max(1, len(terms) // 2)
    return {"Pasted job description": {"required": terms[:half], "preferred": terms[half:]}}

def score(text, jd):
    t = text.lower()
    req = {k: has(k, t) for k in jd.get("required", [])}
    pref = {k: has(k, t) for k in jd.get("preferred", [])}
    r = sum(req.values()) / len(req) if req else 1
    p = sum(pref.values()) / len(pref) if pref else 1
    return round(70 * r + 30 * p), req, pref

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("resume")
    ap.add_argument("--jd-profiles", help="JSON of {name: {required:[...], preferred:[...]}}")
    ap.add_argument("--jd-text", help="plain-text job posting to extract keywords from")
    ap.add_argument("--top", type=int, default=24)
    ap.add_argument("--today", help="YYYY-MM-DD used for 'Present' (default: today)")
    a = ap.parse_args()
    today = date.fromisoformat(a.today) if a.today else date.today()
    text = open(a.resume, encoding="utf-8").read()
    prof, issues = parse(text, today)
    print("PARSED PROFILE")
    for k in ("name", "email", "phone", "location", "linkedin"):
        print(f"  {k:10}: {prof[k] or '-- NOT FOUND --'}")
    print(f"  sections  : {', '.join(prof['sections']) or '-- none detected --'}")
    print(f"  degree    : {prof['degree']} | grad year: {prof['grad_year'] or '-- not found --'}")
    print(f"  experience: {prof['years']} yrs (computed from dates)")
    for p in prof["positions"]:
        e = "Present" if p["end"] == today else (p["end"].strftime("%b %Y") if p["end"] else "?")
        s = p["start"].strftime("%b %Y") if p["start"] else "?"
        print(f"    - {p['title']} @ {p['employer']}  {s} – {e}  ({p['bullets']} bullets)")
    print(f"  skills    : {len(prof['skills'])} extracted")
    print(f"  quantified bullets: {prof['quantified']}/{prof['bullets_total']}")
    print("PARSE NOTES")
    for i in issues or ["none"]: print("  ! " + i)
    jds = {}
    if a.jd_profiles: jds.update(json.load(open(a.jd_profiles)))
    if a.jd_text: jds.update(jd_from_text(open(a.jd_text, encoding="utf-8").read(), a.top))
    if jds:
        print("KEYWORD MATCH (70% required / 30% preferred)")
        for name, jd in jds.items():
            s, req, pref = score(text, jd)
            print(f"  [{s:3}/100] {name}")
            print(f"           missing required : {', '.join(k for k, v in req.items() if not v) or 'none'}")
            print(f"           missing preferred: {', '.join(k for k, v in pref.items() if not v) or 'none'}")

if __name__ == "__main__":
    main()
