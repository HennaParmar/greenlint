🌿 GreenLint — Sustainable Software Analysis Tool

Developed at CGI by Henna Parmar

GreenLint helps developers identify energy-intensive or inefficient code patterns and provides actionable guidance for writing greener, more efficient software.
It aligns with the CGI Green Software Guide principles of measurement, optimisation, and carbon-aware engineering

green_software_guide

.

🧩 What GreenLint Does

Code Sustainability Scanning — detects inefficient patterns that waste energy or bandwidth.

Multi-Language Support — Python, JavaScript/Node.js, Docker, and data workflows.

Actionable Reports — generates a greenlint_report.json compatible with the interactive Streamlit dashboard.

Lifecycle Integration — runs locally or inside CI/CD (Azure DevOps, GitHub Actions).

Education & Awareness — shows “before/after” code examples and aligns each finding to CGI’s green-software principles.

🔍 Example Rule Categories
Area	Example Rule	Purpose
Efficiency	PY001 – Membership test in loops → use sets	Reduces algorithmic complexity and CPU time.
Network	GLNET001 – Network calls in loops	Encourages batching / parallelisation to cut idle compute.
Web	GLWEB001 – Missing compression middleware	Reduces transfer size and energy use.
Containers	CT001–CT006 – Docker best practices	Promotes minimal images and non-root builds.
Data & Assets	IMG001 / APIJSON001	Flags large images or JSON payloads to align with the guide’s storage-optimisation principle

green_software_guide

.
🧠 How It Aligns With the CGI Green Software Guide
Guide Principle	GreenLint Feature
1. Measurement	Establishes a sustainability baseline via rule counts & trend dashboard

green_software_guide

.
2. Efficient Use of Hardware	Encourages reuse and optimisation of compute and memory resources.
3. Storage Optimisation	Detects large or redundant data assets and uncompressed media.
4. Carbon-Aware Engineering	Plans CI/CD execution during low-carbon periods (future roadmap).
5. Energy Efficiency	Flags unnecessary loops, unoptimised assets, and missing caching.
6. Carbon Efficiency	Promotes containerisation and cloud scalability best practices.
7. User Carbon Awareness	Provides visual feedback on potential CO₂e savings per fix.
🚀 Quick Start
# Clone and enter the repo
git clone https://github.com/HennaParmar/greenlint.git
cd greenlint

# (Optional) create a virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt   # or pip install streamlit pandas

# Run a scan (Python or JS/Docker project)
python greenlint_js_scanner.py --path . --out greenlint_report.json

# Launch the dashboard
streamlit run dashboard.py


Upload your greenlint_report.json and explore findings, before/after suggestions, and rule trends.

🔄 Integration Example (Azure DevOps)

GreenLint can run automatically in pipelines:

- task: UsePythonVersion@0
  inputs: { versionSpec: '3.11' }

- script: |
    python greenlint_js_scanner.py --path . --out greenlint_report.json
  displayName: 'Run GreenLint'

- task: PublishBuildArtifacts@1
  inputs:
    PathtoPublish: greenlint_report.json
    ArtifactName: greenlint

🛣️ Roadmap — Next Milestones
Short Term (Q4 2025 – Q1 2026)

Pilot on HMCTS Juror Public Portal project.

Conduct developer user-research interviews to refine rule accuracy and UX.

Publish initial metrics on code efficiency and carbon reduction.

Medium Term (2026)

Expand rule library: cloud efficiency, containerisation, and data-pipeline optimisation.

Integrate into Azure DevOps / GitHub Actions.

Launch internal CGI Developer Sustainability Community.

Long Term (2026 – 2027)

Add multi-language support (Java, Go, TypeScript).

Implement carbon-aware scheduling and “Greenness Index”.

Co-author a CGI × Green Software Foundation white paper.

📈 Future Opportunities

Dynamic Measurement: integrate CodeCarbon or DataTwin360 for real-time power estimates

green_software_guide

.

Storage & Data Lifecycle Audits: automatically detect redundant datasets.

User Carbon Awareness: provide dashboard visualisation of CO₂e avoided.

Procurement Alignment: include supplier-compliance checks following the guide’s green-purchasing criteria

green_software_guide

.

📫 Contact

Henna Parmar
Technical Graduate – Government & Justice, CGI
📧 henna.parmar@cgi.com
 📍 London Office
🔗 github.com/HennaParmar/greenlint