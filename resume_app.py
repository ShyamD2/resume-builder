"""
resume_app.py
Advanced Resume Builder - Desktop GUI (Tkinter)

Run:
    python3 resume_app.py
"""

import os
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox

from resume_data import (
    ResumeData, PersonalInfo, ExperienceEntry, EducationEntry,
    ProjectEntry, CertificationEntry, SkillGroup, LanguageEntry, sample_resume
)
from resume_pdf import render_resume, TEMPLATES
from resume_text import to_ats_text, analyze_resume

APP_TITLE = "Advanced Resume Builder"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(BASE_DIR, "profiles")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


# ---------------------------------------------------------------------------
# Reusable widgets
# ---------------------------------------------------------------------------

class LabeledEntry(ttk.Frame):
    def __init__(self, parent, label, width=30, on_change=None):
        super().__init__(parent)
        ttk.Label(self, text=label).pack(anchor="w")
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=width)
        self.entry.pack(fill="x", pady=(2, 0))
        if on_change:
            self.var.trace_add("write", lambda *a: on_change())

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value or "")


class LabeledText(ttk.Frame):
    def __init__(self, parent, label, height=4, on_change=None):
        super().__init__(parent)
        ttk.Label(self, text=label).pack(anchor="w")
        self.text = tk.Text(self, height=height, wrap="word")
        self.text.pack(fill="both", expand=True, pady=(2, 0))
        if on_change:
            self.text.bind("<KeyRelease>", lambda e: on_change())

    def get(self):
        return self.text.get("1.0", "end").strip()

    def set(self, value):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value or "")


class BulletListEditor(ttk.Frame):
    """Editable list of bullet-point strings, one per line in a Text box."""

    def __init__(self, parent, label="Bullet points (one per line)", height=5, on_change=None):
        super().__init__(parent)
        ttk.Label(self, text=label, foreground="#555").pack(anchor="w")
        self.text = tk.Text(self, height=height, wrap="word")
        self.text.pack(fill="both", expand=True, pady=(2, 0))
        if on_change:
            self.text.bind("<KeyRelease>", lambda e: on_change())

    def get_list(self):
        raw = self.text.get("1.0", "end").strip()
        return [line.strip() for line in raw.split("\n") if line.strip()]

    def set_list(self, items):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(items or []))


class CollapsibleEntryCard(ttk.Frame):
    """A bordered card representing one repeatable entry (job, school, project...)
    with a delete button and a move-up/move-down control."""

    def __init__(self, parent, title, on_delete, on_move_up, on_move_down):
        super().__init__(parent, relief="solid", borderwidth=1, padding=10)
        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text=title, font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Button(header, text="▲", width=3, command=on_move_up).pack(side="right", padx=1)
        ttk.Button(header, text="▼", width=3, command=on_move_down).pack(side="right", padx=1)
        ttk.Button(header, text="✕ Remove", command=on_delete).pack(side="right", padx=6)
        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True, pady=(8, 0))


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class ResumeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1200x800")
        self.minsize(1000, 700)

        os.makedirs(PROFILES_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        self.data = ResumeData()
        self.data.personal = PersonalInfo()

        self._build_style()
        self._build_menu_bar()
        self._build_layout()
        self._refresh_all_lists()

    # ---------- setup ----------

    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook.Tab", padding=(14, 8))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Score.TLabel", font=("Segoe UI", 22, "bold"))

    def _build_menu_bar(self):
        bar = ttk.Frame(self, padding=(10, 8))
        bar.pack(fill="x", side="top")

        ttk.Button(bar, text="Load Sample Resume", command=self._load_sample).pack(side="left")
        ttk.Button(bar, text="New Blank Resume", command=self._new_blank).pack(side="left", padx=6)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(bar, text="Save Profile...", command=self._save_profile).pack(side="left")
        ttk.Button(bar, text="Load Profile...", command=self._load_profile).pack(side="left", padx=6)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=8)

        ttk.Label(bar, text="Template:").pack(side="left")
        self.template_var = tk.StringVar(value="Modern")
        template_combo = ttk.Combobox(bar, textvariable=self.template_var, state="readonly",
                                       values=list(TEMPLATES.keys()), width=12)
        template_combo.pack(side="left", padx=4)

        ttk.Label(bar, text="Accent:").pack(side="left", padx=(10, 0))
        self.accent_swatch = tk.Canvas(bar, width=24, height=20, highlightthickness=1,
                                        highlightbackground="#888", bg="#2563EB", cursor="hand2")
        self.accent_swatch.pack(side="left", padx=4)
        self.accent_swatch.bind("<Button-1>", self._pick_accent)
        self.accent_color = "#2563EB"

        ttk.Button(bar, text="Export PDF", style="Accent.TButton",
                   command=self._export_pdf).pack(side="right")
        ttk.Button(bar, text="Export ATS Text", command=self._export_text).pack(side="right", padx=6)
        ttk.Button(bar, text="Check Resume Score", command=self._show_score).pack(side="right")

    def _build_layout(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_personal = self._make_scrollable_tab("Personal & Summary")
        self.tab_experience = self._make_scrollable_tab("Experience")
        self.tab_education = self._make_scrollable_tab("Education")
        self.tab_skills = self._make_scrollable_tab("Skills")
        self.tab_projects = self._make_scrollable_tab("Projects")
        self.tab_certs = self._make_scrollable_tab("Certifications & Languages")

        self._build_personal_tab(self.tab_personal)
        self._build_experience_tab(self.tab_experience)
        self._build_education_tab(self.tab_education)
        self._build_skills_tab(self.tab_skills)
        self._build_projects_tab(self.tab_projects)
        self._build_certs_tab(self.tab_certs)

        # status bar
        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(self, textvariable=self.status_var, foreground="#555",
                            padding=(10, 4), relief="sunken")
        status.pack(fill="x", side="bottom")

    def _make_scrollable_tab(self, title):
        outer = ttk.Frame(self.notebook)
        self.notebook.add(outer, text=f"  {title}  ")

        canvas = tk.Canvas(outer, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, padding=16)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw", width=1140)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", lambda e: None)  # overridden per-tab if needed

        return inner

    # ---------- Personal tab ----------

    def _build_personal_tab(self, parent):
        frame = ttk.LabelFrame(parent, text="Personal Information", padding=12)
        frame.pack(fill="x", pady=(0, 12))

        grid = ttk.Frame(frame)
        grid.pack(fill="x")
        self.p_name = LabeledEntry(grid, "Full Name")
        self.p_title = LabeledEntry(grid, "Job Title / Headline")
        self.p_email = LabeledEntry(grid, "Email")
        self.p_phone = LabeledEntry(grid, "Phone")
        self.p_location = LabeledEntry(grid, "Location (City, State)")
        self.p_linkedin = LabeledEntry(grid, "LinkedIn")
        self.p_website = LabeledEntry(grid, "Website / Portfolio")
        self.p_github = LabeledEntry(grid, "GitHub")

        fields = [self.p_name, self.p_title, self.p_email, self.p_phone,
                  self.p_location, self.p_linkedin, self.p_website, self.p_github]
        for i, f in enumerate(fields):
            r, c = divmod(i, 2)
            f.grid(row=r, column=c, sticky="ew", padx=8, pady=6)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        summary_frame = ttk.LabelFrame(parent, text="Professional Summary", padding=12)
        summary_frame.pack(fill="x", pady=(0, 12))
        self.summary_text = LabeledText(summary_frame,
                                         "2-4 sentences summarizing your experience and strengths:",
                                         height=5)
        self.summary_text.pack(fill="both", expand=True)

    def _collect_personal(self):
        return PersonalInfo(
            full_name=self.p_name.get(),
            title=self.p_title.get(),
            email=self.p_email.get(),
            phone=self.p_phone.get(),
            location=self.p_location.get(),
            linkedin=self.p_linkedin.get(),
            website=self.p_website.get(),
            github=self.p_github.get(),
        )

    # ---------- Experience tab ----------

    def _build_experience_tab(self, parent):
        ttk.Button(parent, text="+ Add Experience Entry",
                   command=self._add_experience_entry).pack(anchor="w", pady=(0, 10))
        self.experience_container = ttk.Frame(parent)
        self.experience_container.pack(fill="both", expand=True)
        self.experience_cards = []  # list of dict{card, fields}

    def _add_experience_entry(self, entry: ExperienceEntry = None):
        entry = entry or ExperienceEntry()
        idx = len(self.experience_cards)
        card_holder = {}

        def on_delete():
            self._remove_card(self.experience_cards, card_holder, self.experience_container)

        def on_up():
            self._move_card(self.experience_cards, card_holder, self.experience_container, -1)

        def on_down():
            self._move_card(self.experience_cards, card_holder, self.experience_container, 1)

        card = CollapsibleEntryCard(self.experience_container, f"Experience #{idx + 1}",
                                     on_delete, on_up, on_down)
        card.pack(fill="x", pady=6)

        grid = ttk.Frame(card.body)
        grid.pack(fill="x")
        role = LabeledEntry(grid, "Job Title")
        company = LabeledEntry(grid, "Company")
        location = LabeledEntry(grid, "Location")
        start = LabeledEntry(grid, "Start Date (e.g. Jan 2022)")
        end = LabeledEntry(grid, "End Date (or 'Present')")
        role.set(entry.role); company.set(entry.company); location.set(entry.location)
        start.set(entry.start_date); end.set(entry.end_date)

        for i, f in enumerate([role, company, location, start, end]):
            r, c = divmod(i, 3)
            f.grid(row=r, column=c, sticky="ew", padx=6, pady=4)
        for c in range(3):
            grid.columnconfigure(c, weight=1)

        bullets = BulletListEditor(card.body, height=5)
        bullets.pack(fill="both", expand=True, pady=(8, 0))
        bullets.set_list(entry.bullets)

        card_holder.update(card=card, role=role, company=company, location=location,
                            start=start, end=end, bullets=bullets)
        self.experience_cards.append(card_holder)
        self._renumber_cards(self.experience_cards, "Experience")

    def _collect_experience(self):
        result = []
        for c in self.experience_cards:
            result.append(ExperienceEntry(
                role=c["role"].get(), company=c["company"].get(), location=c["location"].get(),
                start_date=c["start"].get(), end_date=c["end"].get(),
                bullets=c["bullets"].get_list(),
            ))
        return result

    # ---------- Education tab ----------

    def _build_education_tab(self, parent):
        ttk.Button(parent, text="+ Add Education Entry",
                   command=self._add_education_entry).pack(anchor="w", pady=(0, 10))
        self.education_container = ttk.Frame(parent)
        self.education_container.pack(fill="both", expand=True)
        self.education_cards = []

    def _add_education_entry(self, entry: EducationEntry = None):
        entry = entry or EducationEntry()
        idx = len(self.education_cards)
        card_holder = {}

        def on_delete():
            self._remove_card(self.education_cards, card_holder, self.education_container)

        def on_up():
            self._move_card(self.education_cards, card_holder, self.education_container, -1)

        def on_down():
            self._move_card(self.education_cards, card_holder, self.education_container, 1)

        card = CollapsibleEntryCard(self.education_container, f"Education #{idx + 1}",
                                     on_delete, on_up, on_down)
        card.pack(fill="x", pady=6)

        grid = ttk.Frame(card.body)
        grid.pack(fill="x")
        institution = LabeledEntry(grid, "Institution")
        degree = LabeledEntry(grid, "Degree (e.g. B.S.)")
        field_study = LabeledEntry(grid, "Field of Study")
        location = LabeledEntry(grid, "Location")
        start = LabeledEntry(grid, "Start Year")
        end = LabeledEntry(grid, "End Year")
        gpa = LabeledEntry(grid, "GPA (optional)")

        institution.set(entry.institution); degree.set(entry.degree)
        field_study.set(entry.field_of_study); location.set(entry.location)
        start.set(entry.start_date); end.set(entry.end_date); gpa.set(entry.gpa)

        fields = [institution, degree, field_study, location, start, end, gpa]
        for i, f in enumerate(fields):
            r, c = divmod(i, 3)
            f.grid(row=r, column=c, sticky="ew", padx=6, pady=4)
        for c in range(3):
            grid.columnconfigure(c, weight=1)

        bullets = BulletListEditor(card.body, "Honors / activities (one per line, optional)", height=3)
        bullets.pack(fill="both", expand=True, pady=(8, 0))
        bullets.set_list(entry.bullets)

        card_holder.update(card=card, institution=institution, degree=degree,
                            field_study=field_study, location=location, start=start, end=end,
                            gpa=gpa, bullets=bullets)
        self.education_cards.append(card_holder)
        self._renumber_cards(self.education_cards, "Education")

    def _collect_education(self):
        result = []
        for c in self.education_cards:
            result.append(EducationEntry(
                institution=c["institution"].get(), degree=c["degree"].get(),
                field_of_study=c["field_study"].get(), location=c["location"].get(),
                start_date=c["start"].get(), end_date=c["end"].get(), gpa=c["gpa"].get(),
                bullets=c["bullets"].get_list(),
            ))
        return result

    # ---------- Skills tab ----------

    def _build_skills_tab(self, parent):
        info = ttk.Label(parent, foreground="#555",
                          text="Group your skills into categories (e.g. Languages, Frameworks, Tools).")
        info.pack(anchor="w", pady=(0, 10))
        ttk.Button(parent, text="+ Add Skill Category",
                   command=self._add_skill_group).pack(anchor="w", pady=(0, 10))
        self.skills_container = ttk.Frame(parent)
        self.skills_container.pack(fill="both", expand=True)
        self.skill_cards = []

    def _add_skill_group(self, group: SkillGroup = None):
        group = group or SkillGroup()
        card_holder = {}

        def on_delete():
            self._remove_card(self.skill_cards, card_holder, self.skills_container)

        def on_up():
            self._move_card(self.skill_cards, card_holder, self.skills_container, -1)

        def on_down():
            self._move_card(self.skill_cards, card_holder, self.skills_container, 1)

        idx = len(self.skill_cards)
        card = CollapsibleEntryCard(self.skills_container, f"Skill Category #{idx + 1}",
                                     on_delete, on_up, on_down)
        card.pack(fill="x", pady=6)

        category = LabeledEntry(card.body, "Category name (e.g. 'Languages')")
        category.set(group.category)
        category.pack(fill="x", pady=(0, 6))

        items = LabeledEntry(card.body, "Skills (comma-separated)", width=60)
        items.set(", ".join(group.items))
        items.pack(fill="x")

        card_holder.update(card=card, category=category, items=items)
        self.skill_cards.append(card_holder)
        self._renumber_cards(self.skill_cards, "Skill Category")

    def _collect_skills(self):
        result = []
        for c in self.skill_cards:
            items = [s.strip() for s in c["items"].get().split(",") if s.strip()]
            if c["category"].get() or items:
                result.append(SkillGroup(category=c["category"].get(), items=items))
        return result

    # ---------- Projects tab ----------

    def _build_projects_tab(self, parent):
        ttk.Button(parent, text="+ Add Project",
                   command=self._add_project_entry).pack(anchor="w", pady=(0, 10))
        self.projects_container = ttk.Frame(parent)
        self.projects_container.pack(fill="both", expand=True)
        self.project_cards = []

    def _add_project_entry(self, entry: ProjectEntry = None):
        entry = entry or ProjectEntry()
        card_holder = {}

        def on_delete():
            self._remove_card(self.project_cards, card_holder, self.projects_container)

        def on_up():
            self._move_card(self.project_cards, card_holder, self.projects_container, -1)

        def on_down():
            self._move_card(self.project_cards, card_holder, self.projects_container, 1)

        idx = len(self.project_cards)
        card = CollapsibleEntryCard(self.projects_container, f"Project #{idx + 1}",
                                     on_delete, on_up, on_down)
        card.pack(fill="x", pady=6)

        grid = ttk.Frame(card.body)
        grid.pack(fill="x")
        name = LabeledEntry(grid, "Project Name")
        tech = LabeledEntry(grid, "Tech Stack (comma-separated)")
        link = LabeledEntry(grid, "Link (optional)")
        name.set(entry.name); tech.set(entry.tech_stack); link.set(entry.link)
        for i, f in enumerate([name, tech, link]):
            f.grid(row=0, column=i, sticky="ew", padx=6, pady=4)
        for c in range(3):
            grid.columnconfigure(c, weight=1)

        desc = LabeledEntry(card.body, "One-line description", width=80)
        desc.set(entry.description)
        desc.pack(fill="x", pady=(6, 0))

        bullets = BulletListEditor(card.body, height=3)
        bullets.pack(fill="both", expand=True, pady=(8, 0))
        bullets.set_list(entry.bullets)

        card_holder.update(card=card, name=name, tech=tech, link=link, desc=desc, bullets=bullets)
        self.project_cards.append(card_holder)
        self._renumber_cards(self.project_cards, "Project")

    def _collect_projects(self):
        result = []
        for c in self.project_cards:
            result.append(ProjectEntry(
                name=c["name"].get(), description=c["desc"].get(), tech_stack=c["tech"].get(),
                link=c["link"].get(), bullets=c["bullets"].get_list(),
            ))
        return result

    # ---------- Certifications & Languages tab ----------

    def _build_certs_tab(self, parent):
        cert_frame = ttk.LabelFrame(parent, text="Certifications", padding=12)
        cert_frame.pack(fill="x", pady=(0, 12))
        ttk.Button(cert_frame, text="+ Add Certification",
                   command=self._add_cert_entry).pack(anchor="w", pady=(0, 8))
        self.certs_container = ttk.Frame(cert_frame)
        self.certs_container.pack(fill="both", expand=True)
        self.cert_cards = []

        lang_frame = ttk.LabelFrame(parent, text="Languages", padding=12)
        lang_frame.pack(fill="x", pady=(0, 12))
        ttk.Button(lang_frame, text="+ Add Language",
                   command=self._add_language_entry).pack(anchor="w", pady=(0, 8))
        self.langs_container = ttk.Frame(lang_frame)
        self.langs_container.pack(fill="both", expand=True)
        self.lang_cards = []

    def _add_cert_entry(self, entry: CertificationEntry = None):
        entry = entry or CertificationEntry()
        card_holder = {}

        def on_delete():
            self._remove_card(self.cert_cards, card_holder, self.certs_container)

        def on_up():
            self._move_card(self.cert_cards, card_holder, self.certs_container, -1)

        def on_down():
            self._move_card(self.cert_cards, card_holder, self.certs_container, 1)

        idx = len(self.cert_cards)
        card = CollapsibleEntryCard(self.certs_container, f"Certification #{idx + 1}",
                                     on_delete, on_up, on_down)
        card.pack(fill="x", pady=6)

        grid = ttk.Frame(card.body)
        grid.pack(fill="x")
        name = LabeledEntry(grid, "Certification Name")
        issuer = LabeledEntry(grid, "Issuer")
        date = LabeledEntry(grid, "Date")
        cred = LabeledEntry(grid, "Credential ID (optional)")
        name.set(entry.name); issuer.set(entry.issuer); date.set(entry.date); cred.set(entry.credential_id)
        for i, f in enumerate([name, issuer, date, cred]):
            r, c = divmod(i, 2)
            f.grid(row=r, column=c, sticky="ew", padx=6, pady=4)
        for c in range(2):
            grid.columnconfigure(c, weight=1)

        card_holder.update(card=card, name=name, issuer=issuer, date=date, cred=cred)
        self.cert_cards.append(card_holder)
        self._renumber_cards(self.cert_cards, "Certification")

    def _collect_certs(self):
        result = []
        for c in self.cert_cards:
            result.append(CertificationEntry(
                name=c["name"].get(), issuer=c["issuer"].get(), date=c["date"].get(),
                credential_id=c["cred"].get(),
            ))
        return result

    def _add_language_entry(self, entry: LanguageEntry = None):
        entry = entry or LanguageEntry()
        card_holder = {}

        def on_delete():
            self._remove_card(self.lang_cards, card_holder, self.langs_container)

        def on_up():
            self._move_card(self.lang_cards, card_holder, self.langs_container, -1)

        def on_down():
            self._move_card(self.lang_cards, card_holder, self.langs_container, 1)

        idx = len(self.lang_cards)
        card = CollapsibleEntryCard(self.langs_container, f"Language #{idx + 1}",
                                     on_delete, on_up, on_down)
        card.pack(fill="x", pady=6)

        grid = ttk.Frame(card.body)
        grid.pack(fill="x")
        lang = LabeledEntry(grid, "Language")
        prof = LabeledEntry(grid, "Proficiency (e.g. Native, Fluent)")
        lang.set(entry.language); prof.set(entry.proficiency)
        lang.grid(row=0, column=0, sticky="ew", padx=6, pady=4)
        prof.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        card_holder.update(card=card, lang=lang, prof=prof)
        self.lang_cards.append(card_holder)
        self._renumber_cards(self.lang_cards, "Language")

    def _collect_languages(self):
        result = []
        for c in self.lang_cards:
            if c["lang"].get():
                result.append(LanguageEntry(language=c["lang"].get(), proficiency=c["prof"].get()))
        return result

    # ---------- Card management helpers ----------

    def _remove_card(self, card_list, card_holder, container):
        card_holder["card"].destroy()
        card_list.remove(card_holder)
        self._renumber_cards(card_list, None)

    def _move_card(self, card_list, card_holder, container, direction):
        idx = card_list.index(card_holder)
        new_idx = idx + direction
        if 0 <= new_idx < len(card_list):
            card_list[idx], card_list[new_idx] = card_list[new_idx], card_list[idx]
            for c in card_list:
                c["card"].pack_forget()
            for c in card_list:
                c["card"].pack(fill="x", pady=6)
            self._renumber_cards(card_list, None)

    def _renumber_cards(self, card_list, label_prefix):
        # Titles were set at creation time; renumbering is cosmetic only when needed.
        pass

    def _refresh_all_lists(self):
        pass

    # ---------- Data <-> UI sync ----------

    def _collect_all(self) -> ResumeData:
        data = ResumeData(
            personal=self._collect_personal(),
            summary=self.summary_text.get(),
            experience=self._collect_experience(),
            education=self._collect_education(),
            skills=self._collect_skills(),
            projects=self._collect_projects(),
            certifications=self._collect_certs(),
            languages=self._collect_languages(),
            template=self.template_var.get(),
            accent_color=self.accent_color,
        )
        return data

    def _load_into_ui(self, data: ResumeData):
        self.p_name.set(data.personal.full_name)
        self.p_title.set(data.personal.title)
        self.p_email.set(data.personal.email)
        self.p_phone.set(data.personal.phone)
        self.p_location.set(data.personal.location)
        self.p_linkedin.set(data.personal.linkedin)
        self.p_website.set(data.personal.website)
        self.p_github.set(data.personal.github)
        self.summary_text.set(data.summary)

        for container, card_list in [
            (self.experience_container, self.experience_cards),
            (self.education_container, self.education_cards),
            (self.skills_container, self.skill_cards),
            (self.projects_container, self.project_cards),
            (self.certs_container, self.cert_cards),
            (self.langs_container, self.lang_cards),
        ]:
            for c in list(card_list):
                c["card"].destroy()
            card_list.clear()

        for e in data.experience:
            self._add_experience_entry(e)
        for ed in data.education:
            self._add_education_entry(ed)
        for sg in data.skills:
            self._add_skill_group(sg)
        for pr in data.projects:
            self._add_project_entry(pr)
        for c in data.certifications:
            self._add_cert_entry(c)
        for l in data.languages:
            self._add_language_entry(l)

        self.template_var.set(data.template or "Modern")
        self.accent_color = data.accent_color or "#2563EB"
        self.accent_swatch.config(bg=self.accent_color)

    # ---------- Actions ----------

    def _pick_accent(self, event=None):
        rgb, hex_code = colorchooser.askcolor(color=self.accent_color, title="Choose accent color")
        if hex_code:
            self.accent_color = hex_code
            self.accent_swatch.config(bg=hex_code)

    def _load_sample(self):
        if messagebox.askyesno("Load Sample", "This will replace current content with a sample resume. Continue?"):
            self._load_into_ui(sample_resume())
            self.status_var.set("Loaded sample resume.")

    def _new_blank(self):
        if messagebox.askyesno("New Blank Resume", "This will clear all current content. Continue?"):
            self._load_into_ui(ResumeData())
            self.status_var.set("Started a new blank resume.")

    def _save_profile(self):
        data = self._collect_all()
        default_name = (data.personal.full_name or "resume").replace(" ", "_").lower()
        path = filedialog.asksaveasfilename(
            initialdir=PROFILES_DIR, initialfile=f"{default_name}.json",
            defaultextension=".json", filetypes=[("JSON profile", "*.json")]
        )
        if not path:
            return
        try:
            data.to_json(path)
            self.status_var.set(f"Profile saved to: {path}")
            messagebox.showinfo("Saved", f"Profile saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _load_profile(self):
        path = filedialog.askopenfilename(initialdir=PROFILES_DIR,
                                           filetypes=[("JSON profile", "*.json")])
        if not path:
            return
        try:
            data = ResumeData.from_json(path)
            self._load_into_ui(data)
            self.status_var.set(f"Loaded profile: {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _export_pdf(self):
        data = self._collect_all()
        if not data.personal.full_name:
            if not messagebox.askyesno("Missing name", "You haven't entered a name. Export anyway?"):
                return
        default_name = (data.personal.full_name or "resume").replace(" ", "_").lower()
        path = filedialog.asksaveasfilename(
            initialdir=OUTPUT_DIR, initialfile=f"{default_name}_{data.template.lower()}.pdf",
            defaultextension=".pdf", filetypes=[("PDF file", "*.pdf")]
        )
        if not path:
            return
        try:
            render_resume(data, path, template=data.template)
            self.status_var.set(f"PDF exported to: {path}")
            messagebox.showinfo("Exported", f"Resume PDF saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _export_text(self):
        data = self._collect_all()
        default_name = (data.personal.full_name or "resume").replace(" ", "_").lower()
        path = filedialog.asksaveasfilename(
            initialdir=OUTPUT_DIR, initialfile=f"{default_name}_ats.txt",
            defaultextension=".txt", filetypes=[("Text file", "*.txt")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(to_ats_text(data))
            self.status_var.set(f"ATS text exported to: {path}")
            messagebox.showinfo("Exported", f"ATS-friendly text saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _show_score(self):
        data = self._collect_all()
        result = analyze_resume(data)

        win = tk.Toplevel(self)
        win.title("Resume Score")
        win.geometry("480x520")

        ttk.Label(win, text="Resume Score", font=("Segoe UI", 14, "bold")).pack(pady=(16, 4))
        score_color = "#16A34A" if result["score"] >= 80 else "#D97706" if result["score"] >= 60 else "#DC2626"
        score_label = tk.Label(win, text=f"{result['score']} / 100", font=("Segoe UI", 28, "bold"),
                                fg=score_color)
        score_label.pack(pady=(0, 10))

        ttk.Label(win, text=f"Word count: {result['word_count']}", foreground="#666").pack()

        if result["issues"]:
            ttk.Label(win, text="Issues to fix:", font=("Segoe UI", 10, "bold"),
                      foreground="#DC2626").pack(anchor="w", padx=16, pady=(14, 2))
            for issue in result["issues"]:
                ttk.Label(win, text=f"• {issue}", wraplength=440, justify="left").pack(anchor="w", padx=24)

        if result["tips"]:
            ttk.Label(win, text="Suggestions:", font=("Segoe UI", 10, "bold"),
                      foreground="#D97706").pack(anchor="w", padx=16, pady=(14, 2))
            for tip in result["tips"]:
                ttk.Label(win, text=f"• {tip}", wraplength=440, justify="left").pack(anchor="w", padx=24)

        if not result["issues"] and not result["tips"]:
            ttk.Label(win, text="Looks great! No major issues found.",
                      foreground="#16A34A").pack(pady=20)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=16)


def main():
    app = ResumeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
