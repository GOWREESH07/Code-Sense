from typing import List, Dict, Any


class MetricsService:
    @staticmethod
    def calculate_technical_debt(file_metrics: List[Dict[str, Any]], findings: List[Any]) -> int:
        debt_minutes = 0
        for f in findings:
            sev = getattr(f, "severity", "warning")
            tool = getattr(f, "tool", "")
            if tool == "bandit" or sev == "critical":
                debt_minutes += 45
            elif sev == "error":
                debt_minutes += 25
            elif sev == "warning":
                debt_minutes += 12
            else:
                debt_minutes += 5

        for m in file_metrics:
            cc = m.get("cyclomatic_complexity", 1.0)
            if cc > 10:
                debt_minutes += int((cc - 10) * 8)
            mi = m.get("maintainability_index", 100.0)
            if mi < 65:
                debt_minutes += int((65 - mi) * 1.5)
            dup = m.get("duplication_pct", 0.0)
            if dup > 5.0:
                debt_minutes += int((dup - 5.0) * 3)

        return max(0, debt_minutes)

    @staticmethod
    def aggregate_metrics(file_metrics: List[Dict[str, Any]], findings: List[Any], repo_summary: Dict[str, Any]) -> Dict[str, Any]:
        count = len(file_metrics) or 1

        total_loc = sum(m.get("loc", 0) for m in file_metrics)
        avg_cc = round(sum(m.get("cyclomatic_complexity", 1.0) for m in file_metrics) / count, 2)
        avg_mi = round(sum(m.get("maintainability_index", 100.0) for m in file_metrics) / count, 2)
        avg_dup = round(sum(m.get("duplication_pct", 0.0) for m in file_metrics) / count, 2)
        avg_cbo = round(sum(m.get("cbo", 0) for m in file_metrics) / count, 2)
        avg_lcom = round(sum(m.get("lcom", 0) for m in file_metrics) / count, 2)
        max_dit = max((m.get("dit", 0) for m in file_metrics), default=0)
        max_noc = max((m.get("noc", 0) for m in file_metrics), default=0)
        avg_comment_density = round(sum(m.get("comment_density", 0.0) for m in file_metrics) / count, 2)

        smells_count = len([f for f in findings if getattr(f, "tool", "") != "bandit"])
        security_count = len([f for f in findings if getattr(f, "tool", "") == "bandit" or "eval" in getattr(f, "rule_id", "").lower()])

        # Defect density: defects per 1,000 LOC
        kloc = max(total_loc / 1000.0, 0.1)
        defect_density = round(len(findings) / kloc, 2)

        test_coverage_pct = repo_summary.get("estimated_test_coverage", 0.0)
        tech_debt_minutes = MetricsService.calculate_technical_debt(file_metrics, findings)

        # Bug Prediction Score (average of module bug probabilities)
        avg_bug_probability = round(sum(m.get("bug_probability", 0.0) for m in file_metrics) / count, 3)

        # Composite Overall Quality Score (0 to 100)
        # Factors: Maintainability (30%), Reliability/Defects (25%), Security (20%), Complexity/Structure (15%), Test Coverage (10%)
        m_score = min(100.0, max(0.0, avg_mi))
        r_score = max(0.0, 100.0 - (defect_density * 4.0) - (avg_bug_probability * 40.0))
        s_score = max(0.0, 100.0 - (security_count * 15.0))
        c_score = max(0.0, 100.0 - max(0.0, (avg_cc - 2.0) * 12.0) - (avg_cbo * 3.0) - (avg_dup * 1.5))
        t_score = test_coverage_pct

        overall_score = round(
            0.30 * m_score +
            0.25 * r_score +
            0.20 * s_score +
            0.15 * c_score +
            0.10 * t_score,
            1
        )
        overall_score = max(5.0, min(100.0, overall_score))

        # AI-Generated Code Metric: LOC-weighted average across all files
        total_file_loc = sum(m.get("loc", 0) for m in file_metrics)
        if total_file_loc > 0:
            weighted_ai_sum = sum(m.get("loc", 0) * m.get("ai_generated_score", 0.0) for m in file_metrics)
            ai_generated_pct = round((weighted_ai_sum / total_file_loc) * 100.0, 1)
        else:
            ai_generated_pct = 0.0

        # Compile the fixed set of metrics + AI code metric
        fixed_metrics = {
            "cyclomatic_complexity": avg_cc,
            "loc": total_loc,
            "maintainability_index": avg_mi,
            "duplication_pct": avg_dup,
            "cbo": avg_cbo,
            "lcom": avg_lcom,
            "dit": max_dit,
            "noc": max_noc,
            "defect_density": defect_density,
            "code_smells": smells_count,
            "tech_debt_minutes": tech_debt_minutes,
            "test_coverage_pct": test_coverage_pct,
            "comment_density": avg_comment_density,
            "security_vulnerabilities": security_count,
            "bug_prediction_score": avg_bug_probability,
            "ai_generated_pct": ai_generated_pct,
            "overall_quality_score": overall_score,
            # Sub-scores for dimensional radar charts
            "dimension_scores": {
                "maintainability": round(m_score, 1),
                "reliability": round(r_score, 1),
                "security": round(s_score, 1),
                "architecture": round(c_score, 1),
                "testability": round(t_score, 1),
            }
        }

        return fixed_metrics



metrics_service = MetricsService()
