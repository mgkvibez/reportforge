"""CLI: reportforge --burp a.xml b.xml --zap c.json --nuclei d.jsonl

Multiple inputs merge into one report (multi-tool / multi-engagement).
"""
import argparse
import sys

from .burp import parse_issues
from .zap import parse_alerts
from .nuclei import parse_results
from .finding import merge_findings
from .render import to_markdown, to_pdf, RULESET_VERSION


def collect(args):
    raw_findings = []
    if args.burp:
        files = args.burp if isinstance(args.burp, list) else [args.burp]
        for f in files:
            raw_findings.extend(parse_issues(f, source_name=f))
    if args.zap:
        files = args.zap if isinstance(args.zap, list) else [args.zap]
        for f in files:
            raw_findings.extend(parse_alerts(f, source_name=f))
    if args.nuclei:
        files = args.nuclei if isinstance(args.nuclei, list) else [args.nuclei]
        for f in files:
            raw_findings.extend(parse_results(f, source_name=f))
    return merge_findings(raw_findings)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="reportforge",
                                     description="Scanner output to client-ready reports")
    parser.add_argument("--burp", nargs="+", help="path(s) to Burp Suite issues XML export")
    parser.add_argument("--zap", nargs="+", help="path(s) to ZAP alerts JSON export")
    parser.add_argument("--nuclei", nargs="+", help="path(s) to nuclei JSONL output")
    parser.add_argument("--out", default="report.pdf", help="PDF output path")
    parser.add_argument("--md", dest="markdown_out", default=None, help="markdown output path")
    parser.add_argument("--engagement", default="Security assessment",
                        help="engagement title for the report")
    parser.add_argument("--title", help="custom document title")
    parser.add_argument("--subtitle", help="custom document subtitle")
    parser.add_argument("--footer", help="custom document footer text")
    parser.add_argument("--accent", help="accent color in hex (e.g. #0055ff)")
    args = parser.parse_args(argv)

    if not (args.burp or args.zap or args.nuclei):
        parser.error("at least one of --burp, --zap, --nuclei is required")

    findings = collect(args)
    if not findings:
        print(f"no issues found by ruleset {RULESET_VERSION}", file=sys.stderr)

    md = to_markdown(
        findings,
        engagement=args.engagement,
        title=args.title,
        subtitle=args.subtitle or "",
        footer=args.footer or "",
        accent=args.accent,
    )

    pdf_bytes = to_pdf(
        findings,
        engagement=args.engagement,
        title=args.title,
        subtitle=args.subtitle or "",
        footer=args.footer or "",
        accent=args.accent,
    )

    with open(args.out, "wb") as fh:
        fh.write(pdf_bytes)
    print(f"{len(findings)} finding(s) -> {args.out}")

    if args.markdown_out:
        with open(args.markdown_out, "w", encoding="utf-8") as fh:
            fh.write(md + "\n")
        print(f"markdown -> {args.markdown_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
