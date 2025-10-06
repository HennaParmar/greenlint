
from greenlint.scanner import scan_path

def test_scan_examples():
    findings = scan_path('examples/bad_patterns.py')
    assert len(findings) >= 1
