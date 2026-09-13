"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { 
  FolderGit2, Plus, Upload, Globe, ArrowRight, Clock, ShieldCheck, 
  Trash2, AlertCircle, FileCode, CheckCircle2, RefreshCw 
} from "lucide-react";
import { fetchProjects, createProject, triggerAnalysis, Project } from "@/lib/api";

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [inputMode, setInputMode] = useState<"upload" | "github">("upload");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [githubUrl, setGithubUrl] = useState("");

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await fetchProjects();
      setProjects(data);
    } catch (err: any) {
      setError(err.message || "Failed to load projects");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleCreateAndAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Project name is required.");
      return;
    }
    if (inputMode === "upload" && !selectedFile) {
      setError("Please select a .zip repository file to upload.");
      return;
    }
    if (inputMode === "github" && !githubUrl.trim()) {
      setError("Please provide a valid public GitHub URL.");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      // 1. Create project
      const proj = await createProject({
        name,
        description,
        repo_url: inputMode === "github" ? githubUrl : "",
      });

      // 2. Trigger analysis
      const formData = new FormData();
      if (inputMode === "upload" && selectedFile) {
        formData.append("file", selectedFile);
      } else if (inputMode === "github" && githubUrl) {
        formData.append("github_url", githubUrl);
      }

      const res = await triggerAnalysis(proj.id, formData);

      // 3. Redirect to live progress
      router.push(`/projects/${proj.id}/runs/${res.run_id}/progress`);
    } catch (err: any) {
      setError(err.message || "An error occurred during project submission.");
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="bg-white rounded-xl p-6 sm:p-8 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Code Repositories</h1>
          <p className="text-sm text-slate-600 mt-1">
            Analyze codebases for static metrics, ML defect risks, technical debt, and AI-driven recommendations.
          </p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="inline-flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>New Analysis</span>
        </button>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="bg-white rounded-xl p-12 text-center border border-slate-200">
          <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-3" />
          <p className="text-slate-600 text-sm">Loading projects...</p>
        </div>
      ) : projects.length === 0 ? (
        <div className="bg-white rounded-xl p-12 text-center border border-dashed border-slate-300">
          <FolderGit2 className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900">No projects analyzed yet</h3>
          <p className="text-sm text-slate-500 max-w-sm mx-auto mt-1 mb-6">
            Upload a .zip repository archive or connect a public GitHub repository to run your first quality audit.
          </p>
          <button
            onClick={() => setModalOpen(true)}
            className="inline-flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Analyze a Repository</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((proj) => (
            <div
              key={proj.id}
              className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:border-indigo-300 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-semibold text-slate-900 text-base leading-tight truncate">
                    {proj.name}
                  </h3>
                  <span className="shrink-0 text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium">
                    {proj.repo_url ? "GitHub" : "Local Archive"}
                  </span>
                </div>
                <p className="text-xs text-slate-500 line-clamp-2 mb-4">
                  {proj.description || "No description provided."}
                </p>
                <div className="flex items-center space-x-2 text-xs text-slate-400 mb-6">
                  <Clock className="w-3.5 h-3.5" />
                  <span>Created {new Date(proj.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                <Link
                  href={`/projects/${proj.id}`}
                  className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1"
                >
                  <span>View Project & Runs</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* New Project Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-8 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Analyze New Repository</h2>
                <p className="text-xs text-slate-500 mt-0.5">Ingest code to compute 15 metrics and ML bug risks</p>
              </div>
              <button
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold p-1"
              >
                ✕
              </button>
            </div>

            {error && (
              <div className="p-3 mb-4 rounded-lg bg-red-50 border border-red-200 flex items-start space-x-2 text-red-700 text-xs">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleCreateAndAnalyze} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Project Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Authentication Microservice"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3.5 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white text-slate-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Description
                </label>
                <input
                  type="text"
                  placeholder="Optional brief notes or tags"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3.5 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white text-slate-900"
                />
              </div>

              {/* Ingestion Source Tabs */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Repository Source
                </label>
                <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-lg mb-3">
                  <button
                    type="button"
                    onClick={() => setInputMode("upload")}
                    className={`py-1.5 text-xs font-medium rounded-md flex items-center justify-center space-x-1.5 transition-colors ${
                      inputMode === "upload" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    <Upload className="w-3.5 h-3.5" />
                    <span>Upload ZIP</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setInputMode("github")}
                    className={`py-1.5 text-xs font-medium rounded-md flex items-center justify-center space-x-1.5 transition-colors ${
                      inputMode === "github" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    <Globe className="w-3.5 h-3.5" />
                    <span>Public GitHub URL</span>
                  </button>
                </div>

                {inputMode === "upload" ? (
                  <div className="border-2 border-dashed border-slate-300 hover:border-indigo-400 rounded-xl p-6 text-center cursor-pointer relative bg-slate-50 transition-colors">
                    <input
                      type="file"
                      accept=".zip"
                      onChange={(e) => setSelectedFile(e.target.files ? e.target.files[0] : null)}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    <FileCode className="w-8 h-8 text-indigo-500 mx-auto mb-2" />
                    <p className="text-xs font-medium text-slate-700">
                      {selectedFile ? selectedFile.name : "Choose a .zip repo archive or drag & drop"}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1">Supports Python, JavaScript, TypeScript</p>
                  </div>
                ) : (
                  <div>
                    <input
                      type="url"
                      placeholder="https://github.com/owner/repository"
                      value={githubUrl}
                      onChange={(e) => setGithubUrl(e.target.value)}
                      className="w-full px-3.5 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white text-slate-900"
                    />
                    <p className="text-[11px] text-slate-500 mt-1">Repository must be publicly cloneable.</p>
                  </div>
                )}
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm disabled:opacity-50 flex items-center space-x-2"
                >
                  {submitting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>{submitting ? "Analyzing..." : "Start Analysis"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
