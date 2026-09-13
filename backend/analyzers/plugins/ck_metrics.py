import ast
import re
from pathlib import Path
from typing import Dict, Any, List, Set
from backend.analyzers.base import AnalyzerPlugin, PluginResult, Finding


class ClassVisitor(ast.NodeVisitor):
    def __init__(self):
        self.classes = {}
        self.current_class = None
        self.class_hierarchy = {} # child -> list of parents

    def visit_ClassDef(self, node: ast.ClassDef):
        class_name = node.name
        self.classes[class_name] = {
            "bases": [b.id for b in node.bases if isinstance(b, ast.Name)],
            "methods": [],
            "attributes_accessed": {}, # method_name -> set of self.attr
            "external_couplings": set(), # referenced classes/types
        }
        self.class_hierarchy[class_name] = self.classes[class_name]["bases"]

        prev_class = self.current_class
        self.current_class = class_name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self.current_class:
            method_name = node.name
            self.classes[self.current_class]["methods"].append(method_name)
            self.classes[self.current_class]["attributes_accessed"][method_name] = set()

            for child in ast.walk(node):
                if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name) and child.value.id == "self":
                    self.classes[self.current_class]["attributes_accessed"][method_name].add(child.attr)
                elif isinstance(child, ast.Name) and child.id not in ["self", "cls", "int", "str", "float", "bool", "dict", "list", "set", "tuple"]:
                    # External class / type usage indicates coupling
                    if child.id[0].isupper():
                        self.classes[self.current_class]["external_couplings"].add(child.id)
        self.generic_visit(node)


class ASTMetricsPlugin(AnalyzerPlugin):
    @property
    def name(self) -> str:
        return "ck_metrics"

    @property
    def supported_languages(self) -> List[str]:
        return ["python", "javascript", "typescript"]

    def analyze(self, file_path: Path, content: str) -> PluginResult:
        findings: List[Finding] = []
        metrics = {
            "cbo": 0,
            "lcom": 0,
            "dit": 0,
            "noc": 0,
            "comment_density": 0.0,
            "duplication_pct": 0.0,
        }

        # Comment density calculation
        lines = content.splitlines()
        total_lines = len(lines)
        if total_lines > 0:
            comment_lines = 0
            for line in lines:
                l_str = line.strip()
                if l_str.startswith("#") or l_str.startswith("//") or l_str.startswith("/*") or l_str.startswith("*"):
                    comment_lines += 1
            metrics["comment_density"] = round((comment_lines / total_lines) * 100, 2)

        # Code Duplication % heuristic (block hashing of 5-line rolling windows)
        if total_lines >= 10:
            cleaned = [re.sub(r'\s+', '', l) for l in lines if l.strip() and not l.strip().startswith(("#", "//", "/*"))]
            if len(cleaned) >= 6:
                seen_windows = set()
                duplicate_windows = 0
                window_size = 4
                for i in range(len(cleaned) - window_size + 1):
                    window_hash = hash(tuple(cleaned[i:i + window_size]))
                    if window_hash in seen_windows:
                        duplicate_windows += 1
                    else:
                        seen_windows.add(window_hash)
                total_windows = len(cleaned) - window_size + 1
                metrics["duplication_pct"] = round((duplicate_windows / total_windows) * 100, 2)

        # Python AST for CK metrics
        is_python = str(file_path).endswith(".py")
        if is_python and content.strip():
            try:
                tree = ast.parse(content)
                visitor = ClassVisitor()
                visitor.visit(tree)

                if visitor.classes:
                    cbo_values = []
                    lcom_values = []
                    dit_values = []

                    for cname, cdata in visitor.classes.items():
                        # CBO: number of coupled external types + bases
                        cbo = len(cdata["external_couplings"] | set(cdata["bases"]))
                        cbo_values.append(cbo)

                        # DIT: depth in class_hierarchy
                        depth = 0
                        curr_bases = cdata["bases"]
                        while curr_bases:
                            depth += 1
                            next_bases = []
                            for b in curr_bases:
                                if b in visitor.class_hierarchy:
                                    next_bases.extend(visitor.class_hierarchy[b])
                            curr_bases = next_bases
                            if depth > 10: # safeguard against circular refs
                                break
                        dit_values.append(depth)

                        # LCOM: Lack of Cohesion of Methods (Henderson-Sellers formula)
                        methods = cdata["methods"]
                        m_count = len(methods)
                        if m_count > 1:
                            # Count attribute accesses across methods
                            attr_map = cdata["attributes_accessed"]
                            all_attrs = set()
                            for s in attr_map.values():
                                all_attrs.update(s)
                            a_count = len(all_attrs)
                            if a_count > 0:
                                sum_methods_per_attr = sum(
                                    sum(1 for m in methods if attr in attr_map[m])
                                    for attr in all_attrs
                                )
                                # Henderson-Sellers LCOM* = (m - (sum / a)) / (m - 1)
                                avg_access = sum_methods_per_attr / a_count
                                lcom_hs = max(0.0, (m_count - avg_access) / (m_count - 1))
                                lcom_values.append(int(round(lcom_hs * 100)))
                            else:
                                lcom_values.append(0)
                        else:
                            lcom_values.append(0)

                    # Compute NOC (Number of children for each class)
                    noc_counts = {c: 0 for c in visitor.classes}
                    for cname, cdata in visitor.classes.items():
                        for b in cdata["bases"]:
                            if b in noc_counts:
                                noc_counts[b] += 1

                    metrics["cbo"] = int(sum(cbo_values) / len(cbo_values)) if cbo_values else 0
                    metrics["dit"] = max(dit_values) if dit_values else 0
                    metrics["lcom"] = int(sum(lcom_values) / len(lcom_values)) if lcom_values else 0
                    metrics["noc"] = max(noc_counts.values()) if noc_counts else 0

                    if metrics["cbo"] > 10:
                        findings.append(Finding(
                            file_path=str(file_path),
                            line_number=1,
                            rule_id="HIGH_COUPLING",
                            severity="warning",
                            tool="ck_metrics",
                            description=f"Class coupling is high (CBO={metrics['cbo']}). Reduces modularity and testability."
                        ))
                    if metrics["lcom"] > 70:
                        findings.append(Finding(
                            file_path=str(file_path),
                            line_number=1,
                            rule_id="LOW_COHESION",
                            severity="warning",
                            tool="ck_metrics",
                            description=f"Class cohesion is poor (LCOM={metrics['lcom']}%). Methods may not share single responsibility."
                        ))
            except Exception:
                pass

        return PluginResult(metrics=metrics, findings=findings)
