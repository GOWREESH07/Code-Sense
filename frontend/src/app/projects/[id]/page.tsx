"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { 
  ArrowLeft, Plus, Play, GitCompare, Clock, ShieldCheck, 
  FileCode, CheckCircle2, AlertTriangle, RefreshCw, Upload, Globe 
} from "lucide-react";
import { fetchProjectDetails, triggerAnalysis, Project, AnalysisRun } from "@/lib/api";

export default function ProjectDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Run selection for comparison
  const [selectedRuns, setSelectedRuns] = useState<string[]>([]);

  // Modal for new run
  const [modalOpen, setModalOpen] = useState(false);
  const [inputMode, setInputMode] = useState<"upload" | "github">("upload");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [githubUrl, setGithubUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await fetchProjectDetails(projectId);
      setProject(data.project);
      setRuns(data.runs);
      if (data.project.repo_url) {
        setGithubUrl(data.project.repo_url);
        setInputMode("github");
      }
    } catch (err: any) {
      setError(err.message || "Failed to load project details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [projectId]);

  const toggleRunSelect = (runId: string) => {
    if (selectedRuns.includes(runId)) {
      setSelectedRuns(selectedRuns.filter((id) => id !== runId));
    } else {
      if (selectedRuns.length >= 2) {
        setSelectedRuns([selectedRuns[1], runId]);
      } else {
        setSelectedRuns([...selectedRuns, runId]);
      }
    }
  };

  const handleStartAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setError(null);

      const formData = new FormData();
      if (inputMode === "upload" && selectedFile) {
        formData.append("file", selectedFile);
      } else if (inputMode === "github" && githubUrl) {
        formData.append("github_url", githubUrl);
      } else {
        setError("Please provide a repository file or URL.");
        setSubmitting(false);
        return;
      }

      const res = await triggerAnalysis(projectId, formData);
      router.push(`/projects/${projectId}/runs/${res.run_id}/progress`);
    } catch (err: any) {
      setError(err.message || "Failed to trigger analysis run");
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl p-12 text-center border border-slate-200">
        <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-3" />
        <p className="text-slate-600 text-sm">Loading project analysis history...</p>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="bg-white rounded-xl p-8 text-center border border-slate-200">
        <p className="text-slate-700 font-semibold mb-4">Project not found</p>
        <Link href="/projects" className="text-indigo-600 text-sm font-medium hover:underline">
          Return to projects
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Back button & Breadcrumb */}
      <div>
        <Link
          href="/projects"
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Projects</span>
        </Link>
      </div>

      {/* Project Overview Card */}
      <div className="bg-white rounded-xl p-6 sm:p-8 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div>
          <div className="flex items-center space-x-3 mb-1.5">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{project.name}</h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium">
              {runs.length} {runs.length === 1 ? "Run" : "Runs"}
            </span>
          </div>
          <p className="text-sm text-slate-600 max-w-2xl">
            {project.description || "No project description provided."}
          </p>
          {project.repo_url && (
            <div className="mt-3 flex items-center space-x-2 text-xs text-indigo-600 font-mono">
              <Globe className="w-3.5 h-3.5" />
              <a href={project.repo_url} target="_blank" rel="noreferrer" className="hover:underline">
                {project.repo_url}
              </a>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-3">
          {selectedRuns.length === 2 && (
            <Link
              href={`/projects/${projectId}/compare?run1=${selectedRuns[0]}&run2=${selectedRuns[1]}`}
              className="inline-flex items-center space-x-2 bg-white border border-indigo-200 text-indigo-700 hover:bg-indigo-50 px-4 py-2.5 rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              <GitCompare className="w-4 h-4" />
              <span>Compare Selected (2)</span>
            </Link>
          )}
          <button
            onClick={() => setModalOpen(true)}
            className="inline-flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <Play className="w-4 h-4" />
            <span>Run New Analysis</span>
          </button>
        </div>
      </div>

      {/* Runs List */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">Analysis Runs History</h2>
            <p className="text-xs text-slate-500 mt-0.5">Select any two runs to compare quality metric diffs</p>
          </div>
          {selectedRuns.length > 0 && (
            <span className="text-xs text-indigo-600 font-medium bg-indigo-50 px-2.5 py-1 rounded-md border border-indigo-100">
              {selectedRuns.length} selected for comparison
            </span>
          )}
        </div>

        {runs.length === 0 ? (
          <div className="p-12 text-center">
            <ShieldCheck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-700 font-medium text-sm">No analysis runs recorded yet</p>
            <p className="text-slate-500 text-xs mt-1 mb-4">Start your first audit to see metrics and defect predictions.</p>
            <button
              onClick={() => setModalOpen(true)}
              className="inline-flex items-center space-x-1.5 bg-indigo-600 hover:bg-indigo-700 text-white px-3.5 py-1.5 rounded-lg text-xs font-medium"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Run Analysis</span>
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4 w-10 text-center">Compare</th>
                  <th className="py-3 px-4">Run Status</th>
                  <th className="py-3 px-4">Overall Score</th>
                  <th className="py-3 px-4">Total LOC</th>
                  <th className="py-3 px-4">Avg Complexity</th>
                  <th className="py-3 px-4">Bug Risk</th>
                  <th className="py-3 px-4">Tech Debt</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                {runs.map((r) => {
                  const isDone = r.status === "done";
                  const isSelected = selectedRuns.includes(r.id);
                  return (
                    <tr key={r.id} className={`hover:bg-slate-50/80 transition-colors ${isSelected ? "bg-indigo-50/40" : ""}`}>
                      <td className="py-3.5 px-4 text-center">
                        <input
                          type="checkbox"
                          disabled={!isDone}
                          checked={isSelected}
                          onChange={() => toggleRunSelect(r.id)}
                          className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                        />
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold capitalize ${
                            r.status === "done"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : r.status === "failed"
                              ? "bg-red-50 text-red-700 border border-red-200"
                              : "bg-indigo-50 text-indigo-700 border border-indigo-200 animate-pulse"
                          }`}
                        >
                          {r.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        {r.overall_score !== null ? (
                          <div className="flex items-center space-x-1.5">
                            <span className="font-bold text-slate-900 text-sm">{r.overall_score}</span>
                            <span className="text-slate-400 text-[11px]">/ 100</span>
                          </div>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 font-mono font-medium">{r.total_loc?.toLocaleString() || "—"}</td>
                      <td className="py-3.5 px-4 font-mono font-medium">{r.total_complexity || "—"}</td>
                      <td className="py-3.5 px-4">
                        {r.bug_probability !== undefined ? (
                          <span className={`font-semibold ${r.bug_probability > 0.4 ? "text-amber-700" : "text-slate-700"}`}>
                            {(r.bug_probability * 100).toFixed(1)}%
                          </span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        {r.tech_debt_minutes ? (
                          <span className="text-slate-700 font-medium">
                            {Math.floor(r.tech_debt_minutes / 60)}h {r.tech_debt_minutes % 60}m
                          </span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-slate-500">
                        {new Date(r.created_at).toLocaleString()}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        {isDone ? (
                          <Link
                            href={`/projects/${projectId}/runs/${r.id}`}
                            className="inline-flex items-center space-x-1 text-indigo-600 hover:text-indigo-800 font-semibold text-xs"
                          >
                            <span>Dashboard</span>
                            <span>→</span>
                          </Link>
                        ) : (
                          <Link
                            href={`/projects/${projectId}/runs/${r.id}/progress`}
                            className="inline-flex items-center space-x-1 text-slate-600 hover:text-slate-800 font-semibold text-xs"
                          >
                            <span>Progress</span>
                            <span>→</span>
                          </Link>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* New Run Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
              <h3 className="text-lg font-bold text-slate-900">Run New Analysis</h3>
              <button onClick={() => setModalOpen(false)} className="text-slate-400 hover:text-slate-600 font-bold">
                ✕
              </button>
            </div>

            {error && (
              <div className="p-3 mb-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs">
                {error}
              </div>
            )}

            <form onSubmit={handleStartAnalysis} className="space-y-4">
              <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-lg mb-2">
                <button
                  type="button"
                  onClick={() => setInputMode("upload")}
                  className={`py-1.5 text-xs font-medium rounded-md ${
                    inputMode === "upload" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
                  }`}
                >
                  Upload ZIP
                </button>
                <button
                  type="button"
                  onClick={() => setInputMode("github")}
                  className={`py-1.5 text-xs font-medium rounded-md ${
                    inputMode === "github" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
                  }`}
                >
                  GitHub URL
                </button>
              </div>

              {inputMode === "upload" ? (
                <div className="border-2 border-dashed border-slate-300 rounded-xl p-5 text-center relative bg-slate-50">
                  <input
                    type="file"
                    accept=".zip"
                    onChange={(e) => setSelectedFile(e.target.files ? e.target.files[0] : null)}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  <FileCode className="w-6 h-6 text-indigo-500 mx-auto mb-1.5" />
                  <p className="text-xs font-medium text-slate-700">
                    {selectedFile ? selectedFile.name : "Select .zip archive"}
                  </p>
                </div>
              ) : (
                <input
                  type="url"
                  placeholder="https://github.com/owner/repository"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 bg-white text-slate-900"
                />
              )}

              <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm disabled:opacity-50"
                >
                  {submitting ? "Starting..." : "Start Analysis"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
