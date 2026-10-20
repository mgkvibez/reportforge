# Changelog

## v0.1.0 — 2026-10-20

- Burp Suite issues XML parser (fields degrade gracefully, never crash a report)
- Finding format with severity normalization and severity-ordered output
- Pure-Python PDF writer (no dependencies): executive summary, severity
  matrix captioning, technical appendix, multi-page overflow
- Markdown report output alongside PDF
- CLI: --burp/--out/--md/--engagement; sample-issues.xml included
- 9 offline tests; PDF verified with an independent parser (pypdf)
