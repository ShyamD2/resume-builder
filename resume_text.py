"""
resume_text.py
Plain-text (ATS-friendly) export and a basic resume "score" checker.
"""

from resume_data import ResumeData


def to_ats_text(data: ResumeData) -> str:
    """Renders the resume as clean plain text - ideal for ATS systems that
    parse resumes as raw text, and for pasting into online application forms."""
    lines = []
    p = data.personal

    lines.append(p.full_name or "Your Name")
    if p.title:
        lines.append(p.title)
    contact_bits = [v for v in [p.email, p.phone, p.location, p.linkedin, p.website, p.github] if v]
    if contact_bits:
        lines.append(" | ".join(contact_bits))
    lines.append("")

    if data.summary:
        lines.append("SUMMARY")
        lines.append(data.summary)
        lines.append("")

    if data.experience:
        lines.append("EXPERIENCE")
        for e in data.experience:
            header = f"{e.role} — {e.company}" if e.role or e.company else ""
            date_range = f"{e.start_date} - {e.end_date}" if e.start_date or e.end_date else ""
            line = header + (f" ({e.location})" if e.location else "")
            if date_range:
                line += f"  [{date_range}]"
            lines.append(line)
            for b in e.bullets:
                if b.strip():
                    lines.append(f"  - {b}")
            lines.append("")

    if data.projects:
        lines.append("PROJECTS")
        for pr in data.projects:
            header = pr.name + (f" ({pr.tech_stack})" if pr.tech_stack else "")
            lines.append(header)
            if pr.description:
                lines.append(f"  {pr.description}")
            for b in pr.bullets:
                if b.strip():
                    lines.append(f"  - {b}")
            if pr.link:
                lines.append(f"  Link: {pr.link}")
            lines.append("")

    if data.education:
        lines.append("EDUCATION")
        for ed in data.education:
            degree_line = f"{ed.degree} {ed.field_of_study}".strip()
            header = f"{degree_line} — {ed.institution}" if ed.institution else degree_line
            date_range = f"{ed.start_date} - {ed.end_date}" if ed.start_date or ed.end_date else ""
            line = header + (f" ({ed.location})" if ed.location else "")
            if date_range:
                line += f"  [{date_range}]"
            if ed.gpa:
                line += f"  GPA: {ed.gpa}"
            lines.append(line)
            for b in ed.bullets:
                if b.strip():
                    lines.append(f"  - {b}")
            lines.append("")

    if data.skills:
        lines.append("SKILLS")
        for sg in data.skills:
            prefix = f"{sg.category}: " if sg.category else ""
            lines.append(f"  {prefix}{', '.join(sg.items)}")
        lines.append("")

    if data.certifications:
        lines.append("CERTIFICATIONS")
        for c in data.certifications:
            meta = " — ".join(filter(None, [c.issuer, c.date]))
            line = c.name + (f", {meta}" if meta else "")
            if c.credential_id:
                line += f" (ID: {c.credential_id})"
            lines.append(f"  - {line}")
        lines.append("")

    if data.languages:
        lines.append("LANGUAGES")
        line = ", ".join(f"{l.language} ({l.proficiency})" if l.proficiency else l.language
                          for l in data.languages)
        lines.append(f"  {line}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


WEAK_VERBS = {"helped", "worked on", "responsible for", "did", "handled", "was involved in", "assisted with"}
STRONG_VERB_EXAMPLES = ["Led", "Built", "Designed", "Launched", "Optimized", "Reduced",
                         "Increased", "Architected", "Delivered", "Automated", "Spearheaded"]


def analyze_resume(data: ResumeData) -> dict:
    """A lightweight heuristic check - not a substitute for a real ATS, but
    flags common resume issues: missing sections, weak language, length, etc."""
    issues = []
    tips = []
    score = 100

    p = data.personal
    if not p.full_name:
        issues.append("Missing full name.")
        score -= 10
    if not p.email:
        issues.append("Missing email address.")
        score -= 8
    if not p.phone:
        tips.append("Consider adding a phone number.")
        score -= 3
    if not data.summary:
        tips.append("Add a 2-3 sentence professional summary at the top.")
        score -= 5
    elif len(data.summary.split()) < 15:
        tips.append("Your summary is quite short — aim for 30-50 words.")
        score -= 2

    if not data.experience:
        issues.append("No work experience listed.")
        score -= 15
    else:
        total_bullets = sum(len(e.bullets) for e in data.experience)
        if total_bullets == 0:
            issues.append("Experience entries have no bullet points describing impact.")
            score -= 10

        weak_count = 0
        no_number_count = 0
        for e in data.experience:
            for b in e.bullets:
                low = b.lower()
                if any(low.startswith(w) for w in WEAK_VERBS):
                    weak_count += 1
                if not any(ch.isdigit() for ch in b):
                    no_number_count += 1
        if weak_count:
            tips.append(
                f"{weak_count} bullet(s) start with a weak phrase (e.g. 'responsible for'). "
                f"Try strong action verbs instead: {', '.join(STRONG_VERB_EXAMPLES[:5])}..."
            )
            score -= min(weak_count * 2, 10)
        if no_number_count and total_bullets:
            ratio = no_number_count / total_bullets
            if ratio > 0.6:
                tips.append("Most bullet points have no numbers. Quantify impact where possible "
                             "(e.g. '30% faster', '$2M saved', '10k users').")
                score -= 5

    if not data.education:
        tips.append("No education section — add it unless deliberately omitted.")
        score -= 3

    if not data.skills:
        tips.append("Add a Skills section — many ATS systems keyword-match against it.")
        score -= 8

    word_count = len(to_ats_text(data).split())
    if word_count < 150:
        tips.append("Resume content looks thin — aim for enough detail to fill about one page.")
        score -= 5
    elif word_count > 900:
        tips.append("Resume content is lengthy — consider trimming to fit 1-2 pages.")
        score -= 3

    score = max(0, min(100, score))
    return {"score": score, "issues": issues, "tips": tips, "word_count": word_count}
