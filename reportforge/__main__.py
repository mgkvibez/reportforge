"""CLI: python -m reportforge --burp issues.xml --out report.pdf"""
import argparse
import sys

from .burp import parse_issues
from .render import to_markdown, to_pdf


def main(argv=None):
    parser = argparse.ArgumentParser(prog="reportforge",
                                     description="Scanner output to client-ready reports")
    parser.add_argument("--burp", help="path to a Burp Suite issues XML export")
    parser.add_argument("--out", default="report.pdf", help="PDF output path")
    parser.add_argument("--md", dest="markdown_out", default=None, help="markdown output path")
    parser.add_argument("--engagement", default="Security assessment",
                        help="engagement title for the report")
    args = parser.parse_args(argv)

    if not args.burp:
        parser.error("--burp is required (ZAP and nuclei parsers are on the roadmap)")

    findings = parse_issues(args.burp)
    if not findings:
        print("no findings parsed from the export", file=sys.stderr)

    with open(args.out, "wb") as fh:
        fh.write(to_pdf(findings, engagement=args.engagement))
    print(f"{len(findings)} finding(s) -> {args.out}")

    if args.markdown_out:
        with open(args.markdown_out, "w", encoding="utf-8") as fh:
            fh.write(to_markdown(findings, engagement=args.engagement) + "\n")
        print(f"markdown -> {args.markdown_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
