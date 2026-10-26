"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck, FolderGit2, ArrowRight } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const isLanding = pathname === "/";

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-2.5 sm:space-x-3 group shrink-0">
          <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 group-hover:bg-indigo-100 transition-colors">
            <ShieldCheck className="w-5 h-5 sm:w-6 sm:h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-bold text-base sm:text-lg text-slate-900 tracking-tight">CodeSense</span>
              <span className="text-[10px] sm:text-[11px] px-1.5 sm:px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-semibold border border-indigo-200">
                v1.0 AI
              </span>
            </div>
            <p className="text-[11px] sm:text-xs text-slate-500 font-normal hidden sm:block">AI-Powered Software Quality Analyser</p>
          </div>
        </Link>

        <nav className="flex items-center space-x-2 sm:space-x-8">
          {isLanding && (
            <div className="hidden md:flex items-center space-x-6 text-xs font-semibold text-slate-600">
              <a href="#features" className="hover:text-indigo-600 transition-colors">Features</a>
              <a href="#how-it-works" className="hover:text-indigo-600 transition-colors">How it Works</a>
              <a href="#metrics" className="hover:text-indigo-600 transition-colors">Metrics</a>
              <a href="#preview" className="hover:text-indigo-600 transition-colors">Report Preview</a>
            </div>
          )}

          <div className="flex items-center space-x-2 sm:space-x-4">
            <Link
              href="/projects"
              className="hidden sm:flex items-center space-x-1.5 text-xs font-semibold text-slate-700 hover:text-indigo-600 transition-colors px-2 py-1"
            >
              <FolderGit2 className="w-4 h-4 text-slate-400" />
              <span>Projects</span>
            </Link>

            <Link
              href="/projects"
              className="inline-flex items-center space-x-1.5 bg-indigo-600 hover:bg-indigo-700 text-white px-3 sm:px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-sm transition-colors whitespace-nowrap"
            >
              <span>Get Started</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </nav>
      </div>
    </header>
  );
}
