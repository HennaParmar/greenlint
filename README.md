<<<<<<< HEAD
<<<<<<< HEAD
=======
GreenLint — Sustainable Coding Linter (PoC)
>>>>>>> fada12d8ad08df1285531d18c92df6843ec2beb0


Prototype linter that flags code patterns likely to waste compute, time, and energy — helping teams write greener software.

✨ Features

Static analysis for Python with early sustainability heuristics:

PY001: Membership tests in loops → prefer set lookups.

PY002: Network requests in loops → batch / parallelise.

PY003: Costly string formatting in logging → use lazy logging.

Score out of 100 + per-rule counts.

JSON report for CI artifacts and dashboards.

Ready-to-use Azure DevOps pipeline; optional GitHub Actions.

🚀 Quick Start
# clone the repo
git clone https://github.com/HennaParmar/greenlint.git
cd greenlint

# install in editable mode (gives you the CLI entrypoint)
pip install --upgrade pip setuptools
pip install -e .

<<<<<<< HEAD
Open the JSON report to see findings, rule counts, and a naive score out of 100.
=======
# greenlint
Prototype linter for sustainable, energy-efficient coding.
>>>>>>> 092d4a6d488f202a454547ec7069235bfdb3a5e1
=======
# run against the example file
greenlint examples/bad_patterns.py --json greenlint_report.json


On Windows, if greenlint isn’t found on PATH, run:

python -m greenlint.cli examples/bad_patterns.py --json greenlint_report.json


Expected output:

=== GreenLint Prototype ===
Total findings: 3  |  Score: 94 / 100
By rule:
  - PY001: 1
  - PY002: 1
  - PY003: 1

Detail:
examples/bad_patterns.py:... PY001 ...
examples/bad_patterns.py:... PY002 ...
examples/bad_patterns.py:... PY003 ...
JSON report written to greenlint_report.json

📁 Project Structure
greenlint/
  __init__.py
  cli.py          # CLI entrypoint
  rules.py        # rule definitions (PY001–PY003)
  scanner.py      # walks files, builds AST, applies rules
  report.py       # scoring + summary
examples/
  bad_patterns.py

⚙️ Azure DevOps

The repo includes azure-pipelines.yml. Create a pipeline pointing to this file.

What it does:

Sets up Python 3.11

Installs the package (pip install -e .)

Runs greenlint on the repo

Publishes greenlint_report.json as a build artifact

Optional: add a quality gate step to soft-fail or fail the build based on findings.

🔧 Pre-commit (local checks)
pip install pre-commit
pre-commit install


This runs GreenLint before each commit to catch issues early.

🧪 Testing
# run a very small smoke test
python - << "PY"
from greenlint.scanner import scan_path
fs = scan_path("examples/bad_patterns.py")
print("findings:", len(fs))
PY

🗺️ Roadmap

Config file (greenlint.toml) for include/exclude paths, severities, and thresholds.

More rules:

Pandas vectorisation (avoid .apply/row loops)

Large file I/O in loops → chunking / buffering

N+1 DB queries (simple ORM heuristic)

Excessive JSON (de)serialisation in hot paths

Outputs: SARIF for PR annotations; HTML/Streamlit report.

Measured runs: optional CodeCarbon integration for rough energy estimates.

Multi-language: Java/Kotlin via javaparser/OpenRewrite; JS/TS via ESLint plugin.

🤝 Contributing

Issues and PRs welcome! For new rules, please include:

Rule ID & rationale

Example “bad” and “better” patterns

Tests that trigger the rule

📜 License

MIT — feel free to use, adapt, and improve.

🙌 Acknowledgements

Inspired by emerging Green Software practices (e.g., the Green Software Foundation’s principles) and community efforts to reduce software’s carbon impact.
>>>>>>> fada12d8ad08df1285531d18c92df6843ec2beb0
