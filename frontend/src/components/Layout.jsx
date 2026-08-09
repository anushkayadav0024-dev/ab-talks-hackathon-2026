import React from "react";
import { Terminal, Cpu } from "lucide-react";

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-darkBg text-slate-100 flex flex-col">
      {/* Sleek Header */}
      <header className="border-b border-darkBorder bg-darkCard/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 print:hidden">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-teal-500/10 border border-teal-500/20 rounded-lg text-teal-400">
              <Cpu className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                AI Interview Agent
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 bg-teal-500/20 text-teal-300 rounded border border-teal-500/30">
                  v1.0
                </span>
              </h1>
              <p className="text-xs text-slate-400">Personalized Cohort Evaluation</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-2 text-xs text-slate-400 font-mono">
              <span className="w-2.5 h-2.5 rounded-full bg-teal-500 inline-block animate-ping"></span>
              <span>Backend Connected</span>
            </span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 w-full max-w-6xl mx-auto p-4 md:p-6 flex flex-col justify-center">
        {children}
      </main>

      {/* Footer */}
      <footer className="py-6 border-t border-darkBorder text-center text-xs text-slate-500 font-mono print:hidden">
        <p>© 2026 AB Talks AI Cohort Hackathon. Built for the future of engineering.</p>
      </footer>
    </div>
  );
}
