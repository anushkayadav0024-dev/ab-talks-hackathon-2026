import React, { useState } from "react";
import { useInterview } from "../context/InterviewContext";
import { 
  CheckCircle2, 
  AlertTriangle, 
  ArrowRightCircle, 
  Sparkles, 
  RefreshCw, 
  FileText, 
  Layers, 
  MessageSquare, 
  ChevronDown, 
  Printer,
  TrendingUp
} from "lucide-react";

export default function ReportView() {
  const { feedback, resetSession, selectedCandidate, messages } = useInterview();
  const [showTranscript, setShowTranscript] = useState(false);

  if (!feedback) {
    return (
      <div className="max-w-md mx-auto p-6 bg-darkCard border border-darkBorder rounded-3xl text-center">
        <p className="text-slate-400 font-mono">No evaluation feedback available.</p>
        <button
          onClick={resetSession}
          className="mt-4 px-4 py-2 bg-teal-600 hover:bg-teal-500 rounded-xl text-white font-bold transition-colors"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  const candidateName = selectedCandidate?.member?.name || "Candidate";
  const candidateRole = selectedCandidate?.member?.jobRole || "AI Engineer";

  // Style readiness status colors
  const readiness = feedback.readiness || "Interview Ready";
  let readinessBadgeClass = "bg-sky-500/10 text-sky-400 border-sky-500/25";
  if (readiness.toLowerCase().includes("strong") || readiness.toLowerCase().includes("ready")) {
    readinessBadgeClass = "bg-emerald-500/10 text-emerald-400 border-emerald-500/25";
  } else if (readiness.toLowerCase().includes("practice") || readiness.toLowerCase().includes("needs")) {
    readinessBadgeClass = "bg-amber-500/10 text-amber-400 border-amber-500/25";
  }

  return (
    <div className="max-w-5xl mx-auto w-full space-y-6 animate-fade-in print:my-0 print:p-0 print:text-slate-900">
      
      {/* Print-Only Header Block */}
      <div className="hidden print:block border-b-2 border-slate-800 pb-4 mb-6">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">AI Interview Agent</h1>
            <p className="text-xs text-slate-500 font-mono">Personalized Cohort Evaluation</p>
          </div>
          <div className="text-right text-xs text-slate-500 font-mono">
            <p>Candidate: {candidateName}</p>
            <p>Date: {new Date().toLocaleDateString()}</p>
          </div>
        </div>
      </div>

      {/* Header Banner */}
      <div className="bg-darkCard border border-darkBorder rounded-3xl p-6 shadow-2xl relative overflow-hidden print:border-none print:shadow-none print:p-0">
        {/* Glow */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-teal-500/5 rounded-full filter blur-[100px] pointer-events-none print:hidden"></div>
        <div className="absolute -bottom-20 -left-20 w-96 h-96 bg-indigo-500/5 rounded-full filter blur-[100px] pointer-events-none print:hidden"></div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div className="flex items-start space-x-4">
            <div className="p-3 bg-teal-500/10 border border-teal-500/20 rounded-2xl text-teal-400 shrink-0 print:bg-slate-100 print:text-slate-800 print:border">
              <FileText className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[10px] uppercase font-mono tracking-widest text-slate-500 print:text-slate-600">
                  Evaluation Complete
                </span>
                <span className={`text-[10.5px] uppercase font-mono font-bold px-2.5 py-0.5 rounded-full border ${readinessBadgeClass}`}>
                  {readiness}
                </span>
              </div>
              <h2 className="text-2xl font-bold text-white tracking-tight print:text-slate-900">
                Interview Performance Assessment
              </h2>
              <p className="text-sm text-slate-400 print:text-slate-600">
                Candidate: <strong className="text-slate-200 print:text-slate-800">{candidateName}</strong> — {candidateRole}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 shrink-0 print:hidden">
            <button
              onClick={() => window.print()}
              className="flex items-center justify-center px-4 py-3 bg-slate-800 hover:bg-slate-700 text-slate-100 font-bold rounded-2xl border border-slate-700 hover:scale-[1.02] active:scale-[0.98] transition-all"
            >
              <Printer className="w-4 h-4 mr-2" />
              Print / Save PDF
            </button>
            <button
              onClick={resetSession}
              className="flex items-center justify-center px-4 py-3 bg-teal-600 hover:bg-teal-500 text-white font-bold rounded-2xl shadow-lg border border-teal-500/30 hover:scale-[1.02] active:scale-[0.98] transition-all"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              New Interview
            </button>
          </div>
        </div>
      </div>

      {/* Summary Box */}
      <div className="bg-darkCard border border-darkBorder rounded-3xl p-6 shadow-xl space-y-3 print:bg-white print:border-slate-200 print:text-slate-800">
        <h3 className="text-xs uppercase font-mono text-slate-500 tracking-wider flex items-center gap-1.5 print:text-slate-600">
          <Sparkles className="w-4 h-4 text-teal-400 print:text-slate-800" />
          Executive Summary
        </h3>
        <p className="text-slate-300 text-sm leading-relaxed print:text-slate-700">
          {feedback.summary}
        </p>
      </div>

      {/* Tri-Column Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 print:grid-cols-3">
        
        {/* Columns 1: Strengths */}
        <div className="bg-emerald-950/[0.05] border border-emerald-500/20 rounded-3xl p-6 shadow-md flex flex-col space-y-4 print:bg-white print:border-slate-200 print:border-l-4 print:border-l-emerald-500">
          <div className="flex items-center space-x-2 pb-3 border-b border-emerald-500/10">
            <div className="p-2 bg-emerald-500/10 rounded-xl text-emerald-400 border border-emerald-500/15 print:bg-emerald-100 print:text-emerald-800 print:border-none">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <h4 className="text-sm font-bold text-white uppercase tracking-wider font-mono print:text-emerald-900">
              Verified Strengths
            </h4>
          </div>
          <ul className="space-y-3 flex-1">
            {feedback.strengths.map((str, i) => (
              <li key={i} className="flex items-start space-x-2.5 text-xs leading-relaxed text-slate-300 print:text-slate-700">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0 mt-1.5"></span>
                <span>{str}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Columns 2: Gaps */}
        <div className="bg-amber-950/[0.05] border border-amber-500/20 rounded-3xl p-6 shadow-md flex flex-col space-y-4 print:bg-white print:border-slate-200 print:border-l-4 print:border-l-amber-500">
          <div className="flex items-center space-x-2 pb-3 border-b border-amber-500/10">
            <div className="p-2 bg-amber-500/10 rounded-xl text-amber-400 border border-amber-500/15 print:bg-amber-100 print:text-amber-800 print:border-none">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <h4 className="text-sm font-bold text-white uppercase tracking-wider font-mono print:text-amber-900">
              Identified Gaps
            </h4>
          </div>
          <ul className="space-y-3 flex-1">
            {feedback.gaps.map((gap, i) => (
              <li key={i} className="flex items-start space-x-2.5 text-xs leading-relaxed text-slate-300 print:text-slate-700">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0 mt-1.5"></span>
                <span>{gap}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Columns 3: Action Plan / Next Steps */}
        <div className="bg-indigo-950/[0.05] border border-indigo-500/20 rounded-3xl p-6 shadow-md flex flex-col space-y-4 print:bg-white print:border-slate-200 print:border-l-4 print:border-l-indigo-500">
          <div className="flex items-center space-x-2 pb-3 border-b border-indigo-500/10">
            <div className="p-2 bg-indigo-500/10 rounded-xl text-indigo-400 border border-indigo-500/15 print:bg-indigo-100 print:text-indigo-800 print:border-none">
              <ArrowRightCircle className="w-5 h-5" />
            </div>
            <h4 className="text-sm font-bold text-white uppercase tracking-wider font-mono print:text-indigo-900">
              Next Action Steps
            </h4>
          </div>
          <ul className="space-y-3 flex-1">
            {feedback.next.map((step, i) => (
              <li key={i} className="flex items-start space-x-2.5 text-xs leading-relaxed text-slate-300 print:text-slate-700">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0 mt-1.5"></span>
                <span>{step}</span>
              </li>
            ))}
          </ul>
        </div>

      </div>

      {/* Prediction vs. Performance Section */}
      {feedback.comparisons && feedback.comparisons.length > 0 && (
        <div className="bg-darkCard border border-darkBorder rounded-3xl p-6 shadow-xl space-y-4 print:bg-white print:border-slate-200">
          <h3 className="text-xs uppercase font-mono text-slate-500 tracking-wider flex items-center gap-1.5 print:text-slate-600">
            <TrendingUp className="w-4 h-4 text-teal-400 print:text-slate-800" />
            Prediction vs. Performance Comparison
          </h3>
          <div className="space-y-3">
            {feedback.comparisons.map((item, i) => {
              let verdictBadgeClass = "";
              const assessment = item.assessment || "Confirmed";
              if (assessment === "Confirmed") {
                verdictBadgeClass = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
              } else if (assessment === "Contradicted") {
                verdictBadgeClass = "bg-rose-500/10 text-rose-400 border-rose-500/20";
              } else if (assessment === "Partially Confirmed") {
                verdictBadgeClass = "bg-amber-500/10 text-amber-400 border-amber-500/20";
              } else {
                verdictBadgeClass = "bg-slate-500/10 text-slate-400 border-slate-500/20";
              }

              let predictedBadgeClass = "";
              const predicted = item.predicted || "Core";
              if (predicted.toLowerCase() === "strength") {
                predictedBadgeClass = "bg-emerald-500/10 text-emerald-400 border-emerald-500/15";
              } else if (predicted.toLowerCase() === "gap") {
                predictedBadgeClass = "bg-rose-500/10 text-rose-400 border-rose-500/15";
              } else if (predicted.toLowerCase() === "struggle") {
                predictedBadgeClass = "bg-amber-500/10 text-amber-400 border-amber-500/15";
              } else {
                predictedBadgeClass = "bg-sky-500/10 text-sky-400 border-sky-500/15";
              }

              return (
                <div key={i} className="p-5 bg-darkBg/40 border border-darkBorder/60 rounded-2xl space-y-3.5 print:bg-slate-50 print:border-slate-200 print:text-slate-800 animate-fade-in">
                  
                  {/* Title & Badge Header Row */}
                  <div className="flex items-center justify-between flex-wrap gap-2 pb-2 border-b border-darkBorder/30">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded bg-slate-800 border border-slate-700/50 text-slate-300 font-mono text-[10px] font-bold print:bg-slate-200 print:text-slate-800">
                        Day {item.day}
                      </span>
                      <h4 className="text-xs font-bold text-white leading-tight print:text-slate-900">{item.title}</h4>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={`text-[9px] uppercase font-mono font-bold px-2 py-0.5 rounded border ${predictedBadgeClass}`}>
                        Prior: {predicted}
                      </span>
                      <span className={`text-[9.5px] uppercase font-mono font-bold px-2.5 py-0.5 rounded-full border ${verdictBadgeClass}`}>
                        {assessment}
                      </span>
                    </div>
                  </div>

                  {/* Evidence & Evaluation Details Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="space-y-3">
                      <div>
                        <span className="text-[10px] font-mono text-slate-500 block uppercase tracking-wider">B. Interview Evidence</span>
                        <p className="text-slate-300 print:text-slate-700 mt-1 italic leading-relaxed">"{item.evidence}"</p>
                      </div>
                      {item.strengths && item.strengths.length > 0 && (
                        <div>
                          <span className="text-[10px] font-mono text-emerald-400 block uppercase tracking-wider">E. Verified Strengths</span>
                          <ul className="list-disc list-inside text-slate-400 print:text-slate-600 mt-1 space-y-1">
                            {item.strengths.map((str, idx) => <li key={idx}>{str}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>
                    
                    <div className="space-y-3">
                      {item.gaps && item.gaps.length > 0 && (
                        <div>
                          <span className="text-[10px] font-mono text-rose-400 block uppercase tracking-wider">D. Knowledge Gaps</span>
                          <ul className="list-disc list-inside text-slate-400 print:text-slate-600 mt-1 space-y-1">
                            {item.gaps.map((gap, idx) => <li key={idx}>{gap}</li>)}
                          </ul>
                        </div>
                      )}
                      {item.next_actions && item.next_actions.length > 0 && (
                        <div>
                          <span className="text-[10px] font-mono text-indigo-400 block uppercase tracking-wider">F. Next Actions</span>
                          <ul className="list-disc list-inside text-slate-400 print:text-slate-600 mt-1 space-y-1">
                            {item.next_actions.map((act, idx) => <li key={idx}>{act}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>

                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Syllabus Day Breakdown Section */}
      {feedback.breakdown && feedback.breakdown.length > 0 && (
        <div className="bg-darkCard border border-darkBorder rounded-3xl p-6 shadow-xl space-y-4 print:bg-white print:border-slate-200">
          <h3 className="text-xs uppercase font-mono text-slate-500 tracking-wider flex items-center gap-1.5 print:text-slate-600">
            <Layers className="w-4 h-4 text-teal-400 print:text-slate-800" />
            Syllabus Day-by-Day Assessment
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 print:grid-cols-2">
            {feedback.breakdown.map((item, i) => (
              <div key={i} className="p-4 bg-darkBg/40 border border-darkBorder/60 rounded-2xl flex flex-col space-y-2 print:bg-slate-50 print:border-slate-200 print:text-slate-800">
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded bg-teal-500/10 border border-teal-500/20 text-teal-400 font-mono text-[10px] font-bold print:bg-slate-200 print:text-slate-800">
                    Day {item.day}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">Curriculum Module</span>
                </div>
                <h4 className="text-xs font-bold text-white leading-tight print:text-slate-900">{item.title}</h4>
                <p className="text-xs text-slate-300 leading-relaxed italic print:text-slate-600">"{item.assessment}"</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Expandable Transcript Accordion */}
      <div className="bg-darkCard border border-darkBorder rounded-3xl overflow-hidden shadow-xl print:hidden">
        <button
          onClick={() => setShowTranscript(!showTranscript)}
          className="w-full px-6 py-5 flex items-center justify-between hover:bg-slate-800/30 transition-colors"
        >
          <h3 className="text-xs uppercase font-mono text-slate-500 tracking-wider flex items-center gap-1.5">
            <MessageSquare className="w-4 h-4 text-teal-400" />
            View Full Interview Transcript
          </h3>
          <ChevronDown className={`w-5 h-5 text-slate-500 transition-transform duration-200 ${showTranscript ? "rotate-180" : ""}`} />
        </button>
        {showTranscript && (
          <div className="px-6 pb-6 pt-2 border-t border-darkBorder/40 space-y-4 max-h-[30rem] overflow-y-auto bg-darkBg/25">
            {messages.map((msg, idx) => {
              const isInterviewer = msg.sender === "interviewer";
              if (idx === 0 && !isInterviewer) return null; // Hide starter prompt
              
              return (
                <div key={idx} className={`flex flex-col space-y-1 ${isInterviewer ? "items-start" : "items-end"}`}>
                  <span className="text-[10px] font-mono text-slate-500">
                    {isInterviewer ? "AI Technical Interviewer" : "Candidate"}
                  </span>
                  <div className={`px-4 py-2.5 rounded-2xl text-xs max-w-[85%] border leading-relaxed break-words ${
                    isInterviewer
                      ? "bg-slate-800/60 border-slate-700/50 text-slate-200 rounded-tl-none"
                      : "bg-teal-600 border-teal-500/20 text-white rounded-tr-none"
                  }`}>
                    {msg.text}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
}
