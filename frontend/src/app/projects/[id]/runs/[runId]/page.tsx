"use client";

import { useEffect, useState, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, Download, ShieldCheck, AlertTriangle, Bug, Code2, 
  Clock, CheckCircle2, TrendingUp, Sparkles, FileText, Search, 
  ArrowUpDown, Filter, ChevronRight, RefreshCw, Layers, ShieldAlert
} from "lucide-react";
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid 
} from "recharts";
import { fetchRunResults, RunResults, FileMetric } from "@/lib/api";

export default function AnalysisDashboardPage() {
  const params = useParams();
  const projectId = params.id as string;
  const runId = params.runId as string;

  const [data, setData] = useState<RunResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // File table filter & sort
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<keyof FileMetric>("bug_probability");
  const [sortAsc, setSortAsc] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<string>("all");

  // Selected file for detail modal
  const [activeFile, setActiveFile] = useState<FileMetric | null>(null);

  useEffect(() => {
    const loadResults = async () => {
      try {
        setLoading(true);
        const res = await fetchRunResults(runId);
        setData(res);
      } catch (err: any) {
        setError(err.message || "Failed to load run results");
      } finally {
        setLoading(false);
      }
    };
    loadResults();
  }, [runId]);

  // Export PDF
  const handleExportPDF = async () => {
    try {
      const { jsPDF } = await import("jspdf");
      const html2canvas = (await import("html2canvas")).default;
      const element = document.getElementById("dashboard-content");
      if (!element) return;

      const canvas = await html2canvas(element, {
        scale: 1.5,
        backgroundColor: "#FFFFFF",
        logging: false,
      });
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");
      const imgWidth = 210;
      const pageHeight = 295;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      let heightLeft = imgHeight;
      let position = 0;

      pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;

      while (heightLeft >= 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }

      pdf.save(`CodeSense_Report_${runId.substring(0, 8)}.pdf`);
    } catch (e) {
      console.error("PDF export failed:", e);
      window.print();
    }
  };

  // Filtered & sorted files
  const filteredFiles = useMemo(() => {
    if (!data?.file_metrics) return [];
    return data.file_metrics
      .filter((f) => {
        const matchesSearch = f.file_path.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesLang = selectedLanguage === "all" || f.language === selectedLanguage;
        return matchesSearch && matchesLang;
      })
      .sort((a, b) => {
        const valA = a[sortField] ?? 0;
        const valB = b[sortField] ?? 0;
        if (valA < valB) return sortAsc ? -1 : 1;
        if (valA > valB) return sortAsc ? 1 : -1;
        return 0;
      });
  }, [data, searchQuery, sortField, sortAsc, selectedLanguage]);

  const toggleSort = (field: keyof FileMetric) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl p-16 text-center border border-slate-200">
        <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-3" />
        <p className="text-slate-700 font-medium text-sm">Rendering Quality Intelligence Dashboard...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-xl p-8 text-center border border-slate-200">
        <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto mb-2" />
        <p className="text-slate-800 font-semibold mb-2">{error || "Failed to load dashboard data."}</p>
        <Link href={`/projects/${projectId}`} className="text-indigo-600 text-xs font-medium hover:underline">
          Return to Project History
        </Link>
      </div>
    );
  }

  const { run, file_metrics, defects, recommendations } = data;
  const summary = run.summary || {};
  const overallScore = run.overall_score || 0;

  // Grade badge based on score
  const getGrade = (score: number) => {
    if (score >= 90) return { grade: "A+", color: "text-emerald-700 bg-emerald-50 border-emerald-200" };
    if (score >= 80) return { grade: "A", color: "text-emerald-700 bg-emerald-50 border-emerald-200" };
    if (score >= 70) return { grade: "B", color: "text-indigo-700 bg-indigo-50 border-indigo-200" };
    if (score >= 60) return { grade: "C", color: "text-amber-700 bg-amber-50 border-amber-200" };
    return { grade: "D", color: "text-red-700 bg-red-50 border-red-200" };
  };

  const gradeInfo = getGrade(overallScore);

  // Radar chart data
  const dimensionScores = summary.dimension_scores || {
    maintainability: 80,
    reliability: 75,
    security: 85,
    architecture: 70,
    testability: 60,
  };

  const radarData = [
    { subject: "Maintainability", score: dimensionScores.maintainability, fullMark: 100 },
    { subject: "Reliability", score: dimensionScores.reliability, fullMark: 100 },
    { subject: "Security", score: dimensionScores.security, fullMark: 100 },
    { subject: "Architecture", score: dimensionScores.architecture, fullMark: 100 },
    { subject: "Testability", score: dimensionScores.testability, fullMark: 100 },
  ];

  // Top complex files for bar chart
  const barData = file_metrics
    .slice(0, 6)
    .map((f) => ({
      name: f.file_path.split("/").pop() || f.file_path,
      complexity: f.cyclomatic_complexity,
      bugProbability: Math.round(f.bug_probability * 100),
    }));

  return (
    <div className="space-y-8" id="dashboard-content">
      {/* Top Navigation & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Link
            href={`/projects/${projectId}`}
            className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Project History</span>
          </Link>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Software Quality Audit Report</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Run executed {new Date(run.created_at).toLocaleString()} • {file_metrics.length} files analyzed
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleExportPDF}
            className="inline-flex items-center space-x-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 px-4 py-2 rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <Download className="w-4 h-4 text-slate-500" />
            <span>Export Report (PDF)</span>
          </button>
        </div>
      </div>

      {/* Hero Overview Card: Overall Quality Score & Key Pillars */}
      <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-sm">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-center">
          {/* Overall Quality Score Dial */}
          <div className="lg:col-span-1 border-b lg:border-b-0 lg:border-r border-slate-100 pb-6 lg:pb-0 lg:pr-6 text-center">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-2">
              Overall Quality Score
            </span>
            <div className="inline-flex items-baseline justify-center space-x-2">
              <span className="text-5xl font-extrabold text-slate-900 tracking-tight">
                {overallScore}
              </span>
              <span className="text-sm font-semibold text-slate-400">/100</span>
            </div>
            <div className="mt-3 flex items-center justify-center space-x-2">
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold border ${gradeInfo.color}`}>
                Grade {gradeInfo.grade}
              </span>
              <span className="text-xs text-slate-500">
                {overallScore >= 75 ? "Production Ready" : "Requires Hardening"}
              </span>
            </div>
          </div>

          {/* Core Metrics Quick Cards */}
          <div className="lg:col-span-3 grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-50/80 p-4 rounded-xl border border-slate-200/80">
              <div className="flex items-center justify-between text-slate-500 mb-1">
                <span className="text-[11px] font-semibold uppercase">Total LOC</span>
                <Code2 className="w-4 h-4 text-indigo-600" />
              </div>
              <p className="text-xl font-bold text-slate-900">{run.total_loc?.toLocaleString()}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Across {file_metrics.length} modules</p>
            </div>

            <div className="bg-slate-50/80 p-4 rounded-xl border border-slate-200/80">
              <div className="flex items-center justify-between text-slate-500 mb-1">
                <span className="text-[11px] font-semibold uppercase">Technical Debt</span>
                <Clock className="w-4 h-4 text-amber-600" />
              </div>
              <p className="text-xl font-bold text-slate-900">
                {Math.floor(run.tech_debt_minutes / 60)}h {run.tech_debt_minutes % 60}m
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">Remediation time</p>
            </div>

            <div className="bg-slate-50/80 p-4 rounded-xl border border-slate-200/80">
              <div className="flex items-center justify-between text-slate-500 mb-1">
                <span className="text-[11px] font-semibold uppercase">Bug Risk</span>
                <Bug className="w-4 h-4 text-rose-600" />
              </div>
              <p className="text-xl font-bold text-slate-900">
                {(run.bug_probability * 100).toFixed(1)}%
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">ML defect expectation</p>
            </div>

            <div className="bg-slate-50/80 p-4 rounded-xl border border-slate-200/80">
              <div className="flex items-center justify-between text-slate-500 mb-1">
                <span className="text-[11px] font-semibold uppercase">Security Alerts</span>
                <ShieldAlert className="w-4 h-4 text-emerald-600" />
              </div>
              <p className="text-xl font-bold text-slate-900">
                {summary.security_vulnerabilities || 0}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">Bandit / static findings</p>
            </div>
          </div>
        </div>
      </div>

      {/* Visual Analytics Row: Radar Dimension & Complexity Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Radar Dimensions */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Software Quality Dimensions</h2>
              <p className="text-[11px] text-slate-500">Holistic balance across key architecture facets</p>
            </div>
            <span className="text-xs font-semibold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-md border border-indigo-100">
              Composite Profile
            </span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                <PolarGrid stroke="#E2E8F0" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: "#475569", fontSize: 11 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#CBD5E1" tick={{ fill: "#64748B", fontSize: 10 }} />
                <Radar name="Quality" dataKey="score" stroke="#4F46E5" fill="#4F46E5" fillOpacity={0.25} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Complexity & Bug Probability Distribution */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Module Complexity & Bug Probability</h2>
              <p className="text-[11px] text-slate-500">Comparison of top modules by cyclomatic complexity</p>
            </div>
            <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2.5 py-0.5 rounded-md">
              Top 6 Files
            </span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="name" tick={{ fill: "#475569", fontSize: 10 }} angle={-25} textAnchor="end" />
                <YAxis tick={{ fill: "#475569", fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#FFFFFF", borderColor: "#E2E8F0", borderRadius: "8px", fontSize: "11px" }}
                />
                <Bar dataKey="complexity" fill="#4F46E5" name="Cyclomatic Complexity" radius={[4, 4, 0, 0]} />
                <Bar dataKey="bugProbability" fill="#F59E0B" name="Bug Risk %" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* The Fixed 15 Quality Metrics Grid */}
      <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-sm">
        <div className="border-b border-slate-100 pb-4 mb-6">
          <h2 className="text-base font-bold text-slate-900">Fixed Metric Set (15 Normalized Dimensions)</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Normalized software engineering metrics computed across Radon, Bandit, Pylint, AST, and ML layers.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {/* 1. Cyclomatic Complexity */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">1. Cyclomatic Complexity</span>
            <p className="text-lg font-bold text-slate-900">{summary.cyclomatic_complexity || 1.0}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Avg decision paths/func</p>
          </div>

          {/* 2. LOC */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">2. Lines of Code (LOC)</span>
            <p className="text-lg font-bold text-slate-900">{summary.loc?.toLocaleString() || 0}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Total executable lines</p>
          </div>

          {/* 3. Maintainability Index */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">3. Maintainability Index</span>
            <p className="text-lg font-bold text-slate-900">{summary.maintainability_index || 75.0}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">0-100 scale (Radon MI)</p>
          </div>

          {/* 4. Code Duplication % */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">4. Duplication %</span>
            <p className="text-lg font-bold text-slate-900">{summary.duplication_pct || 0.0}%</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Identical rolling hashes</p>
          </div>

          {/* 5. CBO */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">5. Coupling (CBO)</span>
            <p className="text-lg font-bold text-slate-900">{summary.cbo || 0}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Coupling between objects</p>
          </div>

          {/* 6. LCOM */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">6. Cohesion (LCOM)</span>
            <p className="text-lg font-bold text-slate-900">{summary.lcom || 0}%</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Lack of cohesion (HS)</p>
          </div>

          {/* 7. DIT */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">7. Inheritance (DIT)</span>
            <p className="text-lg font-bold text-slate-900">{summary.dit || 0}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Max tree depth</p>
          </div>

          {/* 8. NOC */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">8. Children Count (NOC)</span>
            <p className="text-lg font-bold text-slate-900">{summary.noc || 0}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Max subclass fan-out</p>
          </div>

          {/* 9. Defect Density */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">9. Defect Density</span>
            <p className="text-lg font-bold text-slate-900">{summary.defect_density || 0.0}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Defects per 1,000 LOC</p>
          </div>

          {/* 10. Code Smells */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">10. Code Smells</span>
            <p className="text-lg font-bold text-slate-900">{summary.code_smells || 0}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Pylint & ESLint findings</p>
          </div>

          {/* 11. Technical Debt */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">11. Technical Debt</span>
            <p className="text-lg font-bold text-slate-900">{summary.tech_debt_minutes || 0} min</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Sonar remediation model</p>
          </div>

          {/* 12. Test Coverage */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">12. Test Coverage %</span>
            <p className="text-lg font-bold text-slate-900">{summary.test_coverage_pct || 0.0}%</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Test-to-source ratio</p>
          </div>

          {/* 13. Comment Density */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">13. Comment Density</span>
            <p className="text-lg font-bold text-slate-900">{summary.comment_density || 0.0}%</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Doc & inline coverage</p>
          </div>

          {/* 14. Security Vulnerabilities */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">14. Security Flaws</span>
            <p className="text-lg font-bold text-slate-900">{summary.security_vulnerabilities || 0}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Bandit / CWE alerts</p>
          </div>

          {/* 15. Bug Prediction Score */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">15. Bug Prediction</span>
            <p className="text-lg font-bold text-slate-900">{summary.bug_prediction_score || 0.0}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">ML probability (0-1)</p>
          </div>
        </div>
      </div>

      {/* Top Risks & AI Recommendations Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Risks with SHAP factors */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-bold text-slate-900">Highest Risk Modules (ML Defect Ranking)</h2>
                <p className="text-[11px] text-slate-500">Modules most likely to contain latent faults with SHAP attribution</p>
              </div>
              <span className="text-xs font-semibold text-rose-700 bg-rose-50 px-2.5 py-0.5 rounded-md border border-rose-200">
                XGBoost + SHAP
              </span>
            </div>

            <div className="space-y-3">
              {file_metrics.slice(0, 4).map((f) => (
                <div
                  key={f.file_path}
                  onClick={() => setActiveFile(f)}
                  className="p-3.5 rounded-xl border border-slate-200 hover:border-indigo-300 hover:bg-slate-50/50 cursor-pointer transition-all"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-xs font-semibold text-slate-900 truncate max-w-[280px]">
                      {f.file_path}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        f.bug_probability > 0.5
                          ? "bg-rose-100 text-rose-800"
                          : f.bug_probability > 0.25
                          ? "bg-amber-100 text-amber-800"
                          : "bg-emerald-100 text-emerald-800"
                      }`}
                    >
                      {(f.bug_probability * 100).toFixed(1)}% Defect Prob
                    </span>
                  </div>

                  {/* SHAP factor badges */}
                  {f.top_contributing_factors && f.top_contributing_factors.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {f.top_contributing_factors.slice(0, 2).map((fac, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] font-medium bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-200"
                        >
                          +{fac.impact_pct}% {fac.display_name}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[10px] text-slate-500 mt-1">
                      LOC: {f.loc} • Complexity: {f.cyclomatic_complexity} • MI: {f.maintainability_index}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* AI Recommendations Panel */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Prioritized Actionable Recommendations</h2>
              <p className="text-[11px] text-slate-500">Curated AI insights generated by Gemini / Rule Engine</p>
            </div>
            <Sparkles className="w-4 h-4 text-indigo-600" />
          </div>

          <div className="space-y-3">
            {recommendations.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-8">No critical recommendations at this time.</p>
            ) : (
              recommendations.map((rec) => (
                <div key={rec.id} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/40">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="flex items-center space-x-2">
                      <span className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center text-[10px] font-bold">
                        {rec.priority}
                      </span>
                      <h3 className="text-xs font-bold text-slate-900">{rec.title}</h3>
                    </div>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        rec.impact === "Critical"
                          ? "bg-rose-100 text-rose-800"
                          : rec.impact === "High"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-blue-100 text-blue-800"
                      }`}
                    >
                      {rec.impact}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">{rec.description}</p>
                  {rec.suggested_fix && (
                    <div className="mt-2.5 p-2 rounded bg-white border border-slate-200 text-[11px] text-slate-700 font-mono">
                      <span className="font-semibold text-indigo-600 block mb-0.5">Suggested Fix:</span>
                      {rec.suggested_fix}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Sortable & Filterable File Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">Module Metrics & Defect Explorer</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Inspecting {filteredFiles.length} of {file_metrics.length} total source files
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search file path..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white text-slate-900 w-48"
              />
            </div>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="py-1.5 px-3 text-xs rounded-lg border border-slate-200 bg-white text-slate-700"
            >
              <option value="all">All Languages</option>
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-600 uppercase tracking-wider">
                <th
                  onClick={() => toggleSort("file_path")}
                  className="py-3 px-4 cursor-pointer hover:text-slate-900"
                >
                  <div className="flex items-center space-x-1">
                    <span>File Path</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => toggleSort("loc")}
                  className="py-3 px-4 cursor-pointer hover:text-slate-900"
                >
                  <div className="flex items-center space-x-1">
                    <span>LOC</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => toggleSort("cyclomatic_complexity")}
                  className="py-3 px-4 cursor-pointer hover:text-slate-900"
                >
                  <div className="flex items-center space-x-1">
                    <span>Complexity</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => toggleSort("maintainability_index")}
                  className="py-3 px-4 cursor-pointer hover:text-slate-900"
                >
                  <div className="flex items-center space-x-1">
                    <span>Maintainability</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => toggleSort("cbo")}
                  className="py-3 px-4 cursor-pointer hover:text-slate-900"
                >
                  <div className="flex items-center space-x-1">
                    <span>Coupling (CBO)</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => toggleSort("smells_count")}
                  className="py-3 px-4 cursor-pointer hover:text-slate-900"
                >
                  <div className="flex items-center space-x-1">
                    <span>Smells</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => toggleSort("bug_probability")}
                  className="py-3 px-4 cursor-pointer hover:text-slate-900"
                >
                  <div className="flex items-center space-x-1">
                    <span>Bug Probability</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
              {filteredFiles.map((f) => (
                <tr
                  key={f.id || f.file_path}
                  onClick={() => setActiveFile(f)}
                  className="hover:bg-slate-50 cursor-pointer transition-colors"
                >
                  <td className="py-3 px-4 font-mono font-medium text-slate-900">
                    <span className="text-indigo-600 hover:underline">{f.file_path}</span>
                  </td>
                  <td className="py-3 px-4 font-mono">{f.loc}</td>
                  <td className="py-3 px-4 font-mono">
                    <span className={f.cyclomatic_complexity > 10 ? "text-amber-700 font-bold" : ""}>
                      {f.cyclomatic_complexity}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono">
                    <span className={f.maintainability_index < 60 ? "text-amber-700 font-bold" : ""}>
                      {f.maintainability_index}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono">{f.cbo}</td>
                  <td className="py-3 px-4 font-mono">
                    {f.smells_count > 0 ? (
                      <span className="text-amber-700 font-medium">{f.smells_count}</span>
                    ) : (
                      "0"
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold ${
                        f.bug_probability > 0.5
                          ? "bg-rose-50 text-rose-700 border border-rose-200"
                          : f.bug_probability > 0.25
                          ? "bg-amber-50 text-amber-700 border border-amber-200"
                          : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                      }`}
                    >
                      {(f.bug_probability * 100).toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* File Details Modal with SHAP Breakdown */}
      {activeFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 sm:p-8 shadow-xl border border-slate-200">
            <div className="flex items-start justify-between pb-4 border-b border-slate-100 mb-6">
              <div>
                <h3 className="text-base font-bold text-slate-900 font-mono">{activeFile.file_path}</h3>
                <span className="text-xs text-slate-500 uppercase font-semibold mt-0.5 block">
                  Language: {activeFile.language} • LOC: {activeFile.loc}
                </span>
              </div>
              <button
                onClick={() => setActiveFile(null)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold p-1"
              >
                ✕
              </button>
            </div>

            {/* Metrics Breakdown */}
            <div className="grid grid-cols-3 gap-3 mb-6">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <span className="text-[10px] uppercase font-bold text-slate-500">Complexity</span>
                <p className="text-lg font-bold text-slate-900">{activeFile.cyclomatic_complexity}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <span className="text-[10px] uppercase font-bold text-slate-500">Maintainability</span>
                <p className="text-lg font-bold text-slate-900">{activeFile.maintainability_index}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <span className="text-[10px] uppercase font-bold text-slate-500">Bug Probability</span>
                <p className="text-lg font-bold text-slate-900">{(activeFile.bug_probability * 100).toFixed(1)}%</p>
              </div>
            </div>

            {/* SHAP Explanations */}
            <div className="mb-6">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
                SHAP Risk Factor Contributions
              </h4>
              <div className="space-y-2">
                {activeFile.top_contributing_factors && activeFile.top_contributing_factors.length > 0 ? (
                  activeFile.top_contributing_factors.map((factor, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg border border-slate-200 bg-slate-50/60 text-xs">
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="font-semibold text-slate-900">{factor.display_name}</span>
                        <span className="font-bold text-rose-600">+{factor.impact_pct}%</span>
                      </div>
                      <p className="text-[11px] text-slate-500">{factor.explanation}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500">No disproportionate risk drivers identified for this module.</p>
                )}
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => setActiveFile(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
