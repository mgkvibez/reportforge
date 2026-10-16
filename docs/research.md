# RESEARCH — reportforge
Updated: 2026-10-16

## Market thesis
Every pentester hates writing reports. The category leader is pwndoc (2.9k
stars) but it is a heavyweight self-hosted Node web app from 2016. Nobody has
shipped a fast, pip-installable CLI that eats raw tool output (Burp XML, ZAP,
nuclei JSON) and produces a polished, client-ready PDF.

## Competitive landscape (GitHub, Oct 2026)
| Repo | Stars | Gap we exploit |
|---|---|---|
| pwndoc/pwndoc | 2,912 | Heavy Node web app, needs hosting; we are a CLI, pipx install |
| kac89/vulnrepo | 584 | Web app again; end-to-end encryption is overkill for report drafting |
| pwndoc-ng/pwndoc-ng | 460 | Fork of the same heavyweight model |
| everything else | <30 | Small, abandoned, or Word-template scripts |

## Positioning
"Burp XML in, signed PDF out." Reusable finding templates, severity mapped to
CVSS, executive summary + technical appendix, zero web app. Markdown-first:
findings are plain Markdown, easy to edit, rendered to PDF.

## Launch playbook
- pipx install reportforge; reportforge ./burp-export.xml -o report.pdf
- Demo GIF: drag XML in, watch PDF build, in the first screen of README
- Launch: r/netsec, r/Pentesting, pentest Discord/Slack communities, Show HN
- v1.0.0 release with prebuilt binaries for the top-3 findings formats
