# LAB-1203 — Build a Management Report Agent on watsonx Orchestrate and embed it in Planning Analytics

> **IBM TechXchange 2026 · Instructor-led hands-on lab**

In this 75-minute lab you will build a watsonx Orchestrate agent that reads live data from a Planning Analytics database, generates Budget vs Actual analysis, publishes a PDF report to Cloud Object Storage, and runs directly inside the PA workspace chat panel.

---

## What you will build

```
PA workspace (you)
      │  ① ask for a report
      ▼
watsonx Orchestrate agent
  ├── pa_reporting toolkit  ──── HTTPS ──▶  PA MCP server (24Retail cube)
  └── publish_report_pdf    ── S3 API ──▶  IBM Cloud Object Storage
                                                    │
                                    ④ pre-signed link (1 hr)
                                                    │
                                                    ▼
                                            back to PA chat
```

---

## Repo contents

| File / Folder | Description |
|---|---|
| `LAB-1203-GUIDE.pdf` | Full step-by-step lab guide (cover page, ToC, Parts 0–10) |
| `LAB-1203-deck.pdf` | Instructor intro deck (6 slides, 16:9) |
| `agents/management_report_generator.agent.yaml` | Agent definition — import with the ADK |
| `tools/publish_report_pdf.py` | Python tool — builds the PDF and uploads it to COS |
| `tools/requirements.txt` | Tool dependencies (`reportlab`, `boto3`) |

> Screenshots and images are excluded from this repo (listed in `.gitignore`) and shared separately by the instructor.

---

## Lab structure

| Part | What you do | Time |
|---|---|---|
| **0** | Prerequisites and security rules | 5 min |
| **1** | Install the ADK and log in to wxO | 10 min |
| **2** | Connect the PA MCP server to wxO | 15 min |
| **3** | Import the agent (data + analysis only) | 15 min |
| **4** | Test the agent against the 24Retail cube | 15 min |
| **5** | Store the instructor's COS credentials in wxO | 5 min |
| **6** | Import the PDF tool and wire it to the agent | 20 min |
| **7** | Test the full report flow end-to-end | 20 min |
| **8** | Embed the agent in the PA workspace | 25 min |
| **9** | Troubleshooting | reference |
| **10** | Clean-up | 5 min |

Start with **`LAB-1203-GUIDE.pdf`** and follow the parts in order.

---

## Before you start

- **Python 3.11–3.13** and `openssl` must be installed on your machine.
- The ADK (`ibm-watsonx-orchestrate`) must be installed and a wxO environment activated.
- Your instructor will hand out: PA host, tenant ID, PA API key, and the five COS values (endpoint, region, bucket, access key, secret).

> **Shared COS bucket:** The instructor pre-created the Cloud Object Storage bucket. In Part 5 you do **not** create anything — you run one `orchestrate connections set-credentials` command with the values your instructor gives you. Every student writes to the same bucket; file names include a timestamp and random ID so reports never overwrite each other.

> **No credentials in this repo.** COS keys, private keys, and environment IDs are never committed here.

---

## Quick-start commands

```bash
# Part 1 — activate your wxO environment
read -s WXO_KEY
orchestrate env activate lab-1203 --url "<WXO_URL>" --api-key "$WXO_KEY"
unset WXO_KEY

# Part 3 — import the agent
orchestrate agents import -f agents/management_report_generator.agent.yaml

# Part 6 — import the tool
orchestrate tools import -k python -f tools/publish_report_pdf.py \
  -r tools/requirements.txt --app-id cos_reports
```

---

## Authors

| Name | Role |
|---|---|
| Aisha Mohammed Farooq Darga | AI Engineer, Service Engineering — US Select Territory |
| Sami El Cheikh | Senior Product Manager, IBM Planning Analytics |
