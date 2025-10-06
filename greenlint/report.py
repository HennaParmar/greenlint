
from collections import Counter

def summarise(findings):
    counts = Counter(f.rule_id for f in findings)
    total = len(findings)
    score = max(0, 100 - total * 2)
    by_severity = Counter(f.severity for f in findings)
    return {
        "total_findings": total,
        "score": score,
        "by_rule": dict(counts),
        "by_severity": dict(by_severity),
    }
