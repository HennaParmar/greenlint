
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

ALL_RULES = [InefficientMembershipCheck(), UnbatchedRequests(), ExcessiveLogging()]
