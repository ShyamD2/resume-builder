#!/usr/bin/env python3
"""
resume_cli.py - Command line interface for the Advanced Resume Builder.

Examples:
    # Generate a PDF from a JSON profile
    python3 resume_cli.py -i profiles/my_resume.json -o output/my_resume.pdf

    # Choose a template and accent color
    python3 resume_cli.py -i profiles/my_resume.json -o output/my_resume.pdf --template Sidebar --accent "#0F766E"

    # Also export ATS-friendly plain text
    python3 resume_cli.py -i profiles/my_resume.json -o output/my_resume.pdf --ats-text output/my_resume.txt

    # Print a resume quality score / suggestions
    python3 resume_cli.py -i profiles/my_resume.json --score

    # Generate the built-in sample resume in all 4 templates
    python3 resume_cli.py --sample --outdir output/samples
"""

import argparse
import os
import sys

from resume_data import ResumeData, sample_resume
from resume_pdf import render_resume, TEMPLATES
from resume_text import to_ats_text, analyze_resume


def build_parser():
    p = argparse.ArgumentParser(description="Advanced Resume Builder (CLI)")
    p.add_argument("-i", "--input", help="Path to a resume JSON profile")
    p.add_argument("-o", "--output", help="Output PDF path")
    p.add_argument("--template", choices=list(TEMPLATES.keys()), help="Template to use (overrides profile)")
    p.add_argument("--accent", help="Accent color hex, e.g. #2563EB (overrides profile)")
    p.add_argument("--ats-text", help="Also export ATS-friendly plain text to this path")
    p.add_argument("--score", action="store_true", help="Print a resume quality score and suggestions")
    p.add_argument("--sample", action="store_true", help="Use the built-in sample resume instead of --input")
    p.add_argument("--outdir", help="When used with --sample, generate all templates into this directory")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.sample and args.outdir:
        data = sample_resume()
        os.makedirs(args.outdir, exist_ok=True)
        for tpl in TEMPLATES:
            data.template = tpl
            path = os.path.join(args.outdir, f"sample_{tpl.lower()}.pdf")
            render_resume(data, path, template=tpl)
            print(f"Generated: {path}")
        return

    if args.sample:
        data = sample_resume()
    elif args.input:
        if not os.path.exists(args.input):
            print(f"Error: input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        data = ResumeData.from_json(args.input)
    else:
        parser.error("Provide --input <profile.json> or use --sample")
        return

    if args.template:
        data.template = args.template
    if args.accent:
        data.accent_color = args.accent

    if args.score:
        result = analyze_resume(data)
        print(f"Resume Score: {result['score']}/100")
        print(f"Word count: {result['word_count']}")
        if result["issues"]:
            print("\nIssues:")
            for i in result["issues"]:
                print(f"  - {i}")
        if result["tips"]:
            print("\nSuggestions:")
            for t in result["tips"]:
                print(f"  - {t}")
        if not args.output:
            return

    if args.output:
        render_resume(data, args.output, template=data.template)
        print(f"PDF saved to: {args.output}")

    if args.ats_text:
        with open(args.ats_text, "w", encoding="utf-8") as f:
            f.write(to_ats_text(data))
        print(f"ATS text saved to: {args.ats_text}")

    if not args.output and not args.ats_text and not args.score:
        parser.error("Nothing to do — specify --output, --ats-text, or --score")


if __name__ == "__main__":
    main()
