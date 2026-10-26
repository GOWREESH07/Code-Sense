"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, GitCompare, ArrowUpRight, ArrowDownRight, 
  Minus, RefreshCw, AlertCircle, ShieldCheck, CheckCircle2 
} from "lucide-react";
import { fetchRunComparison, fetchProjectDetails, CompareResult, AnalysisRun } from "@/lib/api";

export default function CompareRunsPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const projectId = params.id as string;

  const initialRun1 = searchParams.get("run1") || "";
  const initialRun2 = searchParams.get("run2") || "";

  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [run1Id, setRun1Id] = useState(initialRun1);
  const [run2Id, setRun2Id] = useState(initialRun2);
  const [compareData, setCompareData] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load project runs to allow selecting
  useEffect(() => {
    const loadRuns = async () => {
      try {
        const details = await fetchProjectDetails(projectId);
        const doneRuns = details.runs.filter((r) => r.status === "done");
        setRuns(doneRuns);

        if (!run1Id && doneRuns.length >= 2) {
          setRun1Id(doneRuns[1].id);
        }
        if (!run2Id && doneRuns.length >= 1) {
          setRun2Id(doneRuns[0].id);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load project runs");
      }
    };
    loadRuns();
  }, [projectId]);

  // Fetch comparison when run1Id and run2Id change
  useEffect(() => {
    if (!run1Id || !run2Id) {
      setLoading(false);
      return;
    }
    const loadComparison = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchRunComparison(projectId, run1Id, run2Id);
        setCompareData(data);
      } catch (err: any) {
        setError(err.message || "Failed to compare runs");
      } finally {
        setLoading(false);
      }
    };
    loadComparison();
  }, [projectId, run1Id, run2Id]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Header */}
      <div>
        <Link
          href={`/projects/${projectId}`}
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors mb-2"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Project History</span>
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Run Diff & Metric Comparison</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Side-by-side delta analysis tracking quality progression across code commits.
            </p>
          </div>
        </div>
      </div>

      {/* Run Selection Card */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-4">Select Runs to Diff</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1.5">Base Baseline Run (Before)</label>
            <select
              value={run1Id}
              onChange={(e) => setRun1Id(e.target.value)}
              className="w-full px-3.5 py-2 text-xs rounded-lg border border-slate-300 bg-white text-slate-900 focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Select baseline run...</option>
              {runs.map((r) => (
                <option key={r.id} value={r.id}>
                  {new Date(r.created_at).toLocaleString()} • Score: {r.overall_score || "—"} ({r.id.substring(0, 8)})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1.5">Comparison Target Run (After)</label>
            <select
              value={run2Id}
              onChange={(e) => setRun2Id(e.target.value)}
              className="w-full px-3.5 py-2 text-xs rounded-lg border border-slate-300 bg-white text-slate-900 focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Select target run...</option>
              {runs.map((r) => (
                <option key={r.id} value={r.id}>
                  {new Date(r.created_at).toLocaleString()} • Score: {r.overall_score || "—"} ({r.id.substring(0, 8)})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="bg-white rounded-2xl p-16 text-center border border-slate-200">
          <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-3" />
          <p className="text-slate-600 text-sm">Computing metric deltas...</p>
        </div>
      ) : !compareData ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-dashed border-slate-200">
          <GitCompare className="w-10 h-10 text-slate-400 mx-auto mb-3" />
          <p className="text-slate-700 font-semibold text-sm">Please select two distinct runs to compare</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center space-x-6 text-xs">
              <div>
                <span className="text-slate-400 uppercase font-bold text-[10px] block">Baseline</span>
                <span className="font-semibold text-slate-800">
                  {new Date(compareData.run1.created_at).toLocaleDateString()} (Score: {compareData.run1.overall_score})
                </span>
              </div>
              <div className="text-slate-300 font-bold">vs</div>
              <div>
                <span className="text-slate-400 uppercase font-bold text-[10px] block">Target</span>
                <span className="font-semibold text-slate-800">
                  {new Date(compareData.run2.created_at).toLocaleDateString()} (Score: {compareData.run2.overall_score})
                </span>
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-6">Quality Metric Dimension</th>
                  <th className="py-3 px-6">Baseline Value</th>
                  <th className="py-3 px-6">Target Value</th>
                  <th className="py-3 px-6 text-right">Delta / Trend</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                {compareData.metric_diffs.map((diff) => {
                  const isZero = diff.delta === 0;
                  return (
                    <tr key={diff.metric} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3.5 px-6 font-medium text-slate-900">{diff.label}</td>
                      <td className="py-3.5 px-6 font-mono">{diff.base_value}</td>
                      <td className="py-3.5 px-6 font-mono">{diff.compare_value}</td>
                      <td className="py-3.5 px-6 text-right">
                        {isZero ? (
                          <span className="inline-flex items-center text-slate-400 font-mono text-xs">
                            <Minus className="w-3.5 h-3.5 mr-1" />
                            <span>0.0</span>
                          </span>
                        ) : diff.improved ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                            <span>{diff.delta > 0 ? `+${diff.delta}` : diff.delta} (Improved)</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                            <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />
                            <span>{diff.delta > 0 ? `+${diff.delta}` : diff.delta} (Regressed)</span>
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
