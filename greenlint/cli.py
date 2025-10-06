
import argparse, json
from .scanner import scan_path
from .report import summarise

def main():
    parser = argparse.ArgumentParser(description="GreenLint: prototype sustainable-coding linter")
    parser.add_argument("target", help="File or directory to scan")
    parser.add_argument("--json", dest="json_out", help="Write JSON report to this path")
    args = parser.parse_args()

    findings = scan_path(args.target)
    summary = summarise(findings)

    print("=== GreenLint Prototype ===")
    print(f"Total findings: {summary['total_findings']}  |  Score: {summary['score']} / 100")
    print("By rule:")
    for rid, count in summary["by_rule"].items():
        print(f"  - {rid}: {count}")
    print("\nDetail:")
    for f in findings[:50]:
        rid = getattr(f, "rule_id", getattr(f, "rule", "UNKNOWN"))
        print(f"{f.file}:{f.lineno} {rid} {f.message}")


    if args.json_out:
        out = {
            "summary": summary,
            "findings": [fi.to_dict() for fi in findings],
        }
        with open(args.json_out, "w", encoding="utf-8") as fp:
            json.dump(out, fp, indent=2)
        print(f"\nJSON report written to {args.json_out}")

if __name__ == "__main__":
    main()
