import React from "react";
import { useInterview } from "../context/InterviewContext";
import { CheckCircle2, ArrowRight, ClipboardList } from "lucide-react";

export default function ConfirmationView({ onProceed }) {
  const { questionCount, daysCovered, selectedCandidate } = useInterview();
  
  const candidateName = selectedCandidate?.member?.name || "Candidate";

  return (
    <div className="max-w-md mx-auto w-full text-center space-y-6 animate-fade-in py-12">
      <div className="bg-darkCard border border-darkBorder rounded-3xl p-8 shadow-2xl relative overflow-hidden">
        {/* Glow */}
        <div className="absolute -top-10 -left-10 w-40 h-40 bg-teal-500/10 rounded-full filter blur-xl pointer-events-none"></div>
        <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-indigo-500/10 rounded-full filter blur-xl pointer-events-none"></div>

        {/* Success Icon */}
        <div className="flex justify-center mb-6">
          <div className="relative">
            <div className="absolute inset-0 bg-teal-500/20 rounded-full blur-md animate-ping"></div>
            <div className="p-4 bg-teal-500/10 border border-teal-500/20 rounded-full text-teal-400 relative z-10">
              <CheckCircle2 className="w-16 h-16 animate-bounce" />
            </div>
          </div>
        </div>

        {/* Messaging */}
        <div className="space-y-2">
          <span className="text-[10px] uppercase font-mono tracking-widest text-teal-400 bg-teal-500/10 px-3 py-1 rounded-full border border-teal-500/20">
            Session Completed
          </span>
          <h2 className="text-2xl font-bold text-white tracking-tight mt-2">
            Interview Finished!
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed max-w-xs mx-auto">
            Thank you, {candidateName}. Your responses have been recorded and successfully compiled for the evaluation panel.
          </p>
        </div>

        {/* Stats card */}
        <div className="grid grid-cols-2 gap-4 mt-6 bg-darkBg/60 border border-darkBorder/80 p-4 rounded-2xl">
          <div className="text-center">
            <p className="text-2xl font-bold text-teal-400">{questionCount}</p>
            <p className="text-[9px] uppercase font-mono text-slate-500">Questions Answered</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-indigo-400">{daysCovered.length}</p>
            <p className="text-[9px] uppercase font-mono text-slate-500">Topics Covered</p>
          </div>
        </div>

        {/* CTA */}
        <button
          onClick={onProceed}
          className="mt-8 w-full py-4 bg-teal-600 hover:bg-teal-500 text-white font-bold rounded-2xl shadow-lg border border-teal-500/30 hover:scale-[1.01] active:scale-[0.99] transition-all flex items-center justify-center gap-2 group"
        >
          <ClipboardList className="w-5 h-5" />
          <span>View Performance Report</span>
          <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
        </button>
      </div>
    </div>
  );
}
