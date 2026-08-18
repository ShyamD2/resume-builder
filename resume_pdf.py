"""
resume_pdf.py
Renders a ResumeData object into a polished PDF using reportlab.

Templates:
- Modern   : accent-colored header band, clean section rules, single column
- Classic  : traditional serif, centered header, no color (ATS-safe)
- Minimal  : lots of whitespace, light rules, sans-serif
- Sidebar  : two-column layout with colored sidebar for contact/skills
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage, KeepTogether, Frame, PageTemplate, BaseDocTemplate,
    NextPageTemplate, FrameBreak
)
from reportlab.pdfbase.pdfmetrics import stringWidth

from resume_data import ResumeData


def hex_to_color(hex_str: str) -> colors.Color:
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    r, g, b = (int(hex_str[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colors.Color(r, g, b)


def darken(color: colors.Color, factor: float = 0.7) -> colors.Color:
    return colors.Color(color.red * factor, color.green * factor, color.blue * factor)


def _bullets_flowable(bullets, style):
    from reportlab.platypus import ListFlowable, ListItem
    items = [ListItem(Paragraph(b, style), leftIndent=10) for b in bullets if b.strip()]
    if not items:
        return None
    return ListFlowable(items, bulletType="bullet", start="•", leftIndent=14,
                         bulletFontSize=8, spaceBefore=1, spaceAfter=1)


def _contact_line(personal, separator=" | ") -> str:
    parts = []
    if personal.email:
        parts.append(personal.email)
    if personal.phone:
        parts.append(personal.phone)
    if personal.location:
        parts.append(personal.location)
    if personal.linkedin:
        parts.append(personal.linkedin)
    if personal.website:
        parts.append(personal.website)
    if personal.github:
        parts.append(personal.github)
    return separator.join(parts)


# ---------------------------------------------------------------------------
# Base style factory
# ---------------------------------------------------------------------------

def _base_styles(accent: colors.Color, body_font="Helvetica", heading_font="Helvetica-Bold"):
    styles = getSampleStyleSheet()
    s = {}
    s["name"] = ParagraphStyle("NameStyle", fontName=heading_font, fontSize=24,
                                leading=28, textColor=colors.HexColor("#111111"))
    s["title"] = ParagraphStyle("TitleStyle", fontName=body_font, fontSize=12.5,
                                 leading=16, textColor=accent)
    s["contact"] = ParagraphStyle("ContactStyle", fontName=body_font, fontSize=9,
                                   leading=12, textColor=colors.HexColor("#444444"))
    s["section"] = ParagraphStyle("SectionStyle", fontName=heading_font, fontSize=11.5,
                                   leading=14, textColor=accent, spaceBefore=10, spaceAfter=4,
                                   letterSpacing=0.6)
    s["body"] = ParagraphStyle("BodyStyle", fontName=body_font, fontSize=9.6,
                                leading=13.4, textColor=colors.HexColor("#222222"))
    s["bullet"] = ParagraphStyle("BulletStyle", fontName=body_font, fontSize=9.6,
                                  leading=13, textColor=colors.HexColor("#222222"))
    s["entry_title"] = ParagraphStyle("EntryTitle", fontName=heading_font, fontSize=10.4,
                                       leading=13, textColor=colors.HexColor("#111111"))
    s["entry_sub"] = ParagraphStyle("EntrySub", fontName=body_font, fontSize=9.4,
                                     leading=12.5, textColor=accent)
    s["entry_date"] = ParagraphStyle("EntryDate", fontName=body_font, fontSize=9,
                                      leading=12, textColor=colors.HexColor("#666666"),
                                      alignment=TA_LEFT)
    s["sidebar_heading"] = ParagraphStyle("SidebarHeading", fontName=heading_font, fontSize=10.5,
                                           leading=13, textColor=colors.white, spaceBefore=12, spaceAfter=4)
    s["sidebar_body"] = ParagraphStyle("SidebarBody", fontName=body_font, fontSize=9,
                                        leading=12.5, textColor=colors.white)
    return s


def _section_header(text, style, rule_color, width=None, thickness=1.1):
    flows = [Paragraph(text.upper(), style)]
    flows.append(HRFlowable(width="100%", thickness=thickness, color=rule_color,
                             spaceBefore=1, spaceAfter=6))
    return flows


def _entry_header_table(left_title, left_sub, right_date, styles, col_widths):
    left = [Paragraph(left_title, styles["entry_title"])]
    if left_sub:
        left.append(Paragraph(left_sub, styles["entry_sub"]))
    data = [[left, Paragraph(right_date, styles["entry_date"])]]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


# ---------------------------------------------------------------------------
# TEMPLATE 1: Modern (single column, colored header band)
# ---------------------------------------------------------------------------

def render_modern(data: ResumeData, path: str):
    accent = hex_to_color(data.accent_color)
    styles = _base_styles(accent)
    doc = SimpleDocTemplate(path, pagesize=letter,
                             leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                             topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    story = []
    p = data.personal

    story.append(Paragraph(p.full_name or "Your Name", styles["name"]))
    if p.title:
        story.append(Paragraph(p.title, styles["title"]))
    contact = _contact_line(p)
    if contact:
        story.append(Spacer(1, 3))
        story.append(Paragraph(contact, styles["contact"]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=2, color=accent, spaceAfter=8))

    if data.summary:
        story += _section_header("Summary", styles["section"], accent)
        story.append(Paragraph(data.summary, styles["body"]))
        story.append(Spacer(1, 4))

    if data.experience:
        story += _section_header("Experience", styles["section"], accent)
        for e in data.experience:
            sub = e.company + (f" — {e.location}" if e.location else "")
            date_range = f"{e.start_date} – {e.end_date}" if e.start_date or e.end_date else ""
            block = [_entry_header_table(e.role or "Role", sub, date_range, styles,
                                          [4.4 * inch, 2.0 * inch])]
            bf = _bullets_flowable(e.bullets, styles["bullet"])
            if bf:
                block.append(bf)
            block.append(Spacer(1, 6))
            story.append(KeepTogether(block))

    if data.projects:
        story += _section_header("Projects", styles["section"], accent)
        for pr in data.projects:
            title = pr.name + (f" ({pr.tech_stack})" if pr.tech_stack else "")
            block = [_entry_header_table(title, pr.description, pr.link or "", styles,
                                          [4.4 * inch, 2.0 * inch])]
            bf = _bullets_flowable(pr.bullets, styles["bullet"])
            if bf:
                block.append(bf)
            block.append(Spacer(1, 6))
            story.append(KeepTogether(block))

    if data.education:
        story += _section_header("Education", styles["section"], accent)
        for ed in data.education:
            degree_line = f"{ed.degree} {ed.field_of_study}".strip()
            sub = ed.institution + (f" — {ed.location}" if ed.location else "")
            date_range = f"{ed.start_date} – {ed.end_date}" if ed.start_date or ed.end_date else ""
            if ed.gpa:
                date_range += f"  |  GPA: {ed.gpa}" if date_range else f"GPA: {ed.gpa}"
            block = [_entry_header_table(degree_line, sub, date_range, styles,
                                          [4.4 * inch, 2.0 * inch])]
            bf = _bullets_flowable(ed.bullets, styles["bullet"])
            if bf:
                block.append(bf)
            block.append(Spacer(1, 6))
            story.append(KeepTogether(block))

    if data.skills:
        story += _section_header("Skills", styles["section"], accent)
        rows = []
        for sg in data.skills:
            label = f"<b>{sg.category}:</b> " if sg.category else ""
            rows.append(Paragraph(label + ", ".join(sg.items), styles["body"]))
        story.append(Table([[r] for r in rows], colWidths=[6.4 * inch],
                            style=TableStyle([
                                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                            ])))
        story.append(Spacer(1, 4))

    if data.certifications:
        story += _section_header("Certifications", styles["section"], accent)
        for c in data.certifications:
            line = f"<b>{c.name}</b>"
            meta = " — ".join(filter(None, [c.issuer, c.date]))
            if meta:
                line += f", {meta}"
            story.append(Paragraph(line, styles["body"]))
        story.append(Spacer(1, 4))

    if data.languages:
        story += _section_header("Languages", styles["section"], accent)
        line = "  •  ".join(f"{l.language} ({l.proficiency})" if l.proficiency else l.language
                             for l in data.languages)
        story.append(Paragraph(line, styles["body"]))

    doc.build(story)


# ---------------------------------------------------------------------------
# TEMPLATE 2: Classic (traditional, ATS-safe, centered header, no color)
# ---------------------------------------------------------------------------

def render_classic(data: ResumeData, path: str):
    black = colors.HexColor("#000000")
    styles = _base_styles(black, body_font="Times-Roman", heading_font="Times-Bold")
    styles["name"].alignment = TA_CENTER
    styles["name"].fontSize = 20
    styles["title"].alignment = TA_CENTER
    styles["title"].textColor = colors.HexColor("#333333")
    styles["contact"].alignment = TA_CENTER
    styles["section"].textColor = black
    styles["section"].fontName = "Times-Bold"
    styles["entry_sub"].textColor = colors.HexColor("#333333")
    styles["entry_sub"].fontName = "Times-Italic"

    doc = SimpleDocTemplate(path, pagesize=letter,
                             leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                             topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    story = []
    p = data.personal

    story.append(Paragraph(p.full_name or "Your Name", styles["name"]))
    if p.title:
        story.append(Paragraph(p.title, styles["title"]))
    contact = _contact_line(p)
    if contact:
        story.append(Spacer(1, 3))
        story.append(Paragraph(contact, styles["contact"]))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=black, spaceAfter=8))

    def section(title):
        story.append(Paragraph(title.upper(), styles["section"]))
        story.append(HRFlowable(width="100%", thickness=0.6, color=black, spaceBefore=1, spaceAfter=6))

    if data.summary:
        section("Summary")
        story.append(Paragraph(data.summary, styles["body"]))
        story.append(Spacer(1, 4))

    if data.experience:
        section("Experience")
        for e in data.experience:
            sub = e.company + (f" — {e.location}" if e.location else "")
            date_range = f"{e.start_date} – {e.end_date}" if e.start_date or e.end_date else ""
            block = [_entry_header_table(e.role or "Role", sub, date_range, styles,
                                          [4.3 * inch, 2.0 * inch])]
            bf = _bullets_flowable(e.bullets, styles["bullet"])
            if bf:
                block.append(bf)
            block.append(Spacer(1, 6))
            story.append(KeepTogether(block))

    if data.education:
        section("Education")
        for ed in data.education:
            degree_line = f"{ed.degree} {ed.field_of_study}".strip()
            sub = ed.institution + (f" — {ed.location}" if ed.location else "")
            date_range = f"{ed.start_date} – {ed.end_date}" if ed.start_date or ed.end_date else ""
            if ed.gpa:
                date_range += f"  |  GPA: {ed.gpa}" if date_range else f"GPA: {ed.gpa}"
            block = [_entry_header_table(degree_line, sub, date_range, styles,
                                          [4.3 * inch, 2.0 * inch])]
            bf = _bullets_flowable(ed.bullets, styles["bullet"])
            if bf:
                block.append(bf)
            block.append(Spacer(1, 6))
            story.append(KeepTogether(block))

    if data.projects:
        section("Projects")
        for pr in data.projects:
            title = pr.name + (f" ({pr.tech_stack})" if pr.tech_stack else "")
            block = [_entry_header_table(title, pr.description, pr.link or "", styles,
                                          [4.3 * inch, 2.0 * inch])]
            bf = _bullets_flowable(pr.bullets, styles["bullet"])
            if bf:
                block.append(bf)
            block.append(Spacer(1, 6))
            story.append(KeepTogether(block))

    if data.skills:
        section("Skills")
        for sg in data.skills:
            label = f"<b>{sg.category}:</b> " if sg.category else ""
            story.append(Paragraph(label + ", ".join(sg.items), styles["body"]))
        story.append(Spacer(1, 4))

    if data.certifications:
        section("Certifications")
        for c in data.certifications:
            line = f"<b>{c.name}</b>"
            meta = " — ".join(filter(None, [c.issuer, c.date]))
            if meta:
                line += f", {meta}"
            story.append(Paragraph(line, styles["body"]))
        story.append(Spacer(1, 4))

    if data.languages:
        section("Languages")
        line = "  •  ".join(f"{l.language} ({l.proficiency})" if l.proficiency else l.language
                             for l in data.languages)
        story.append(Paragraph(line, styles["body"]))

    doc.build(story)


# ---------------------------------------------------------------------------
# TEMPLATE 3: Minimal (lots of whitespace, light rules)
# ---------------------------------------------------------------------------

def render_minimal(data: ResumeData, path: str):
    accent = hex_to_color(data.accent_color)
    gray = colors.HexColor("#999999")
    styles = _base_styles(colors.HexColor("#111111"), body_font="Helvetica", heading_font="Helvetica")
    styles["name"].fontName = "Helvetica"
    styles["name"].fontSize = 22
    styles["section"].textColor = gray
    styles["section"].fontName = "Helvetica-Bold"
    styles["section"].fontSize = 9.5
    styles["entry_title"].fontName = "Helvetica-Bold"
    styles["entry_sub"].textColor = colors.HexColor("#555555")
    styles["title"].textColor = accent

    doc = SimpleDocTemplate(path, pagesize=letter,
                             leftMargin=0.8 * inch, rightMargin=0.8 * inch,
                             topMargin=0.7 * inch, bottomMargin=0.7 * inch)
    story = []
    p = data.personal

    story.append(Paragraph(p.full_name or "Your Name", styles["name"]))
    if p.title:
        story.append(Paragraph(p.title, styles["title"]))
    contact = _contact_line(p, separator="   ·   ")
    if contact:
        story.append(Spacer(1, 4))
        story.append(Paragraph(contact, styles["contact"]))
    story.append(Spacer(1, 14))

    def section(title):
        story.append(Paragraph(title.upper() + "  ", styles["section"]))
        story.append(Spacer(1, 4))

    if data.summary:
        section("Summary")
        story.append(Paragraph(data.summary, styles["body"]))
        story.append(Spacer(1, 10))

    if data.experience:
        section("Experience")
        for e in data.experience:
            sub = e.company + (f" — {e.location}" if e.location else "")
            date_range = f"{e.start_date} – {e.end_date}" if e.start_date or e.end_date else ""
            block = [_entry_header_table(e.role or "Role", sub, date_range, styles,
                                          [4.3 * inch, 2.0 * inch])]
            bf = _bullets_flowable(e.bullets, styles["bullet"])
            if bf:
                block.append(bf)
            block.append(Spacer(1, 8))
            story.append(KeepTogether(block))
        story.append(Spacer(1, 2))

    if data.projects:
        section("Projects")
        for pr in data.projects:
            title = pr.name + (f" ({pr.tech_stack})" if pr.tech_stack else "")
            block = [_entry_header_table(title, pr.description, pr.link or "", styles,
                                          [4.3 * inch, 2.0 * inch])]
            bf = _bullets_flowable(pr.bullets, styles["bullet"])
            if bf:
                block.append(bf)
            block.append(Spacer(1, 8))
            story.append(KeepTogether(block))

    if data.education:
        section("Education")
        for ed in data.education:
            degree_line = f"{ed.degree} {ed.field_of_study}".strip()
            sub = ed.institution + (f" — {ed.location}" if ed.location else "")
            date_range = f"{ed.start_date} – {ed.end_date}" if ed.start_date or ed.end_date else ""
            if ed.gpa:
                date_range += f"  |  GPA: {ed.gpa}" if date_range else f"GPA: {ed.gpa}"
            block = [_entry_header_table(degree_line, sub, date_range, styles,
                                          [4.3 * inch, 2.0 * inch])]
            bf = _bullets_flowable(ed.bullets, styles["bullet"])
            if bf:
                block.append(bf)
            block.append(Spacer(1, 8))
            story.append(KeepTogether(block))

    if data.skills:
        section("Skills")
        for sg in data.skills:
            label = f"<b>{sg.category}:</b> " if sg.category else ""
            story.append(Paragraph(label + ", ".join(sg.items), styles["body"]))
        story.append(Spacer(1, 8))

    if data.certifications:
        section("Certifications")
        for c in data.certifications:
            line = f"<b>{c.name}</b>"
            meta = " — ".join(filter(None, [c.issuer, c.date]))
            if meta:
                line += f", {meta}"
            story.append(Paragraph(line, styles["body"]))
        story.append(Spacer(1, 8))

    if data.languages:
        section("Languages")
        line = "   ·   ".join(f"{l.language} ({l.proficiency})" if l.proficiency else l.language
                               for l in data.languages)
        story.append(Paragraph(line, styles["body"]))

    doc.build(story)


# ---------------------------------------------------------------------------
# TEMPLATE 4: Sidebar (two-column, colored sidebar)
# ---------------------------------------------------------------------------

def render_sidebar(data: ResumeData, path: str):
    accent = hex_to_color(data.accent_color)
    dark_accent = darken(accent, 0.75)
    styles = _base_styles(accent)

    SIDEBAR_W = 2.3 * inch
    MAIN_W = 5.7 * inch
    PAGE_W, PAGE_H = letter

    doc = BaseDocTemplate(path, pagesize=letter,
                           leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0)

    sidebar_frame = Frame(0, 0, SIDEBAR_W, PAGE_H, leftPadding=16, rightPadding=14,
                           topPadding=28, bottomPadding=24, id="sidebar")
    main_frame = Frame(SIDEBAR_W, 0, MAIN_W, PAGE_H, leftPadding=24, rightPadding=28,
                        topPadding=32, bottomPadding=28, id="main")

    def draw_sidebar_bg(canvas, doc_):
        canvas.saveState()
        canvas.setFillColor(dark_accent)
        canvas.rect(0, 0, SIDEBAR_W, PAGE_H, fill=1, stroke=0)
        canvas.restoreState()

    template = PageTemplate(id="sidebarTemplate", frames=[sidebar_frame, main_frame],
                             onPage=draw_sidebar_bg)
    doc.addPageTemplates([template])

    p = data.personal
    sidebar_story = []
    main_story = []

    # ---- Sidebar content ----
    name_style = ParagraphStyle("SBName", fontName="Helvetica-Bold", fontSize=15,
                                 leading=18, textColor=colors.white)
    title_style = ParagraphStyle("SBTitle", fontName="Helvetica", fontSize=9.5,
                                  leading=12.5, textColor=colors.Color(1, 1, 1, 0.85))
    sidebar_story.append(Paragraph(p.full_name or "Your Name", name_style))
    if p.title:
        sidebar_story.append(Spacer(1, 3))
        sidebar_story.append(Paragraph(p.title, title_style))
    sidebar_story.append(Spacer(1, 10))
    sidebar_story.append(HRFlowable(width="100%", thickness=0.7,
                                     color=colors.Color(1, 1, 1, 0.4), spaceAfter=8))

    sidebar_story.append(Paragraph("CONTACT", styles["sidebar_heading"]))
    for val in [p.email, p.phone, p.location, p.linkedin, p.website, p.github]:
        if val:
            sidebar_story.append(Paragraph(val, styles["sidebar_body"]))
            sidebar_story.append(Spacer(1, 2))

    if data.skills:
        sidebar_story.append(Paragraph("SKILLS", styles["sidebar_heading"]))
        for sg in data.skills:
            if sg.category:
                sidebar_story.append(Paragraph(f"<b>{sg.category}</b>", styles["sidebar_body"]))
            sidebar_story.append(Paragraph(", ".join(sg.items), styles["sidebar_body"]))
            sidebar_story.append(Spacer(1, 5))

    if data.languages:
        sidebar_story.append(Paragraph("LANGUAGES", styles["sidebar_heading"]))
        for l in data.languages:
            txt = f"{l.language} — {l.proficiency}" if l.proficiency else l.language
            sidebar_story.append(Paragraph(txt, styles["sidebar_body"]))
            sidebar_story.append(Spacer(1, 2))

    if data.certifications:
        sidebar_story.append(Paragraph("CERTIFICATIONS", styles["sidebar_heading"]))
        for c in data.certifications:
            sidebar_story.append(Paragraph(f"<b>{c.name}</b>", styles["sidebar_body"]))
            meta = " — ".join(filter(None, [c.issuer, c.date]))
            if meta:
                sidebar_story.append(Paragraph(meta, styles["sidebar_body"]))
            sidebar_story.append(Spacer(1, 5))

    # ---- Main content ----
    main_section_style = ParagraphStyle("MainSection", fontName="Helvetica-Bold", fontSize=11.5,
                                         leading=14, textColor=dark_accent, spaceBefore=8, spaceAfter=4)

    def main_section(title):
        main_story.append(Paragraph(title.upper(), main_section_style))
        main_story.append(HRFlowable(width="100%", thickness=1, color=dark_accent, spaceAfter=6))

    if data.summary:
        main_section("Profile")
        main_story.append(Paragraph(data.summary, styles["body"]))
        main_story.append(Spacer(1, 4))

    if data.experience:
        main_section("Experience")
        for e in data.experience:
            sub = e.company + (f" — {e.location}" if e.location else "")
            date_range = f"{e.start_date} – {e.end_date}" if e.start_date or e.end_date else ""
            block = [_entry_header_table(e.role or "Role", sub, date_range, styles,
                                          [3.6 * inch, 1.7 * inch])]
            bf = _bullets_flowable(e.bullets, styles["bullet"])
            if bf:
                block.append(bf)
            block.append(Spacer(1, 6))
            main_story.append(KeepTogether(block))

    if data.projects:
        main_section("Projects")
        for pr in data.projects:
            title = pr.name + (f" ({pr.tech_stack})" if pr.tech_stack else "")
            block = [_entry_header_table(title, pr.description, pr.link or "", styles,
                                          [3.6 * inch, 1.7 * inch])]
            bf = _bullets_flowable(pr.bullets, styles["bullet"])
            if bf:
                block.append(bf)
            block.append(Spacer(1, 6))
            main_story.append(KeepTogether(block))

    if data.education:
        main_section("Education")
        for ed in data.education:
            degree_line = f"{ed.degree} {ed.field_of_study}".strip()
            sub = ed.institution + (f" — {ed.location}" if ed.location else "")
            date_range = f"{ed.start_date} – {ed.end_date}" if ed.start_date or ed.end_date else ""
            if ed.gpa:
                date_range += f"  |  GPA: {ed.gpa}" if date_range else f"GPA: {ed.gpa}"
            block = [_entry_header_table(degree_line, sub, date_range, styles,
                                          [3.6 * inch, 1.7 * inch])]
            bf = _bullets_flowable(ed.bullets, styles["bullet"])
            if bf:
                block.append(bf)
            block.append(Spacer(1, 6))
            main_story.append(KeepTogether(block))

    story = sidebar_story + [FrameBreak()] + main_story
    doc.build(story)


TEMPLATES = {
    "Modern": render_modern,
    "Classic": render_classic,
    "Minimal": render_minimal,
    "Sidebar": render_sidebar,
}


def render_resume(data: ResumeData, path: str, template: str = None):
    template_name = template or data.template or "Modern"
    fn = TEMPLATES.get(template_name, render_modern)
    fn(data, path)
    return path
