
import ast
from pathlib import Path
from .rules import ALL_RULES

def scan_path(path):
    path = Path(path)
    files = list(path.rglob("*.py")) if path.is_dir() else [path]
    findings = []
    for f in files:
        try:
            code = f.read_text(encoding="utf-8")
            tree = ast.parse(code)
        except Exception:
            continue
        for rule in ALL_RULES:
            findings.extend(rule.check(str(f), tree))
    return findings
