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

Overview
GreenLint is a rule-based static analysis tool that detects code patterns known to waste energy, bandwidth, or compute resources — and then estimates their sustainability impact.
It doesn’t run or execute your code (so it’s safe and fast); instead, it reads source files as text and applies a library of heuristics (regular expressions and small logic checks) to find inefficiencies.

🧩 The Core Scanning Engine
When you run:

node greenlint-js-scan.js
GreenLint performs these steps:
1️⃣ Walk the project tree
It recursively reads files under your defined folders (client/, server/), skipping things like node_modules, .git, dist, etc.

const entries = fs.readdirSync(dir, { withFileTypes: true });
for (const e of entries) {
  const p = path.join(dir, e.name);
  if (e.isDirectory()) walk(p);
  else if (/\.(js|mjs|cjs)$/i.test(e.name)) scanJs(p);
}
2️⃣ Parse each file as text
For every .js, .mjs, or .cjs file, it:
	• reads the content into a string,
	• splits it into lines,
	• checks each line (and sometimes its neighbours) for rule matches.
3️⃣ Apply heuristic rules
Each rule is a small self-contained pattern detector.
For example:
🕸️ GLNET001 — Network call inside a loop

const netRegex = /\b(fetch|axios|request)\b/i;
if (/\b(for|while)\b/.test(lines[i])) {
  if (netRegex.test(nextLines) && (/await|\.then/.test(nextLines))) {
    addFinding(file, j+1, "GLNET001",
      "Network call inside loop; prefer batching (Promise.all).");
  }
}
This detects code that repeatedly calls APIs inside loops — a wasteful pattern in both CPU and network energy terms.
🌐 GLWEB001 — Missing compression middleware

const usesExpress = /\brequire\(['"]express['"]\)/.test(text);
const hasCompression = /\brequire\(['"]compression['"]\)/.test(text);
if (usesExpress && !hasCompression) {
  addFinding(file, line, "GLWEB001",
    "Express app missing compression middleware (gzip/Brotli).");
}
It simply checks if your Express app uses express() but never imports or configures compression.
🧱 CT001 — Docker base image not minimal
In greenlint-docker-check.js:

if (/^FROM\s+node:(?!.*alpine)/i.test(line)) {
  add("CT001", i+1, "Base image not alpine/minimal; prefer node:alpine.");
}
That rule spots Dockerfiles based on heavyweight images.

📦 What each scanner produces
Each scanner builds a JSON report like this:

{
  "summary": { "total_findings": 42 },
  "findings": [
    {
      "file": "client/config/express.js",
      "line": 10,
      "rule": "GLWEB001",
      "message": "Express app missing compression middleware.",
      "severity": "LOW"
    }
  ]
}
Then the merge script (greenlint-merge.js) combines:
	• greenlint_js.json
	• greenlint_docker.json
into:

greenlint_report.json
and tags each finding with the project name (juror-public, juror-api, etc.).
Finally, your all-project script (greenlint-scan-all.js) merges everything into:

reports/greenlint_all_projects.json

🧠 How “testing” and “checking” actually work
Each rule is like a mini-test, but instead of executing functions, it tests the code structure against known efficiency bad smells.
Example mapping:
Test Question	What GreenLint Checks	Why it matters
Does code compress HTTP responses?	looks for app.use(compression())	reduces data transfer energy
Are network requests batched?	looks for fetch() inside loops	avoids repeated connections
Are static assets cached?	finds express.static() without options	prevents redundant downloads
Are Docker images minimal?	checks for node:alpine base image	reduces build size and storage
Are templates cached in prod?	finds nunjucks({ watch: true })	prevents repeated I/O
Are console logs removed?	detects console.log() in app code	avoids unnecessary I/O and clutter
Every match becomes a “finding” — essentially a test failure for sustainability.

🧮 How the Carbon/Cost Estimates are Calculated
Once the findings are uploaded into the dashboard, the carbon estimator section uses:
	• Counts of each rule (e.g., 5 × GLWEB001, 3 × GLNET001)
	• Heuristic efficiency factors (e.g., each GLWEB001 ≈ 0.4% potential CO₂e reduction)
	• Baseline energy or carbon figure (entered by you)
	• Grid intensity (gCO₂e/kWh) and £/kWh inputs
Then:

total_reduction = 1 - Π(1 - per_occurrence^count)
saved_kgCO₂e    = baseline_kg * total_reduction
saved_kWh       = (saved_kgCO₂e * 1000) / grid_intensity
saved_cost      = saved_kWh * electricity_price

This gives an estimated impact of applying GreenLint’s fixes — conceptually similar to Azure’s Carbon Optimization dashboard.

🧩 Key Takeaways for Presentations
	• Not AI — deterministic, explainable pattern matching.
	• No execution — static text scanning.
	• Lightweight — runs fast, no dependencies or cloud APIs.
	• Explainable — every rule is visible in the code and dashboard.
	• Extendable — you can add new rules easily (just one if block).
	• Measurable — findings can be converted into energy and CO₂e savings estimates.

🔧 Example developer workflow
	1. Developer runs:

node greenlint-js-scan.js
	2. GreenLint finds:

GLWEB001  Express missing compression (client/config/express.js:10)
GLNET001  Network call in loop (client/utils/api.js:45)
	3. Developer fixes these issues.
	4. Re-run scanner — zero findings ✅
	5. Dashboard recalculates lower projected CO₂e footprint 🌍
<img width="925" height="3161" alt="image" src="https://github.com/user-attachments/assets/a7eedca2-d15b-4149-94a1-c90fa6576a81" />
