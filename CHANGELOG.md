# Changelog

## v0.2.0 — 2026-10-20

- OWASP ZAP alerts JSON parser
- nuclei JSONL parser (severity mapped to report scale)
- Multi-tool merging: one report from Burp + ZAP + nuclei inputs
- Severity matrix with CVSS v3.1 qualitative bands, in the markdown report
- CLI: --zap/--nuclei alongside --burp
- 6 new tests (15 total)

## v0.1.0 — 2026-10-20

- Burp Suite issues XML parser (fields degrade gracefully, never crash a report)
- Finding format with severity normalization and severity-ordered output
- Pure-Python PDF writer (no dependencies): executive summary, severity
  matrix captioning, technical appendix, multi-page overflow
- Markdown report output alongside PDF
- CLI: --burp/--out/--md/--engagement; sample-issues.xml included
- 9 offline tests; PDF verified with an independent parser (pypdf)
