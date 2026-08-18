"""
resume_data.py
Data model for the Advanced Resume Builder.

All resume content lives in a single ResumeData object which can be
serialized to / loaded from JSON, so profiles can be saved and reused.
"""

import json
import dataclasses
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class PersonalInfo:
    full_name: str = ""
    title: str = ""              # e.g. "Senior Software Engineer"
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    website: str = ""
    github: str = ""
    photo_path: str = ""         # optional, used by templates that support a photo


@dataclass
class ExperienceEntry:
    company: str = ""
    role: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""           # "Present" allowed
    bullets: List[str] = field(default_factory=list)


@dataclass
class EducationEntry:
    institution: str = ""
    degree: str = ""
    field_of_study: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    gpa: str = ""
    bullets: List[str] = field(default_factory=list)


@dataclass
class ProjectEntry:
    name: str = ""
    description: str = ""
    tech_stack: str = ""         # comma separated
    link: str = ""
    bullets: List[str] = field(default_factory=list)


@dataclass
class CertificationEntry:
    name: str = ""
    issuer: str = ""
    date: str = ""
    credential_id: str = ""


@dataclass
class SkillGroup:
    category: str = ""           # e.g. "Languages", "Frameworks"
    items: List[str] = field(default_factory=list)


@dataclass
class LanguageEntry:
    language: str = ""
    proficiency: str = ""        # e.g. "Native", "Fluent", "Conversational"


@dataclass
class ResumeData:
    personal: PersonalInfo = field(default_factory=PersonalInfo)
    summary: str = ""
    experience: List[ExperienceEntry] = field(default_factory=list)
    education: List[EducationEntry] = field(default_factory=list)
    skills: List[SkillGroup] = field(default_factory=list)
    projects: List[ProjectEntry] = field(default_factory=list)
    certifications: List[CertificationEntry] = field(default_factory=list)
    languages: List[LanguageEntry] = field(default_factory=list)
    template: str = "Modern"
    accent_color: str = "#2563EB"

    # ---------- persistence ----------

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> "ResumeData":
        personal = PersonalInfo(**data.get("personal", {}))
        experience = [ExperienceEntry(**e) for e in data.get("experience", [])]
        education = [EducationEntry(**e) for e in data.get("education", [])]
        skills = [SkillGroup(**s) for s in data.get("skills", [])]
        projects = [ProjectEntry(**p) for p in data.get("projects", [])]
        certifications = [CertificationEntry(**c) for c in data.get("certifications", [])]
        languages = [LanguageEntry(**l) for l in data.get("languages", [])]
        return cls(
            personal=personal,
            summary=data.get("summary", ""),
            experience=experience,
            education=education,
            skills=skills,
            projects=projects,
            certifications=certifications,
            languages=languages,
            template=data.get("template", "Modern"),
            accent_color=data.get("accent_color", "#2563EB"),
        )

    @classmethod
    def from_json(cls, path: str) -> "ResumeData":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


def sample_resume() -> ResumeData:
    """Returns a filled-in example resume, useful for template previews and demos."""
    return ResumeData(
        personal=PersonalInfo(
            full_name="Alex Morgan",
            title="Senior Software Engineer",
            email="alex.morgan@email.com",
            phone="+1 (555) 123-4567",
            location="San Francisco, CA",
            linkedin="linkedin.com/in/alexmorgan",
            website="alexmorgan.dev",
            github="github.com/alexmorgan",
        ),
        summary=(
            "Results-driven software engineer with 7+ years building scalable web "
            "applications and distributed systems. Proven track record leading "
            "cross-functional teams to ship high-impact products used by millions "
            "of users. Passionate about clean architecture, mentorship, and "
            "developer tooling."
        ),
        experience=[
            ExperienceEntry(
                company="Nimbus Cloud Systems",
                role="Senior Software Engineer",
                location="San Francisco, CA",
                start_date="Jan 2022",
                end_date="Present",
                bullets=[
                    "Led migration of monolithic backend to microservices, reducing deployment time by 65%",
                    "Designed and implemented a real-time analytics pipeline processing 2M+ events/day",
                    "Mentored 4 junior engineers; established code review guidelines adopted org-wide",
                    "Reduced infrastructure costs by 30% through autoscaling and resource optimization",
                ],
            ),
            ExperienceEntry(
                company="BrightPath Technologies",
                role="Software Engineer",
                location="Austin, TX",
                start_date="Jun 2019",
                end_date="Dec 2021",
                bullets=[
                    "Built customer-facing dashboard used by 50,000+ monthly active users",
                    "Improved API response times by 40% through query optimization and caching",
                    "Collaborated with product and design to launch 3 major feature releases",
                ],
            ),
            ExperienceEntry(
                company="StartUp Labs",
                role="Junior Developer",
                location="Austin, TX",
                start_date="Jul 2017",
                end_date="May 2019",
                bullets=[
                    "Developed and maintained RESTful APIs using Python and Django",
                    "Wrote automated test suites, increasing code coverage from 45% to 85%",
                ],
            ),
        ],
        education=[
            EducationEntry(
                institution="University of Texas at Austin",
                degree="B.S.",
                field_of_study="Computer Science",
                location="Austin, TX",
                start_date="2013",
                end_date="2017",
                gpa="3.8/4.0",
                bullets=["Dean's List, 6 semesters", "President, Computer Science Society"],
            )
        ],
        skills=[
            SkillGroup(category="Languages", items=["Python", "JavaScript", "TypeScript", "Go", "SQL"]),
            SkillGroup(category="Frameworks", items=["React", "Django", "FastAPI", "Node.js"]),
            SkillGroup(category="Tools & Platforms", items=["AWS", "Docker", "Kubernetes", "PostgreSQL", "Redis"]),
            SkillGroup(category="Practices", items=["CI/CD", "Agile/Scrum", "TDD", "System Design"]),
        ],
        projects=[
            ProjectEntry(
                name="OpenMetrics",
                description="Open-source real-time metrics dashboard with plugin architecture",
                tech_stack="React, Node.js, WebSocket, InfluxDB",
                link="github.com/alexmorgan/openmetrics",
                bullets=["1,200+ GitHub stars", "Used by 200+ organizations"],
            ),
        ],
        certifications=[
            CertificationEntry(
                name="AWS Certified Solutions Architect – Professional",
                issuer="Amazon Web Services",
                date="2023",
                credential_id="AWS-PSA-88291",
            ),
        ],
        languages=[
            LanguageEntry(language="English", proficiency="Native"),
            LanguageEntry(language="Spanish", proficiency="Professional working proficiency"),
        ],
        template="Modern",
        accent_color="#2563EB",
    )
