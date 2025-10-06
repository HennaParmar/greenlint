
# GreenLint (Starter Kit v0.2)

A tiny proof‑of‑concept linter that flags code patterns likely to waste compute, time, and energy.

## Quick start (local)

```bash
pip install --upgrade pip setuptools
pip install -e .
greenlint examples/bad_patterns.py --json greenlint_report.json
```

Open the JSON report to see findings, rule counts, and a naive score out of 100.
