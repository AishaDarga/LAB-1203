# LAB-1203 — Student Material

**Build a Management Report Agent on watsonx Orchestrate and embed it in Planning Analytics**

This repository contains everything you need to complete the lab hands-on exercises.

---

## Contents

| Path | Description |
|---|---|
| `LAB-1203-GUIDE.md` | Step-by-step lab guide (Markdown) |
| `LAB-1203-GUIDE.pdf` | Same guide as a PDF for offline reading |
| `agents/management_report_generator.agent.yaml` | watsonx Orchestrate agent definition — import this via the ADK |
| `tools/publish_report_pdf.py` | Python tool that builds and uploads the PDF report to Cloud Object Storage |
| `tools/requirements.txt` | Python dependencies for the tool (`reportlab`, `boto3`) |

---

## Lab structure

| Part | What you do |
|---|---|
| **Part 0** | Prerequisites and security rules |
| **Part 1** | Set up the ADK and log in to wxO |
| **Part 2** | Connect the PA MCP server to wxO |
| **Part 3** | Build the agent (data and analysis only) |
| **Part 4** | Test the agent (data only) |
| **Part 5** | Run `orchestrate connections set-credentials` with the values your instructor gives you — this stores them inside wxO so the report tool can upload PDFs |
| **Part 6** | Build the report tool and add it to the agent |
| **Part 7** | Test the full report flow |
| **Part 8** | Embed the agent in the PA workspace |
| **Part 9** | Troubleshooting |
| **Part 10** | Clean-up |

Start with **`LAB-1203-GUIDE.md`** and follow the parts in order.

> **Shared COS bucket:** The instructor has already created the Cloud Object Storage bucket and HMAC credentials. In Part 5 you do **not** create a bucket — you only store the five values your instructor hands out into a local wxO connection (`cos_reports`). Every student writes to the same bucket; file names include a timestamp and random ID so they never overwrite each other.

> **No credentials in this repo:** COS keys, private keys, and environment-specific IDs are never committed here. Your instructor will supply them verbally or via a shared channel during the lab.
