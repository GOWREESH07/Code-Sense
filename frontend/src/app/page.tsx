"use client";

import Link from "next/link";
import { 
  ShieldCheck, ArrowRight, Play, Sparkles, Cpu, Binary, FileCheck, 
  FolderGit2, CheckCircle2, AlertTriangle, Bug, Code2, Clock, 
  Layers, Lock, LineChart, ExternalLink, ChevronRight, BarChart3, Database
} from "lucide-react";

export default function LandingPage() {
  const metricsList = [
    { name: "Cyclomatic Complexity", desc: "Decision branch density (Radon CC)", category: "Complexity" },
    { name: "Lines of Code (LOC)", desc: "Physical executable lines", category: "Size" },
    { name: "Maintainability Index", desc: "Composite 0-100 maintainability score", category: "Maintainability" },
    { name: "Code Duplication %", desc: "Sliding-window hash collision rate", category: "Refactoring" },
    { name: "Coupling Between Objects (CBO)", desc: "Inter-module class dependency fan-in/out", category: "Architecture" },
    { name: "Lack of Cohesion (LCOM)", desc: "Henderson-Sellers method attribute disjointness", category: "Architecture" },
    { name: "Depth of Inheritance (DIT)", desc: "Maximum class hierarchy depth", category: "Architecture" },
    { name: "Number of Children (NOC)", desc: "Immediate subclass count", category: "Architecture" },
    { name: "Defect Density", desc: "Identified defects per 1,000 LOC (KLOC)", category: "Reliability" },
    { name: "Code Smells Count", desc: "Static rule violations (Pylint & ESLint)", category: "Maintainability" },
    { name: "Technical Debt (Minutes)", desc: "Remediation time estimation model", category: "Debt" },
    { name: "Test Coverage %", desc: "Automated test assertion & code ratio", category: "Testing" },
    { name: "Comment Density %", desc: "Inline and API documentation coverage", category: "Documentation" },
    { name: "Security Vulnerabilities", desc: "CWE flaws & insecure calls (Bandit)", category: "Security" },
    { name: "Bug Prediction Score", desc: "ML-computed module bug probability (0–1)", category: "ML Risk" },
    { name: "Overall Quality Score", desc: "Composite 0-100 multi-dimensional index", category: "Composite" },
  ];

  const features = [
    {
      icon: FolderGit2,
      title: "Automated Ingestion",
      desc: "Ingest repositories via ZIP archive upload or direct public GitHub URL cloning with zero server-side setup.",
    },
    {
      icon: Layers,
      title: "Comprehensive 15-Metric Set",
      desc: "Computes industry-standard Chidamber & Kemerer object-oriented metrics, Radon complexity, and Halstead effort.",
    },
    {
      icon: Binary,
      title: "AI Defect Prediction",
      desc: "Pre-trained XGBoost classifier predicts the likelihood of latent bugs per module using NASA MDP defect distributions.",
    },
    {
      icon: Lock,
      title: "Smell & Security Auditing",
      desc: "Dual-engine static inspection surfaces Bandit security vulnerabilities and Pylint/ESLint architectural code smells.",
    },
    {
      icon: Sparkles,
      title: "Actionable AI Reports",
      desc: "Gemini API and expert rule engines synthesize findings into max 5 prioritized, high-impact recommendations with code fixes.",
    },
    {
      icon: Clock,
      title: "Technical Debt Tracking",
      desc: "SonarQube-aligned remediation formulas translate code smells and architectural anti-patterns into estimated repair minutes.",
    },
  ];

  return (
    <div className="space-y-24 pb-16">
      {/* 1. Hero Section */}
      <section className="pt-12 sm:pt-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-semibold mb-6">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Next-Generation Software Quality Intelligence</span>
        </div>

        <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight max-w-4xl mx-auto leading-tight break-normal">
          Automated Code Quality Assessment with{" "}
          <span className="text-indigo-600">Static Analysis</span> and{" "}
          <span className="text-indigo-600">Machine Learning</span>
        </h1>

        <p className="mt-6 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
          Go beyond rigid linters. CodeSense unifies multi-engine static metrics, machine-learned defect prediction with SHAP explainability, and AI-driven remediation guidance.
        </p>

        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/projects"
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl text-sm font-semibold shadow-sm transition-all hover:shadow-md"
          >
            <span>Analyze your repo</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <a
            href="#how-it-works"
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 px-6 py-3 rounded-xl text-sm font-semibold shadow-sm transition-all"
          >
            <span>See how it works</span>
          </a>
        </div>

        {/* Stylized Miniature Dashboard Mockup */}
        <div className="mt-14 max-w-5xl mx-auto rounded-2xl border border-slate-200 bg-white p-4 sm:p-6 shadow-xl text-left w-full overflow-hidden">
          <div className="flex flex-wrap items-center justify-between pb-4 mb-5 border-b border-slate-100 gap-2">
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full bg-slate-200" />
              <span className="w-3 h-3 rounded-full bg-slate-200" />
              <span className="w-3 h-3 rounded-full bg-slate-200" />
              <span className="text-xs font-mono text-slate-400 ml-2 truncate max-w-[180px] sm:max-w-none">Live Dashboard Preview</span>
            </div>
            <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
              Analysis Finalized
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 mb-4">
            <div className="p-4 rounded-xl border border-slate-100 bg-slate-50/70 text-center">
              <span className="text-[10px] font-bold uppercase text-slate-500 tracking-wider block mb-1">Quality Score</span>
              <div className="text-3xl font-extrabold text-slate-900">88.4<span className="text-xs text-slate-400 font-normal">/100</span></div>
              <span className="inline-block mt-1 text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">Grade A • Ready</span>
            </div>
            <div className="p-4 rounded-xl border border-slate-100 bg-slate-50/70">
              <span className="text-[10px] font-bold uppercase text-slate-500 tracking-wider block mb-1">Executable Lines</span>
              <div className="text-2xl font-bold text-slate-900">14,280</div>
              <span className="text-[10px] text-slate-400 mt-0.5 block">Across 38 modules</span>
            </div>
            <div className="p-4 rounded-xl border border-slate-100 bg-slate-50/70">
              <span className="text-[10px] font-bold uppercase text-slate-500 tracking-wider block mb-1">Estimated Debt</span>
              <div className="text-2xl font-bold text-slate-900">1h 45m</div>
              <span className="text-[10px] text-slate-400 mt-0.5 block">Remediation time</span>
            </div>
            <div className="p-4 rounded-xl border border-slate-100 bg-slate-50/70">
              <span className="text-[10px] font-bold uppercase text-slate-500 tracking-wider block mb-1">ML Defect Risk</span>
              <div className="text-2xl font-bold text-slate-900">3.8%</div>
              <span className="text-[10px] text-slate-400 mt-0.5 block">XGBoost prediction</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl border border-slate-200 bg-white">
              <div className="flex flex-wrap items-center justify-between gap-1 mb-2">
                <span className="text-xs font-bold text-slate-900">Top Risky Module</span>
                <span className="text-[10px] font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded">18.4% Defect Likelihood</span>
              </div>
              <p className="text-xs font-mono text-slate-700 font-semibold mb-2 break-all">services/payment_orchestrator.py</p>
              <div className="flex flex-wrap gap-1.5">
                <span className="text-[10px] font-medium bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-200">
                  +14.2% Cyclomatic Complexity (19.0)
                </span>
                <span className="text-[10px] font-medium bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-200">
                  +8.5% High Coupling (CBO=11)
                </span>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-900">Prioritized AI Recommendation</span>
                <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded">High Impact</span>
              </div>
              <p className="text-xs font-bold text-slate-800 mb-1">Decompose Branching in execute_transaction()</p>
              <p className="text-[11px] text-slate-500 line-clamp-2">
                Deep nesting and high complexity spike the probability of boundary calculation errors. Extract sub-procedures into discrete handler strategies.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Problem / Why Section */}
      <section className="py-12 bg-white border-y border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">The Software Quality Dilemma</span>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight mt-2">
              Why Traditional Linters and Manual Reviews Fall Short
            </h2>
            <p className="text-sm text-slate-500 mt-2">
              Modern codebases face structural and architectural risks that simple syntax checkers cannot identify.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200">
              <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 mb-4">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-2">Static Linters Miss Latent Faults</h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Traditional linters focus on surface-level stylistic rules and syntax flags. They lack predictive capabilities and cannot evaluate whether high coupling (CBO) and low cohesion (LCOM) will precipitate runtime failure.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200">
              <div className="w-10 h-10 rounded-xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600 mb-4">
                <Bug className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-2">Manual Reviews Do Not Scale</h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                As pull request volume increases, manual peer review degrades into cursory glance checks. Teams lack systematic metrics to measure creeping technical debt or inheritance tree depth (DIT) across releases.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600 mb-4">
                <Sparkles className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-2">Alert Fatigue Without Fixes</h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Legacy tools dump thousands of trivial warnings that developers ignore. CodeSense uses machine learning to prioritize top risks and synthesizes actionable recommendations with concrete code fix patterns.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 3. How It Works Section */}
      <section id="how-it-works" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 scroll-mt-24">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Analysis Lifecycle</span>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight mt-2">
            How CodeSense Evaluates Your Codebase
          </h2>
          <p className="text-sm text-slate-500 mt-2">
            A 4-stage pipeline combining static analysis, AST inspection, ML defect scoring, and generative remediation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
          {/* Step 1 */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm relative">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-sm mb-4">
              1
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-1">Ingest Repository</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Upload any .zip archive or connect a public GitHub URL. The backend handles sandboxed extraction and multi-language discovery.
            </p>
          </div>

          {/* Step 2 */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm relative">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-sm mb-4">
              2
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-1">Static & AST Metrics</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Radon, Pylint, Bandit, ESLint, and custom AST analyzers compute cyclomatic complexity, maintainability, and Chidamber-Kemerer metrics.
            </p>
          </div>

          {/* Step 3 */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm relative">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-sm mb-4">
              3
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-1">ML Defect Prediction</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Our trained XGBoost model evaluates the metric vector of each module, computing defect probability (0–1) and SHAP feature contributions.
            </p>
          </div>

          {/* Step 4 */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm relative">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-sm mb-4">
              4
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-1">Actionable AI Report</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Gemini LLM curates findings into maximum 5 prioritized recommendations with impact ratings and suggested fixes, rendered on your dashboard.
            </p>
          </div>
        </div>
      </section>

      {/* 4. Features Grid */}
      <section id="features" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 scroll-mt-24">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Engine Capabilities</span>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight mt-2">
            Engineered for Modern Engineering Standards
          </h2>
          <p className="text-sm text-slate-500 mt-2">
            Every layer designed to turn raw codebase signals into actionable developer intelligence.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map((feat, idx) => {
            const Icon = feat.icon;
            return (
              <div key={idx} className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm hover:border-indigo-300 transition-all">
                <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mb-4">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900 mb-1.5">{feat.title}</h3>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">{feat.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* 5. Metrics Showcase */}
      <section id="metrics" className="py-12 bg-white border-y border-slate-200 scroll-mt-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Normalized Data Model</span>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight mt-2">
              The Fixed 15 Software Quality Metrics Set
            </h2>
            <p className="text-sm text-slate-500 mt-2">
              Sourced directly from our backend metrics service — standardized across Python, JavaScript, and TypeScript targets.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {metricsList.map((m, idx) => (
              <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600">
                    {m.category}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">#{idx + 1}</span>
                </div>
                <h4 className="text-xs font-bold text-slate-900 mt-1">{m.name}</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">{m.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 6. Sample Report Preview Panel */}
      <section id="preview" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 scroll-mt-24">
        <div className="text-center max-w-3xl mx-auto mb-10">
          <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Interactive Report Interface</span>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight mt-2">
            Sample Audit Report Preview
          </h2>
          <p className="text-sm text-slate-500 mt-2">
            A static preview of the real dashboard output generated for an audited repository.
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-8 relative w-full overflow-hidden">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-6 mb-6 border-b border-slate-100">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-amber-50 text-amber-800 border border-amber-200">
                  Illustrative Sample Data
                </span>
                <span className="text-xs text-slate-400">• FinTech Platform Audit</span>
              </div>
              <h3 className="text-base sm:text-lg font-bold text-slate-900 mt-1">Audit Run #1b1d7ad3 Summary</h3>
            </div>
            <Link
              href="/projects"
              className="inline-flex items-center space-x-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
            >
              <span>Launch Live Dashboard</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
              <span className="text-[10px] uppercase font-bold text-slate-500">Overall Score</span>
              <p className="text-2xl font-extrabold text-slate-900">86.2<span className="text-xs font-normal text-slate-400">/100</span></p>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
              <span className="text-[10px] uppercase font-bold text-slate-500">Cyclomatic Complexity</span>
              <p className="text-2xl font-extrabold text-slate-900">2.84</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
              <span className="text-[10px] uppercase font-bold text-slate-500">Maintainability Index</span>
              <p className="text-2xl font-extrabold text-slate-900">89.6</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
              <span className="text-[10px] uppercase font-bold text-slate-500">Test Coverage</span>
              <p className="text-2xl font-extrabold text-slate-900">85.0%</p>
            </div>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/40">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center space-x-2">
                <span className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center text-[10px] font-bold">1</span>
                <span className="text-xs font-bold text-slate-900">Resolve Insecure Cryptographic Hash (MD5)</span>
              </div>
              <span className="text-[10px] font-bold bg-rose-100 text-rose-800 px-2 py-0.5 rounded">Critical</span>
            </div>
            <p className="text-xs text-slate-600">
              Identified use of weak MD5 hash in app/auth_service.py:17. Vulnerable to pre-image and collision attacks.
            </p>
            <div className="mt-2.5 p-2 rounded bg-white border border-slate-200 text-[11px] font-mono text-slate-700">
              <span className="font-semibold text-indigo-600 block mb-0.5">Suggested Fix:</span>
              Replace hashlib.md5 with argon2 or bcrypt for credential verification.
            </div>
          </div>
        </div>
      </section>

      {/* 7. CTA Band */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-3xl bg-indigo-600 p-8 sm:p-12 text-center text-white shadow-lg">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Ready to harden your software codebase?
          </h2>
          <p className="text-indigo-100 text-sm max-w-xl mx-auto mt-2 mb-6 leading-relaxed">
            Ingest your Python, JavaScript, or TypeScript repositories in seconds. Get 15 normalized metrics, ML bug predictions, and prioritized fixes.
          </p>
          <Link
            href="/projects"
            className="inline-flex items-center space-x-2 bg-white text-indigo-700 hover:bg-indigo-50 px-6 py-3 rounded-xl text-sm font-bold shadow-md transition-all"
          >
            <span>Analyze a Repository</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* 8. Footer */}
      <footer className="border-t border-slate-200 bg-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-sm text-slate-900">CodeSense</span>
              <p className="text-xs text-slate-500">AI-Powered Software Quality Analyser</p>
            </div>
          </div>

          <div className="flex items-center space-x-6 text-xs font-semibold text-slate-600">
            <Link href="/projects" className="hover:text-indigo-600 transition-colors">Projects</Link>
            <a href="#how-it-works" className="hover:text-indigo-600 transition-colors">How it Works</a>
            <a href="#metrics" className="hover:text-indigo-600 transition-colors">Metrics</a>
            <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="hover:text-indigo-600 transition-colors">API Docs</a>
          </div>

          <p className="text-xs text-slate-400">
            Engineered for software engineering quality assurance & defect prediction.
          </p>
        </div>
      </footer>
    </div>
  );
}
