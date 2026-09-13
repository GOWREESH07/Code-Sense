"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  CheckCircle2, Circle, Clock, AlertCircle, RefreshCw, 
  ArrowRight, ShieldCheck, Binary, Sparkles, Code2 
} from "lucide-react";
import { fetchRunStatus, AnalysisRun } from "@/lib/api";

const STEPS = [
  { id: "queued", title: "Repository Ingestion", desc: "Extracting archive / cloning repository", icon: Code2 },
  { id: "analyzing", title: "Static Analysis Engine", desc: "Radon, Pylint, Bandit, ESLint, & AST metrics", icon: ShieldCheck },
  { id: "scoring", title: "ML Defect Prediction", desc: "Running trained model & calculating SHAP explanations", icon: Binary },
  { id: "recommending", title: "AI Recommendations", desc: "Synthesizing prioritized remediation plan", icon: Sparkles },
  { id: "done", title: "Audit Finalized", desc: "Compiling composite quality scores and dashboard", icon: CheckCircle2 },
];

export default function RunProgressPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const runId = params.runId as string;

  const [run, setRun] = useState<AnalysisRun | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout;

    const checkStatus = async () => {
      try {
        const data = await fetchRunStatus(runId);
        setRun(data);

        if (data.status === "done") {
          clearInterval(interval);
          setTimeout(() => {
            router.push(`/projects/${projectId}/runs/${runId}`);
          }, 1200);
        } else if (data.status === "failed") {
          clearInterval(interval);
          setError(data.error_message || "Analysis failed unexpectedly.");
        }
      } catch (err: any) {
        console.error("Status polling error:", err);
      }
    };

    checkStatus();
    interval = setInterval(checkStatus, 2000);

    return () => clearInterval(interval);
  }, [projectId, runId, router]);

  const currentStatus = run?.status || "queued";
  const getStepState = (stepId: string) => {
    const order = ["queued", "analyzing", "scoring", "recommending", "done"];
    const currIdx = order.indexOf(currentStatus);
    const stepIdx = order.indexOf(stepId);

    if (currentStatus === "failed") {
      return stepIdx <= currIdx ? "failed" : "pending";
    }
    if (stepIdx < currIdx) return "completed";
    if (stepIdx === currIdx) return "active";
    return "pending";
  };

  return (
    <div className="max-w-2xl mx-auto py-8">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mx-auto mb-3">
            <RefreshCw className={`w-6 h-6 ${currentStatus !== "done" && currentStatus !== "failed" ? "animate-spin" : ""}`} />
          </div>
          <h1 className="text-xl font-bold text-slate-900">
            {currentStatus === "done" ? "Analysis Complete!" : currentStatus === "failed" ? "Analysis Encountered an Error" : "Analyzing Codebase..."}
          </h1>
          <p className="text-xs text-slate-500 mt-1 font-mono">Run ID: {runId}</p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 flex items-start space-x-3 text-red-700 text-xs">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-800">Pipeline Error</p>
              <p className="mt-0.5">{error}</p>
              <div className="mt-3">
                <Link
                  href={`/projects/${projectId}`}
                  className="inline-flex items-center text-red-700 font-semibold underline hover:text-red-900"
                >
                  Return to Project
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Stepper */}
        <div className="space-y-4">
          {STEPS.map((step, idx) => {
            const state = getStepState(step.id);
            const Icon = step.icon;

            return (
              <div
                key={step.id}
                className={`flex items-start space-x-4 p-4 rounded-xl border transition-all ${
                  state === "active"
                    ? "bg-indigo-50/50 border-indigo-300 shadow-sm"
                    : state === "completed"
                    ? "bg-slate-50/70 border-slate-200"
                    : state === "failed"
                    ? "bg-red-50/30 border-red-200"
                    : "bg-white border-slate-100 opacity-60"
                }`}
              >
                <div className="mt-0.5 shrink-0">
                  {state === "completed" ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  ) : state === "active" ? (
                    <RefreshCw className="w-5 h-5 text-indigo-600 animate-spin" />
                  ) : state === "failed" ? (
                    <AlertCircle className="w-5 h-5 text-red-500" />
                  ) : (
                    <Circle className="w-5 h-5 text-slate-300" />
                  )}
                </div>

                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3
                      className={`text-sm font-semibold ${
                        state === "active" ? "text-indigo-950 font-bold" : "text-slate-900"
                      }`}
                    >
                      {step.title}
                    </h3>
                    <span
                      className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded ${
                        state === "completed"
                          ? "bg-emerald-100 text-emerald-800"
                          : state === "active"
                          ? "bg-indigo-100 text-indigo-800 animate-pulse"
                          : state === "failed"
                          ? "bg-red-100 text-red-800"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {state}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{step.desc}</p>
                </div>
              </div>
            );
          })}
        </div>

        {currentStatus === "done" && (
          <div className="mt-8 text-center">
            <Link
              href={`/projects/${projectId}/runs/${runId}`}
              className="inline-flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-lg text-sm font-semibold shadow-sm transition-colors"
            >
              <span>View Analysis Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
