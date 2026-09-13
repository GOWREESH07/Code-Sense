const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Project {
  id: string;
  name: string;
  description: string;
  repo_url: string;
  created_at: string;
  updated_at: string;
}

export interface AnalysisRun {
  id: string;
  project_id: string;
  status: "queued" | "analyzing" | "scoring" | "recommending" | "done" | "failed";
  overall_score: number | null;
  total_loc: number;
  total_complexity: number;
  bug_probability: number;
  tech_debt_minutes: number;
  error_message?: string;
  summary: any;
  created_at: string;
  completed_at?: string;
}

export interface FileMetric {
  id: string;
  run_id: string;
  file_path: string;
  language: string;
  loc: number;
  cyclomatic_complexity: number;
  maintainability_index: number;
  duplication_pct: number;
  cbo: number;
  lcom: number;
  dit: number;
  noc: number;
  comment_density: number;
  bug_probability: number;
  smells_count: number;
  top_contributing_factors?: Array<{
    feature: string;
    display_name: string;
    value: number;
    impact_pct: number;
    explanation: string;
  }>;
}

export interface DefectFinding {
  id: string;
  file_path: string;
  line_number: number;
  rule_id: string;
  severity: "info" | "warning" | "error" | "critical";
  tool: string;
  description: string;
}

export interface Recommendation {
  id: string;
  priority: number;
  title: string;
  category: string;
  description: string;
  suggested_fix: string;
  file_path?: string;
  impact: "Critical" | "High" | "Medium" | "Low";
}

export interface RunResults {
  run: AnalysisRun;
  file_metrics: FileMetric[];
  defects: DefectFinding[];
  recommendations: Recommendation[];
}

export interface CompareResult {
  project_id: string;
  run1: { id: string; created_at: string; overall_score: number };
  run2: { id: string; created_at: string; overall_score: number };
  metric_diffs: Array<{
    metric: string;
    label: string;
    base_value: number;
    compare_value: number;
    delta: number;
    improved: boolean;
  }>;
}

export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE_URL}/api/projects`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

export async function createProject(data: { name: string; description?: string; repo_url?: string }): Promise<Project> {
  const res = await fetch(`${API_BASE_URL}/api/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create project");
  return res.json();
}

export async function fetchProjectDetails(id: string): Promise<{ project: Project; runs: AnalysisRun[] }> {
  const res = await fetch(`${API_BASE_URL}/api/projects/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch project details");
  return res.json();
}

export async function triggerAnalysis(projectId: string, formData: FormData): Promise<{ run_id: string }> {
  const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}/analyze`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Analysis request failed" }));
    throw new Error(err.detail || "Failed to trigger analysis");
  }
  return res.json();
}

export async function fetchRunStatus(runId: string): Promise<AnalysisRun> {
  const res = await fetch(`${API_BASE_URL}/api/runs/${runId}/status`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch run status");
  return res.json();
}

export async function fetchRunResults(runId: string): Promise<RunResults> {
  const res = await fetch(`${API_BASE_URL}/api/runs/${runId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch run results");
  return res.json();
}

export async function fetchRunComparison(projectId: string, run1: string, run2: string): Promise<CompareResult> {
  const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}/compare?run1=${run1}&run2=${run2}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch run comparison");
  return res.json();
}
