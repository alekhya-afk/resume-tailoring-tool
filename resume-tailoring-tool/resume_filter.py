import argparse
import json
import re
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

SKILL_ALIASES = {
    "AI": ["AI", "artificial intelligence"],
    "Microsoft Copilot": ["Microsoft Copilot", "Microsoft CoPilot", "Copilot"],
    "C++": ["C++", "cpp"],
    "JavaScript": ["JavaScript", "JS"],
    "Machine Learning": ["machine learning", "ML"],
}

DEFAULT_SKILLS = [
    "Python", "Java", "C++", "JavaScript", "SQL", "Git", "GitHub",
    "AI", "Machine Learning", "automation", "ChatGPT", "Claude",
    "Microsoft Copilot", "Zapier", "Notion AI", "dashboard design",
    "Excel", "Power BI", "Tableau", "Pandas", "NumPy",
]

JOB_SECTION_WEIGHTS = {
    "Summary": 1,
    "Responsibilities": 2,
    "Qualifications": 3,
    "Requirements": 3,
    "Preferred Qualifications": 2,
    "Skills": 3,
}

DEFAULT_SELECTION_LIMITS = {
    "Projects": 3,
    "Experience": 2,
    "Additional Experience": 1,
}

DEFAULT_BULLET_LIMIT = 3

# ============================================================
# TEXT / SKILL HELPERS
# ============================================================

def normalize_space(text):
    return re.sub(r"\s+", " ", text).strip()

def skill_terms(skill):
    return SKILL_ALIASES.get(skill, [skill])

def skill_appears_in_text(skill, text):
    """Match a canonical skill or alias as a whole term, case-insensitively."""
    return any(
        re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, re.IGNORECASE)
        for term in skill_terms(skill)
    )

def discover_skills_from_text(text, supported_skills=None):
    supported_skills = supported_skills or DEFAULT_SKILLS
    return [skill for skill in supported_skills if skill_appears_in_text(skill, text)]

# ============================================================
# PARSING
# ============================================================

def parse_colon_sections(path):
    """
    Parse a text file whose section headings end with ':'.
    Lines before the first heading are stored under 'Header'.
    """
    sections = {}
    current_header = "Header"
    sections[current_header] = []

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            if line.endswith(":") and len(line) < 80:
                current_header = line[:-1].strip()
                sections.setdefault(current_header, [])
            else:
                sections.setdefault(current_header, []).append(line)

    if not sections["Header"]:
        sections.pop("Header")
    return sections

def parse_resume(path):
    return parse_colon_sections(path)

def parse_job_description(path):
    """
    Parse colon-style headings when present. If a job description has no
    headings, keep all text under 'Description'.
    """
    parsed = parse_colon_sections(path)
    if len(parsed) == 1 and "Header" in parsed:
        return {"Description": parsed["Header"]}
    return parsed

# ============================================================
# JOB ANALYSIS
# ============================================================

def section_weight(section):
    return JOB_SECTION_WEIGHTS.get(section, 1)

def analyze_job(job_description, supported_skills=None):
    """Return requested skills and section-weighted importance."""
    supported_skills = supported_skills or DEFAULT_SKILLS
    job_skills = []
    skill_weights = {}

    for section, lines in job_description.items():
        for line in lines:
            for skill in supported_skills:
                if skill_appears_in_text(skill, line) and skill not in job_skills:
                    job_skills.append(skill)

    for skill in job_skills:
        weight = 0
        for section, lines in job_description.items():
            for line in lines:
                if skill_appears_in_text(skill, line):
                    weight += section_weight(section)
        skill_weights[skill] = weight

    return job_skills, skill_weights

# ============================================================
# RESUME STRUCTURING
# ============================================================

def looks_like_date(text):
    return bool(
        re.search(
            r"\b(19|20)\d{2}\b|present|current|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec",
            text,
            re.IGNORECASE,
        )
    )

def is_entry_header(section, line):
    parts = [part.strip() for part in line.split("|")]
    if len(parts) < 2:
        return False

    if section in {"Experience", "Additional Experience"}:
        return looks_like_date(parts[-1])
    if section == "Projects":
        return not line.endswith(".")
    return False

def group_resume_entries(section, lines):
    entries = []
    current_entry = None

    for line in lines:
        if is_entry_header(section, line):
            parts = [part.strip() for part in line.split("|")]
            current_entry = {
                "section": section,
                "title": parts[0],
                "organization": (
                    parts[1] if section in {"Experience", "Additional Experience"} else None
                ),
                "dates": parts[-1] if looks_like_date(parts[-1]) else None,
                "technologies": (
                    [x.strip() for x in parts[1].split(",")]
                    if section == "Projects" else []
                ),
                "header_line": line,
                "bullets": [],
                "lines": [line],
            }
            entries.append(current_entry)
        elif current_entry:
            current_entry["bullets"].append(line)
            current_entry["lines"].append(line)

    return entries

# ============================================================
# RESUME ANALYSIS / SCORING
# ============================================================

def find_skill_evidence(resume, job_skills):
    searchable = ["Projects", "Experience", "Additional Experience"]
    evidence = []

    for skill in job_skills:
        for section in searchable:
            for line in resume.get(section, []):
                if skill_appears_in_text(skill, line):
                    evidence.append({"skill": skill, "section": section, "line": line})
    return evidence

def sort_resume_skills(resume_skills, skill_weights):
    return sorted(
        resume_skills,
        key=lambda resume_skill: max(
            (
                weight
                for job_skill, weight in skill_weights.items()
                if skill_appears_in_text(job_skill, resume_skill)
            ),
            default=0,
        ),
        reverse=True,
    )

def score_resume_entries(resume, job_skills, skill_weights):
    searchable = ["Projects", "Experience", "Additional Experience"]
    scored = []

    for section in searchable:
        for entry in group_resume_entries(section, resume.get(section, [])):
            text = " ".join(entry["lines"])
            matched = [s for s in job_skills if skill_appears_in_text(s, text)]
            if matched:
                item = entry.copy()
                item["skills"] = matched
                item["score"] = sum(skill_weights[s] for s in matched)
                scored.append(item)

    return sorted(scored, key=lambda item: item["score"], reverse=True)

def select_best_entries(resume_item_scores, selection_limits=None):
    selection_limits = selection_limits or DEFAULT_SELECTION_LIMITS
    return {
        section: [
            item for item in resume_item_scores if item["section"] == section
        ][:limit]
        for section, limit in selection_limits.items()
    }

def score_entry_bullets(entry, job_skills, skill_weights):
    """10A: score every bullet while preserving the original text."""
    scored = []
    for index, bullet in enumerate(entry.get("bullets", [])):
        matched = [s for s in job_skills if skill_appears_in_text(s, bullet)]
        scored.append({
            "bullet": bullet,
            "skills": matched,
            "score": sum(skill_weights[s] for s in matched),
            "original_index": index,
        })

    return sorted(
        scored,
        key=lambda item: (-item["score"], item["original_index"])
    )

def select_best_bullets(entry, job_skills, skill_weights, limit=DEFAULT_BULLET_LIMIT):
    """
    Keep the strongest bullets. If all bullets score zero, preserve the first
    bullets rather than deleting the entry's content.
    """
    ranked = score_entry_bullets(entry, job_skills, skill_weights)
    if not ranked:
        return []

    positive = [item for item in ranked if item["score"] > 0]
    chosen = positive[:limit] if positive else ranked[:limit]

    # Preserve original resume order in final output.
    return sorted(chosen, key=lambda item: item["original_index"])

def attach_selected_bullets(best_resume_entries, job_skills, skill_weights, bullet_limit):
    result = {}
    for section, entries in best_resume_entries.items():
        result[section] = []
        for entry in entries:
            updated = entry.copy()
            updated["ranked_bullets"] = score_entry_bullets(
                entry, job_skills, skill_weights
            )
            updated["selected_bullets"] = select_best_bullets(
                entry, job_skills, skill_weights, bullet_limit
            )
            result[section].append(updated)
    return result

# ============================================================
# TAILORED RESUME GENERATION
# ============================================================

def build_tailored_resume(resume, sorted_resume_skills, best_resume_entries):
    tailored = {
        section: lines.copy()
        for section, lines in resume.items()
        if section not in best_resume_entries
    }

    if "Skills" in tailored:
        tailored["Skills"] = sorted_resume_skills

    for section, entries in best_resume_entries.items():
        output_lines = []
        for entry in entries:
            output_lines.append(entry["header_line"])
            selected = entry.get("selected_bullets")
            if selected is None:
                output_lines.extend(entry["bullets"])
            else:
                output_lines.extend(item["bullet"] for item in selected)
        # Keep original content when no supported keywords match this section.
        tailored[section] = output_lines if entries else resume.get(section, []).copy()

    return tailored

def export_tailored_resume(tailored_resume, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for section, lines in tailored_resume.items():
            f.write(f"{section}:\n")
            for line in lines:
                f.write(f"{line}\n")
            f.write("\n")

# ============================================================
# SAFE BULLET REWRITE SUPPORT (10B)
# ============================================================

def build_rewrite_requests(best_resume_entries, job_skills):
    """
    Create rewrite requests for a future LLM/API layer.
    This project intentionally does not fabricate an AI rewrite locally.
    Each request includes only the original factual bullet and target skills.
    """
    requests = []
    for section, entries in best_resume_entries.items():
        for entry in entries:
            for item in entry.get("selected_bullets", []):
                requests.append({
                    "section": section,
                    "entry": entry["title"],
                    "original_bullet": item["bullet"],
                    "matched_skills": item["skills"],
                    "instruction": (
                        "Rewrite for clarity and job relevance using only facts "
                        "present in the original bullet. Do not add metrics, tools, "
                        "responsibilities, outcomes, or experience."
                    ),
                    "job_skills": job_skills,
                })
    return requests

def export_rewrite_requests(requests, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(requests, f, indent=2)

# ============================================================
# REPORTING
# ============================================================

def create_job_match_report(
    job_skills,
    skill_weights,
    known_skills,
    evidence_matches,
    best_resume_entries,
    tailored_resume,
    tailored_resume_path,
):
    evidence_skills = {match["skill"] for match in evidence_matches}
    explicit, elsewhere, missing = [], [], []

    for skill in job_skills:
        if any(skill_appears_in_text(skill, known) for known in known_skills):
            explicit.append(skill)
        elif skill in evidence_skills:
            elsewhere.append(skill)
        else:
            missing.append(skill)

    found = set(explicit) | set(elsewhere)
    requested_weight = sum(skill_weights.values())
    found_weight = sum(skill_weights[s] for s in found)
    percentage = (found_weight / requested_weight * 100) if requested_weight else 0

    return {
        "match_percentage": round(percentage, 1),
        "weight_coverage": {"found": found_weight, "requested": requested_weight},
        "job_skills": job_skills,
        "skill_weights": skill_weights,
        "explicit_skill_matches": explicit,
        "evidence_elsewhere": elsewhere,
        "not_found": missing,
        "selected_entries": best_resume_entries,
        "tailored_resume": tailored_resume,
        "tailored_resume_path": str(tailored_resume_path),
    }

def print_job_match_report(report):
    coverage = report["weight_coverage"]
    print("\n=== JOB MATCH REPORT ===")
    print(
        f"Overall match: {report['match_percentage']:.1f}% "
        f"({coverage['found']}/{coverage['requested']} weighted points)"
    )
    print("Requested skills:", ", ".join(report["job_skills"]) or "None detected")
    print("Explicit matches:", ", ".join(report["explicit_skill_matches"]) or "None")
    print("Evidence elsewhere:", ", ".join(report["evidence_elsewhere"]) or "None")
    print("Not found:", ", ".join(report["not_found"]) or "None")
    print("Tailored resume:", report["tailored_resume_path"])

    print("\nSelected entries and bullets:")
    for section, entries in report["selected_entries"].items():
        print(f"\n{section}:")
        for entry in entries:
            print(f"- {entry['title']} | entry score {entry['score']}")
            for bullet in entry.get("ranked_bullets", []):
                skills = ", ".join(bullet["skills"]) or "no keyword match"
                print(f"  {bullet['score']} | {skills} | {bullet['bullet']}")

def export_report(report, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        coverage = report["weight_coverage"]
        f.write("JOB MATCH REPORT\n")
        f.write("================\n")
        f.write(
            f"Overall match: {report['match_percentage']:.1f}% "
            f"({coverage['found']}/{coverage['requested']} weighted points)\n\n"
        )
        f.write("Requested skills: " + ", ".join(report["job_skills"]) + "\n")
        f.write("Explicit matches: " + (", ".join(report["explicit_skill_matches"]) or "None") + "\n")
        f.write("Evidence elsewhere: " + (", ".join(report["evidence_elsewhere"]) or "None") + "\n")
        f.write("Not found: " + (", ".join(report["not_found"]) or "None") + "\n\n")

        f.write("Skill weights:\n")
        for skill, weight in report["skill_weights"].items():
            f.write(f"- {skill}: {weight}\n")

        f.write("\nSelected entries:\n")
        for section, entries in report["selected_entries"].items():
            f.write(f"\n{section}:\n")
            for entry in entries:
                f.write(f"- {entry['title']} | score {entry['score']}\n")
                for bullet in entry.get("selected_bullets", []):
                    skills = ", ".join(bullet["skills"]) or "no keyword match"
                    f.write(f"  {bullet['score']} | {skills} | {bullet['bullet']}\n")

def export_report_json(report, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

# ============================================================
# VALIDATION
# ============================================================

def validate_inputs(resume_path, job_path):
    for path, label in [(resume_path, "resume"), (job_path, "job description")]:
        if not Path(path).is_file():
            raise FileNotFoundError(f"Could not find {label} file: {path}")

# ============================================================
# MAIN / CLI
# ============================================================

def build_parser():
    parser = argparse.ArgumentParser(
        description="Tailor a master resume to a job description."
    )
    parser.add_argument("--resume", default="resume.txt", help="Master resume text file")
    parser.add_argument("--job", default="job_description.txt", help="Job description text file")
    parser.add_argument("--output-dir", default="output", help="Directory for generated files")
    parser.add_argument(
        "--bullet-limit",
        type=int,
        default=DEFAULT_BULLET_LIMIT,
        help="Maximum bullets kept per selected entry",
    )
    return parser

def run_pipeline(resume_path, job_path, output_dir, bullet_limit=DEFAULT_BULLET_LIMIT):
    validate_inputs(resume_path, job_path)
    if bullet_limit < 1:
        raise ValueError("bullet_limit must be at least 1")

    resume = parse_resume(resume_path)
    job_description = parse_job_description(job_path)

    job_skills, skill_weights = analyze_job(job_description)
    known_skills = resume.get("Skills", [])
    evidence = find_skill_evidence(resume, job_skills)
    sorted_skills = sort_resume_skills(known_skills, skill_weights)

    entry_scores = score_resume_entries(resume, job_skills, skill_weights)
    best_entries = select_best_entries(entry_scores)
    best_entries = attach_selected_bullets(
        best_entries, job_skills, skill_weights, bullet_limit
    )

    tailored = build_tailored_resume(resume, sorted_skills, best_entries)

    output_dir = Path(output_dir)
    tailored_path = output_dir / "tailored_resume.txt"
    report_path = output_dir / "job_match_report.txt"
    report_json_path = output_dir / "job_match_report.json"
    rewrite_path = output_dir / "rewrite_requests.json"

    export_tailored_resume(tailored, tailored_path)

    report = create_job_match_report(
        job_skills,
        skill_weights,
        known_skills,
        evidence,
        best_entries,
        tailored,
        tailored_path,
    )
    export_report(report, report_path)
    export_report_json(report, report_json_path)

    rewrite_requests = build_rewrite_requests(best_entries, job_skills)
    export_rewrite_requests(rewrite_requests, rewrite_path)

    print_job_match_report(report)
    print(f"\nReport: {report_path}")
    print(f"JSON report: {report_json_path}")
    print(f"Safe rewrite requests: {rewrite_path}")
    return report

def main():
    args = build_parser().parse_args()
    try:
        run_pipeline(args.resume, args.job, args.output_dir, args.bullet_limit)
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}")

if __name__ == "__main__":
    main()
