# reportforge

> Burp XML in. Client-ready PDF out.

**Status: early development.** This repo is public research + planning until the first release.

reportforge is a command-line pentest report generator:

- Parses Burp Suite XML, OWASP ZAP and nuclei JSON exports
- Findings are plain Markdown — easy to edit, easy to diff
- Renders a polished PDF: executive summary, severity matrix (CVSS-mapped),
  technical appendix, remediation advice from reusable finding templates
- Zero web app, zero hosting: `pipx install reportforge`

Built for pentesters who would rather hack than format documents.

## Usage (planned)

    reportforge ./burp-export.xml -o report.pdf

## Documentation

- [docs/research.md](docs/research.md) — market research and competitive landscape
- [docs/roadmap.md](docs/roadmap.md) — development milestones toward v1.0.0

## License

MIT
