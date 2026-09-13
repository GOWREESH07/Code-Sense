import Link from "next/link";
import { ShieldCheck, Layers, GitCompare, Sparkles, FolderGit2 } from "lucide-react";

export default function Navbar() {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/projects" className="flex items-center space-x-3 group">
          <div className="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 group-hover:bg-indigo-100 transition-colors">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-bold text-lg text-slate-900 tracking-tight">CodeSense</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-medium border border-indigo-200">
                v1.0 AI
              </span>
            </div>
            <p className="text-xs text-slate-500 font-normal">AI-Powered Software Quality Analyser</p>
          </div>
        </Link>

        <nav className="flex items-center space-x-6">
          <Link
            href="/projects"
            className="flex items-center space-x-1.5 text-sm font-medium text-slate-700 hover:text-indigo-600 transition-colors"
          >
            <FolderGit2 className="w-4 h-4 text-slate-500" />
            <span>Projects</span>
          </Link>
          <div className="h-4 w-px bg-slate-200" />
          <div className="flex items-center space-x-2 text-xs text-slate-500 bg-slate-50 px-3 py-1.5 rounded-md border border-slate-200">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-medium text-slate-700">ML Engine Active</span>
          </div>
        </nav>
      </div>
    </header>
  );
}
