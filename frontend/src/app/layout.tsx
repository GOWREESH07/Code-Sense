import type { Metadata } from "next";
import Navbar from "@/components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "CodeSense — AI-Powered Software Quality Analyser",
  description: "Automated code quality assessment with static analysis, 15 software metrics, ML defect prediction, and AI recommendations.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full bg-slate-50 scroll-smooth">
      <body className="min-h-full flex flex-col bg-[#F8FAFC] text-slate-900 antialiased overflow-x-hidden">
        <Navbar />
        <main className="flex-1 w-full overflow-x-hidden">
          {children}
        </main>
      </body>
    </html>
  );
}
