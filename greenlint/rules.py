
import ast

class Finding:
    def __init__(self, file, lineno, rule_id, message, severity="MEDIUM"):
        self.file = file
        self.lineno = lineno
        self.rule_id = rule_id
        self.message = message
        self.severity = severity

    def to_dict(self):
        return {
            "file": self.file,
            "line": self.lineno,
            "rule": self.rule_id,
            "message": self.message,
            "severity": self.severity,
        }

class RuleBase:
    id = "GEN000"
    description = "Generic rule"
    severity = "MEDIUM"

    def check(self, file_path, tree):
        return []

class InefficientMembershipCheck(RuleBase):
    id = "PY001"
    description = "Use set for membership checks in loops"

    def check(self, file_path, tree):
        findings = []
        class Visitor(ast.NodeVisitor):
            def visit_For(self, node):
                for n in ast.walk(node):
                    if isinstance(n, ast.Compare) and any(isinstance(op, ast.In) for op in n.ops):
                        findings.append(Finding(file_path, n.lineno, "PY001",
                            "Membership test inside loop; consider using a set for O(1) lookups."))
                self.generic_visit(node)
        Visitor().visit(tree)
        return findings

class UnbatchedRequests(RuleBase):
    id = "PY002"
    description = "Potential unbatched network requests in loop"

    def check(self, file_path, tree):
        findings = []
        network_calls = {"requests.get", "requests.post", "requests.put", "requests.delete"}
        class Visitor(ast.NodeVisitor):
            def visit_For(self, node):
                for n in ast.walk(node):
                    if isinstance(n, ast.Call):
                        func = n.func
                        name = None
                        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                            name = f"{func.value.id}.{func.attr}"
                        if name in network_calls:
                            findings.append(Finding(file_path, n.lineno, "PY002",
                                "Network calls inside loops; batch or parallelise to reduce time/energy."))
                self.generic_visit(node)
        Visitor().visit(tree)
        return findings

class ExcessiveLogging(RuleBase):
    id = "PY003"
    description = "Excessive string formatting in logging calls"

    def check(self, file_path, tree):
        findings = []
        log_funcs = {"logging.debug", "logging.info"}
        class Visitor(ast.NodeVisitor):
            def visit_Call(self, node):
                func = node.func
                name = None
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    name = f"{func.value.id}.{func.attr}"
                if name in log_funcs and node.args:
                    if isinstance(node.args[0], (ast.JoinedStr, ast.Call)):
                        findings.append(Finding(file_path, node.lineno, "PY003",
                            "Use lazy logging (e.g., logging.debug('x=%s', x)) to avoid unnecessary string ops."))
                self.generic_visit(node)
        Visitor().visit(tree)
        return findings

# === AI Sustainability Rules ===

import os

class LargeModelFile(RuleBase):
    id = "AI001"
    description = "Model file exceeds recommended sustainable size (>500MB)"

    def check(self, file_path, tree=None):
        findings = []
        if file_path.endswith((".pt", ".pth", ".h5", ".onnx", ".joblib", ".pickle")):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb > 500:
                findings.append(Finding(
                    file_path,
                    0,
                    self.id,
                    f"Model file size {size_mb:.1f}MB — consider pruning or quantizing to reduce footprint."
                ))
        return findings


class TrainFromScratch(RuleBase):
    id = "AI002"
    description = "Training model from scratch — consider transfer learning or fine-tuning pre-trained models"

    def check(self, file_path, tree):
        findings = []
        class Visitor(ast.NodeVisitor):
            def visit_Call(self, node):
                if isinstance(node.func, ast.Attribute):
                    name = node.func.attr.lower()
                    if name in {"fit", "train"}:
                        findings.append(Finding(
                            file_path,
                            node.lineno,
                            "AI002",
                            "Detected model training call — check if using pre-trained weights to reduce compute."
                        ))
                self.generic_visit(node)
        Visitor().visit(tree)
        return findings
    
class PandasRowWiseOps(RuleBase):
    id = "PD001"
    description = "Row-wise pandas operations detected; prefer vectorisation"

    def check(self, file_path, tree):
        findings = []
        rule_id = self.id  # capture for inner class

        class V(ast.NodeVisitor):
            def visit_Call(self, node):
                # df.apply(..., axis=1) or df.iterrows()
                if isinstance(node.func, ast.Attribute):
                    attr = node.func.attr

                    # df.apply(..., axis=1)
                    if attr == "apply":
                        for kw in (node.keywords or []):
                            try:
                                if kw.arg == "axis" and getattr(kw.value, "value", None) == 1:
                                    findings.append(Finding(
                                        file_path, node.lineno, rule_id,
                                        "pandas apply(axis=1) is slow; prefer vectorised ops."
                                    ))
                            except Exception:
                                pass

                    # df.iterrows()
                    if attr == "iterrows":
                        findings.append(Finding(
                            file_path, node.lineno, rule_id,
                            "pandas iterrows() is slow; prefer vectorised ops."
                        ))
                self.generic_visit(node)

        V().visit(tree)
        return findings


class LargeFileIoInLoop(RuleBase):
    id = "IO001"
    description = "Potential large file I/O inside loop; use chunking/buffering"

    def check(self, file_path, tree):
        findings = []
        rule_id = self.id  # capture for inner class
        suspicious_funcs = {"read_csv", "read_json", "open"}

        class V(ast.NodeVisitor):
            def visit_For(self, node):
                for n in ast.walk(node):
                    if isinstance(n, ast.Call):
                        name = None
                        try:
                            if isinstance(n.func, ast.Attribute):
                                name = n.func.attr
                            elif isinstance(n.func, ast.Name):
                                name = n.func.id
                            if name in suspicious_funcs:
                                findings.append(Finding(
                                    file_path, getattr(n, "lineno", getattr(node, "lineno", 0)), rule_id,
                                    "File I/O called inside loop; consider chunked reads or preloading."
                                ))
                        except Exception:
                            pass
                self.generic_visit(node)

        V().visit(tree)
        return findings



ALL_RULES = [
    InefficientMembershipCheck(),
    UnbatchedRequests(),
    ExcessiveLogging(),
    LargeModelFile(),
    TrainFromScratch(),
    PandasRowWiseOps(),
    LargeFileIoInLoop()
]
