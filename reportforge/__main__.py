"""CLI: reportforge --burp issues.xml --zap alerts.json --nuclei out.jsonl

Multiple inputs merge into one report (multi-tool engagements).
"""
import argparse
import sys

from .burp import parse_issues
from .zap import parse_alerts
from .nuclei import parse_results
from .render import to_markdown, to_pdf
from .severity_matrix import matrix, matrix_markdown


def collect(args):
    findings = []
    if args.burp:
        findings += parse_issues(args.burp)
    if args.zap:
        findings += parse_alerts(args.zap)
    if args.nuclei:
        findings += parse_results(args.nuclei)
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(prog="reportforge",
                                     description="Scanner output to client-ready reports")
    parser.add_argument("--burp", help="path to a Burp Suite issues XML export")
    parser.add_argument("--zap", help="path to a ZAP alerts JSON export")
    parser.add_argument("--nuclei", help="path to nuclei JSONL output")
    parser.add_argument("--out", default="report.pdf", help="PDF output path")
    parser.add_argument("--md", dest="markdown_out", default=None, help="markdown output path")
    parser.add_argument("--engagement", default="Security assessment",
                        help="engagement title for the report")
    args = parser.parse_args(argv)

    if not (args.burp or args.zap or args.nuclei):
        parser.error("at least one of --burp, --zap, --nuclei is required")

    findings = collect(args)
    if not findings:
        print("no findings parsed from the inputs", file=sys.stderr)

    md = to_markdown(findings, engagement=args.engagement)
    md += "\n## Severity matrix\n\n" + matrix_markdown(matrix(findings)) + "\n"

    with open(args.out, "wb") as fh:
        fh.write(to_pdf(findings, engagement=args.engagement))
    print(f"{len(findings)} finding(s) -> {args.out}")

    if args.markdown_out:
        with open(args.markdown_out, "w", encoding="utf-8") as fh:
            fh.write(md + "\n")
        print(f"markdown -> {args.markdown_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
