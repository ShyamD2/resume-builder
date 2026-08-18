# Advanced Resume Builder

A Python resume builder with a desktop GUI, a command-line tool, and a
library core — 4 professional templates, save/load profiles as JSON,
PDF + ATS-friendly plain-text export, and a built-in resume quality checker.

## Features

- **4 templates** — Modern (colored header), Classic (traditional/ATS-safe),
  Minimal (whitespace-forward), Sidebar (two-column with colored panel)
- **Full sections** — personal info, summary, experience, education, skills
  (grouped by category), projects, certifications, languages
- **Reorderable entries** — move any experience/education/project/etc. up or
  down, or remove it, right from the GUI
- **Custom accent color** for templates that support it
- **Save & load profiles** as JSON — build once, re-export in different
  templates or colors any time
- **PDF export** — clean, ATS-parseable text layer (verified with
  `pdftotext`), not an image
- **ATS plain-text export** — a stripped-down `.txt` version for pasting
  into online application forms that don't accept PDFs
- **Resume Score checker** — flags missing sections, weak action verbs
  (e.g. "responsible for"), bullets with no quantified impact, and length
  issues, with concrete suggestions

## Setup

```bash
pip install -r requirements.txt
```

Requires Python 3.8+. The GUI uses Tkinter, which ships with most standard
Python installs (on Linux you may need `sudo apt install python3-tk`).

## Usage

### 1. Desktop GUI (recommended)

```bash
python3 resume_app.py
```

- Click **Load Sample Resume** to see a fully filled-out example, or start
  from a blank resume and fill in your own info tab by tab.
- Each repeatable section (Experience, Education, Skills, Projects,
  Certifications, Languages) has an **+ Add** button — every entry becomes
  its own card with ▲ / ▼ reorder buttons and a ✕ remove button.
- Pick a **Template** and **Accent** color from the top bar.
- **Save Profile...** writes your data to a JSON file you can reopen later
  with **Load Profile...** — this is how you keep multiple resume versions
  (e.g. one per job type) or come back and edit later.
- **Export PDF** produces the final resume. **Export ATS Text** produces a
  plain-text version. **Check Resume Score** opens a report with a score out
  of 100 and specific suggestions.

### 2. Command line

```bash
# Generate a PDF from a saved JSON profile
python3 resume_cli.py -i profiles/my_resume.json -o output/my_resume.pdf

# Override template & accent color at export time
python3 resume_cli.py -i profiles/my_resume.json -o output/my_resume.pdf \
    --template Sidebar --accent "#0F766E"

# Also produce an ATS-friendly plain-text version
python3 resume_cli.py -i profiles/my_resume.json -o output/my_resume.pdf \
    --ats-text output/my_resume.txt

# Get a resume quality score without exporting anything
python3 resume_cli.py -i profiles/my_resume.json --score

# Try it instantly with the built-in sample, in every template
python3 resume_cli.py --sample --outdir output/samples
```

Run `python3 resume_cli.py --help` for the full option list.

### 3. As a library

```python
from resume_data import ResumeData, PersonalInfo, ExperienceEntry
from resume_pdf import render_resume
from resume_text import to_ats_text, analyze_resume

data = ResumeData(
    personal=PersonalInfo(full_name="Jane Doe", title="Product Manager",
                           email="jane@example.com"),
    summary="Product manager with 5 years of experience shipping...",
    experience=[
        ExperienceEntry(role="Senior PM", company="Acme Inc.",
                         start_date="2021", end_date="Present",
                         bullets=["Launched X, increasing revenue 20%"]),
    ],
    template="Modern",
    accent_color="#2563EB",
)

render_resume(data, "resume.pdf")
print(analyze_resume(data))
```

## Writing your own profile JSON by hand

Every profile follows the shape produced by `ResumeData.to_dict()`. The
easiest way to get a starting point is:

```bash
python3 -c "from resume_data import sample_resume; sample_resume().to_json('profiles/starter.json')"
```

Then edit `profiles/starter.json` in any text editor and re-render it.

## Tips for a strong resume (enforced by the Score checker)

- Start bullet points with a strong action verb (Led, Built, Launched,
  Reduced...) instead of "Responsible for" or "Helped with".
- Quantify impact where you can — percentages, dollar amounts, user counts,
  time saved.
- Keep total content roughly in the 150–900 word range for a 1-page (or
  tight 2-page) resume.
- Use the **Classic** template if you're not sure a target company's ATS
  handles colored/styled PDFs well — it's plain black-on-white and still
  extracts perfectly as text.

## Project structure

```
resume_builder_app/
├── resume_data.py     # Data model (ResumeData, PersonalInfo, etc.) + JSON I/O
├── resume_pdf.py       # PDF rendering — 4 templates, built on reportlab
├── resume_text.py      # ATS plain-text export + resume quality analyzer
├── resume_app.py       # Tkinter desktop GUI
├── resume_cli.py        # Command-line interface
├── requirements.txt
├── README.md
├── profiles/           # Save/load your resume data here (JSON)
│   └── sample_profile.json   # A filled-in example to try immediately
├── photos/              # (reserved for future photo-enabled templates)
└── output/              # Generated PDFs / text land here by default
```
