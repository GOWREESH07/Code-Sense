from typing import List, Dict, Any
from backend.recommendations.base import RecommendationProvider, RecommendationItem


class RuleBasedRecommendationProvider(RecommendationProvider):
    def generate_recommendations(
        self,
        metrics_summary: Dict[str, Any],
        top_risky_files: List[Dict[str, Any]],
        findings: List[Any],
    ) -> List[RecommendationItem]:
        recs: List[RecommendationItem] = []

        # 1. Check for Security Vulnerabilities (Bandit / ESLint security findings)
        sec_findings = [f for f in findings if getattr(f, "tool", "") == "bandit" or "eval" in getattr(f, "rule_id", "").lower()]
        if sec_findings:
            top_sec = sec_findings[0]
            recs.append(RecommendationItem(
                priority=len(recs) + 1,
                title=f"Resolve Security Vulnerability ({getattr(top_sec, 'rule_id', 'SECURITY')})",
                category="Security",
                description=f"Found {len(sec_findings)} security alert(s). Example: {getattr(top_sec, 'description', '')} in {getattr(top_sec, 'file_path', '')}.",
                suggested_fix="Replace insecure functions (eval, raw SQL queries, or weak crypto) with parameterized inputs and vetted standard library equivalents.",
                file_path=getattr(top_sec, "file_path", ""),
                impact="Critical",
            ))

        # 2. Check for Top High-Risk / Complex Modules
        if top_risky_files:
            riskiest = top_risky_files[0]
            cc = riskiest.get("cyclomatic_complexity", 1.0)
            f_path = riskiest.get("file_path", "")
            prob = riskiest.get("bug_probability", 0.0)

            if cc > 10.0 or prob > 0.4:
                recs.append(RecommendationItem(
                    priority=len(recs) + 1,
                    title=f"Decompose Complex Control Flow in {f_path}",
                    category="Maintainability",
                    description=f"File has cyclomatic complexity of {cc:.1f} and bug probability of {prob*100:.1f}%. Deep nesting and excessive decision points introduce latent bugs.",
                    suggested_fix="Extract sub-routines using the 'Extract Method' refactoring pattern. Replace nested conditionals with guard clauses or strategy dictionaries.",
                    file_path=f_path,
                    impact="High",
                ))

        # 3. Check for High Class Coupling (CBO) or Low Cohesion (LCOM)
        high_cbo_files = [f for f in top_risky_files if f.get("cbo", 0) > 8 or f.get("lcom", 0) > 60]
        if high_cbo_files and len(recs) < 5:
            target = high_cbo_files[0]
            cbo = target.get("cbo", 0)
            lcom = target.get("lcom", 0)
            recs.append(RecommendationItem(
                priority=len(recs) + 1,
                title=f"Decouple Monolithic Classes in {target.get('file_path')}",
                category="Architecture",
                description=f"High coupling (CBO={cbo}) and low cohesion (LCOM={lcom}%) indicate violation of Single Responsibility Principle (SRP).",
                suggested_fix="Introduce dependency injection or facade abstractions to isolate external type dependencies. Split multifarious classes into cohesive components.",
                file_path=target.get("file_path", ""),
                impact="High",
            ))

        # 4. Check Code Duplication
        dup_pct = metrics_summary.get("duplication_pct", 0.0)
        if dup_pct > 8.0 and len(recs) < 5:
            recs.append(RecommendationItem(
                priority=len(recs) + 1,
                title="Consolidate Duplicated Logic",
                category="Refactoring",
                description=f"Detected {dup_pct:.1f}% repeated logic across modules. Code duplication multiplies maintenance overhead and risk of inconsistent bug fixes.",
                suggested_fix="Extract shared utility functions or base abstract classes into a dedicated shared service module.",
                file_path=top_risky_files[0].get("file_path", "") if top_risky_files else "",
                impact="Medium",
            ))

        # 5. Check Test Coverage & Defect Density
        coverage = metrics_summary.get("test_coverage_pct", 0.0)
        if coverage < 50.0 and len(recs) < 5:
            recs.append(RecommendationItem(
                priority=len(recs) + 1,
                title="Expand Automated Test Suite Coverage",
                category="Testing",
                description=f"Current estimated test coverage is {coverage:.1f}%. High-risk business logic lacks regression guards.",
                suggested_fix="Add parameterized unit tests targeting the highest risk files and edge cases in branching logic.",
                file_path=top_risky_files[0].get("file_path", "") if top_risky_files else "",
                impact="High",
            ))

        # 6. Fallback General Recommendation if still under 3
        if len(recs) < 3:
            recs.append(RecommendationItem(
                priority=len(recs) + 1,
                title="Add Type Annotations and Documentation",
                category="Maintainability",
                description="Improve codebase clarity and static safety by ensuring public methods have explicit typing and docstrings.",
                suggested_fix="Enable strict type checking and enforce docstrings on public APIs.",
                file_path="",
                impact="Low",
            ))

        # Ensure maximum of 5 recommendations
        return recs[:5]
