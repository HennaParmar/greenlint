# 🌿 GreenLint — Sustainable Software Analysis Tool

**Developed at [CGI](https://www.cgi.com/uk/en) by Henna Parmar**  
_Aligned with the CGI Green Software Guide principles of measurement, optimisation, and carbon-aware engineering._

---

## 🧩 Overview

**GreenLint** helps developers identify **energy-intensive or inefficient code patterns** and provides actionable guidance for writing greener, more efficient software.

It supports multiple languages and environments — from frontend JavaScript to backend Dockerfiles — and generates rich JSON reports viewable in an **interactive Streamlit dashboard**.

---

## 🚀 What GreenLint Does

| Category | Description |
|-----------|--------------|
| **Code Sustainability Scanning** | Detects inefficient patterns that waste energy or bandwidth. |
| **Multi-Language Support** | Works with **Python**, **JavaScript / Node.js**, **Docker**, and **data workflows**. |
| **Actionable Reports** | Produces `greenlint_report.json` for visual exploration in the Streamlit dashboard. |
| **Lifecycle Integration** | Runs locally or inside CI/CD (Azure DevOps, GitHub Actions). |
| **Education & Awareness** | Provides “Before / After” examples and links findings to CGI’s Green Software Guide principles. |

---

## 🔍 Example Rule Categories

| Area | Example Rule | Purpose | Efficiency |
|------|---------------|----------|-------------|
| **Algorithms** | `PY001` – Membership tests in loops → use sets | Reduces algorithmic complexity and CPU time. | 🧠 |
| **Network** | `GLNET001` – Network calls inside loops | Encourages batching / parallelisation to cut idle compute. | 🌐 |
| **Web** | `GLWEB001` – Missing compression middleware | Reduces transfer size and energy use. | ⚙️ |
| **Containers** | `CT001–CT006` – Dockerfile best practices | Promotes minimal images and non-root builds. | 🐳 |
| **Data & Assets** | `IMG001`, `APIJSON001` | Flags large images or JSON payloads; aligns with storage optimisation principles. | 💾 |

---

## 🧠 Alignment with the CGI Green Software Guide

| **Guide Principle** | **GreenLint Feature** |
|----------------------|-----------------------|
| **1. Measurement** | Establishes a sustainability baseline via rule counts & dashboard trends. |
| **2. Efficient Use of Hardware** | Encourages reuse and optimisation of compute and memory resources. |
| **3. Storage Optimisation** | Detects large or redundant data assets and uncompressed media. |
| **4. Carbon-Aware Engineering** | (Roadmap) Plans CI/CD execution during low-carbon grid periods. |
| **5. Energy Efficiency** | Flags unnecessary loops, missing caching, or inefficient network use. |
| **6. Carbon Efficiency** | Promotes containerisation, scaling, and efficient runtime configs. |
| **7. User Carbon Awareness** | Displays potential CO₂e savings per optimisation in the dashboard. |

---

## ⚙️ Quick Start

### 1️⃣ Clone the repo
```bash
git clone https://github.com/HennaParmar/greenlint.git
cd greenlint
2️⃣ (Optional) Create a virtual environment
bash
Copy code
python -m venv .venv
. .venv/Scripts/activate  # (Windows)
# source .venv/bin/activate  # (macOS/Linux)
3️⃣ Install dependencies
bash
Copy code
pip install -r requirements.txt
# or
pip install streamlit pandas
4️⃣ Run a scan
bash
Copy code
node greenlint-js-scan.js
node greenlint-docker-check.js
node greenlint-merge.js
This will generate greenlint_js.json, greenlint_docker.json, and greenlint_report.json.

5️⃣ Launch the dashboard
bash
Copy code
streamlit run dashboard.py
Upload your greenlint_report.json and explore:

🔎 Detected inefficiencies

🧠 Before / After examples

📈 Rule distribution trends

🔄 Example CI/CD Integration (Azure DevOps)
You can add GreenLint as a quality gate in your pipeline:

yaml
Copy code
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.11'

- script: |
    node greenlint-js-scan.js
    node greenlint-docker-check.js
    node greenlint-merge.js
  displayName: 'Run GreenLint'

- task: PublishBuildArtifacts@1
  inputs:
    PathtoPublish: greenlint_report.json
    ArtifactName: greenlint

## Juror Digital Public Portal
===========================
- Author: CGI
- Owner: HMCTS
- Technologies: NodeJS, Express, Nunjucks
- Standards: [GDS Design System](https://design-system.service.gov.uk/)

### What is it?
The Juror Digital solution for prospective Jurors provides an online service to allow people to respond via a website instead of using the paper form. Jurors provide their Juror Number (as provided on the invitation letter), surname and postcode. They are taken through the steps to confirm their details, and on to providing their response (acceptance, deferral or excusal), and to provide any supporting documentation. Upon completion, they are provided with confirmation by email that their response has been submitted for processing. 

### Where is it implemented? 
[Reply to a jury summons](https://www.gov.uk/reply-jury-summons)


