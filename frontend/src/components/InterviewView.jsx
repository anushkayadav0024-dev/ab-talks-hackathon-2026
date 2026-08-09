import React, { useState, useRef, useEffect } from "react";
import { useInterview } from "../context/InterviewContext";
import { Send, Terminal, User, Sparkles, Check, AlertCircle, RefreshCw, HelpCircle } from "lucide-react";

export default function InterviewView() {
  const {
    selectedCandidate,
    messages,
    loading,
    error,
    questionCount,
    daysCovered,
    interviewPlan,
    focusDay,
    submitAnswer,
    resetSession
  } = useInterview();

  const [input, setInput] = useState("");
  const [expandedReasons, setExpandedReasons] = useState(new Set());

  const toggleReason = (idx) => {
    setExpandedReasons(prev => {
      const next = new Set(prev);
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        next.add(idx);
      }
      return next;
    });
  };

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Focus textarea on load/loading done
  useEffect(() => {
    if (!loading) {
      textareaRef.current?.focus();
    }
  }, [loading]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;
    submitAnswer(input.trim());
    setInput("");
  };

  const handleKeyDown = (e) => {
    // Submit on Enter, allow shift+Enter for newline
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const candidateName = selectedCandidate?.member?.name || "Candidate";
  const candidateRole = selectedCandidate?.member?.jobRole || "AI Engineer";

  // Escalate color as it nears the 8-question goal
  const getProgressBarColor = () => {
    if (questionCount < 4) return "bg-sky-500";
    if (questionCount < 8) return "bg-amber-500";
    return "bg-teal-500 animate-pulse";
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-140px)] animate-fade-in max-w-7xl mx-auto w-full">
      
      {/* 1. Sidebar Panel: Profile & Plan */}
      <div className="lg:col-span-1 bg-darkCard border border-darkBorder rounded-3xl p-5 flex flex-col justify-between overflow-y-auto">
        <div className="space-y-5">
          {/* Candidate Card */}
          <div>
            <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest block mb-1">
              Active Candidate
            </span>
            <h3 className="text-lg font-bold text-white leading-tight">{candidateName}</h3>
            <p className="text-xs text-teal-400 font-medium mt-0.5">{candidateRole}</p>
          </div>

          <div className="h-px bg-darkBorder/60"></div>

          {/* Progress Stats */}
          <div>
            <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest block mb-2">
              Interview Status
            </span>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs font-mono text-slate-400 mb-1">
                  <span>Questions Asked</span>
                  <span className="text-teal-400 font-bold">{questionCount}</span>
                </div>
                <div className="w-full bg-darkBg rounded-full h-2 overflow-hidden border border-darkBorder/40">
                  <div
                    className={`${getProgressBarColor()} h-2 transition-all duration-500 rounded-full`}
                    style={{ width: `${Math.min((questionCount / 8) * 100, 100)}%` }}
                  ></div>
                </div>
                <p className="text-[10px] text-slate-500 font-mono mt-1 text-right">
                  Goal: minimum 8 questions
                </p>
              </div>
            </div>
          </div>

          <div className="h-px bg-darkBorder/60"></div>

          {/* Personalized plan details */}
          <div>
            <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest block mb-2">
              Personalized Syllabus Days
            </span>
            {interviewPlan && interviewPlan.length > 0 ? (
              <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                {interviewPlan.map((m, i) => {
                  const isDayCovered = daysCovered.includes(m.day);
                  const isActive = m.day === focusDay;
                  
                  // Style badges per mission type
                  let typeBadge = null;
                  if (m.type === "strength") {
                    typeBadge = <span className="text-[8px] uppercase tracking-wider font-mono font-bold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">Strength</span>;
                  } else if (m.type === "struggle") {
                    typeBadge = <span className="text-[8px] uppercase tracking-wider font-mono font-bold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/25">Struggle</span>;
                  } else if (m.type === "gap") {
                    typeBadge = <span className="text-[8px] uppercase tracking-wider font-mono font-bold px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/25">Gap</span>;
                  } else {
                    typeBadge = <span className="text-[8px] uppercase tracking-wider font-mono font-bold px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/25">Core Topic</span>;
                  }

                  // Find matching candidate mission details for passed/attempts
                  const missionDetails = selectedCandidate?.missions?.find(candM => candM.day === m.day) || {};
                  const attempts = missionDetails.attempts || 1;
                  const passed = missionDetails.passed || false;
                  const skipped = missionDetails.skipped || false;

                  let statusBadge = null;
                  if (passed) {
                    statusBadge = <span className="px-1.5 py-0.5 rounded bg-emerald-950/40 text-emerald-400 border border-emerald-500/15 font-mono text-[9px]">Passed ({attempts} att)</span>;
                  } else if (skipped) {
                    statusBadge = <span className="px-1.5 py-0.5 rounded bg-amber-950/40 text-amber-400 border border-amber-500/15 font-mono text-[9px]">Skipped</span>;
                  } else {
                    statusBadge = <span className="px-1.5 py-0.5 rounded bg-rose-950/40 text-rose-400 border border-rose-500/15 font-mono text-[9px]">Failed</span>;
                  }

                  return (
                    <div
                      key={i}
                      className={`p-3 rounded-2xl border flex flex-col space-y-2 transition-all relative ${
                        isActive
                          ? "bg-teal-500/10 border-teal-500 text-teal-300 ring-2 ring-teal-500/20"
                          : isDayCovered
                          ? "bg-teal-500/[0.02] border-teal-500/15 text-slate-300"
                          : "bg-darkBg/60 border-darkBorder/40 text-slate-400"
                      }`}
                      title={m.reason}
                    >
                      <div className="flex items-center justify-between">
                        <span className={`flex items-center justify-center w-5 h-5 rounded text-[10px] font-bold font-mono shrink-0 ${
                          isActive
                            ? "bg-teal-500 text-darkBg"
                            : isDayCovered
                            ? "bg-teal-500/20 text-teal-300"
                            : "bg-slate-500/10 text-slate-400"
                        }`}>
                          D{m.day}
                        </span>
                        <div className="flex items-center space-x-1.5">
                          {typeBadge}
                          {isDayCovered && (
                            <span className="text-teal-400 font-bold uppercase tracking-wider text-[8px] bg-teal-500/10 px-1 py-0.5 rounded border border-teal-500/15">
                              Covered
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="min-w-0">
                        <p className={`text-xs font-semibold break-words leading-tight ${
                          isActive ? "text-white animate-pulse" : isDayCovered ? "text-slate-200" : "text-slate-300"
                        }`}>
                          {m.title}
                        </p>
                        <p className="text-[10px] text-slate-400 leading-snug break-words mt-1">
                          {m.reason}
                        </p>
                      </div>

                      <div className="flex justify-between items-center pt-1 border-t border-darkBorder/20">
                        <span className="text-[9px] uppercase font-mono text-slate-500">History Status</span>
                        {statusBadge}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-slate-500 font-mono">Loading syllabus details...</p>
            )}
          </div>
        </div>

        {/* Quit Button */}
        <button
          onClick={resetSession}
          className="mt-6 w-full py-2.5 bg-slate-800 hover:bg-slate-800/80 border border-slate-700/50 hover:border-red-500/30 text-xs font-mono font-bold text-slate-400 hover:text-red-400 rounded-xl transition-all"
        >
          Quit Interview
        </button>
      </div>

      {/* 2. Main Panel: Conversation Thread */}
      <div className="lg:col-span-3 bg-darkCard border border-darkBorder rounded-3xl flex flex-col h-full overflow-hidden shadow-2xl">
        {/* Progress Header */}
        <div className="px-5 py-4 border-b border-darkBorder bg-darkBg/25 flex items-center justify-between text-xs font-mono">
          <div className="flex items-center space-x-2 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse"></span>
            <span>
              Syllabus Topics Covered: <strong className="text-teal-400 font-bold">{daysCovered.length}</strong> of <strong className="text-white">4+</strong>
            </span>
          </div>
          <span className="text-slate-400">
            Current Question: <strong className="text-teal-400 font-bold">{questionCount}</strong>
          </span>
        </div>

        {/* Chat window body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {messages.map((msg, index) => {
            const isInterviewer = msg.sender === "interviewer";
            return (
              <div
                key={index}
                className={`flex w-full items-start space-x-3 text-sm animate-fade-in ${
                  isInterviewer ? "justify-start" : "justify-end flex-row-reverse space-x-reverse"
                }`}
              >
                {/* Logo mark */}
                <div
                  className={`w-8 h-8 rounded-xl border flex items-center justify-center shrink-0 shadow-sm ${
                    isInterviewer
                      ? "bg-teal-500/10 border-teal-500/20 text-teal-400"
                      : "bg-indigo-500/10 border-indigo-500/20 text-indigo-400"
                  }`}
                >
                  {isInterviewer ? <Sparkles className="w-4 h-4" /> : <User className="w-4 h-4" />}
                </div>

                {/* Bubble content */}
                <div className="max-w-[80%] flex flex-col">
                  <span className="text-[10px] font-mono text-slate-500 mb-1 px-1">
                    {isInterviewer ? "AI Technical Interviewer" : candidateName}
                  </span>

                  {/* Dynamic Area Context Badge */}
                  {isInterviewer && msg.focusDay && (() => {
                    const prevInterviewerMsg = messages.slice(0, index).reverse().find(m => m.sender === "interviewer");
                    const isNewDayFocus = prevInterviewerMsg ? prevInterviewerMsg.focusDay !== msg.focusDay : true;
                    if (!isNewDayFocus) return null;

                    const planItem = interviewPlan.find(item => item.day === msg.focusDay);
                    if (!planItem) return null;

                    let labelText = "";
                    let labelClass = "";
                    if (planItem.type === "strength") {
                      labelText = index === 1 
                        ? `🚀 Starting with your strongest area: Day ${msg.focusDay} (${planItem.title})` 
                        : `🚀 Testing your strongest area: Day ${msg.focusDay} (${planItem.title})`;
                      labelClass = "bg-emerald-500/10 text-emerald-400 border-emerald-500/25";
                    } else if (planItem.type === "struggle") {
                      labelText = `⚠️ Exploring a struggle area: Day ${msg.focusDay} (${planItem.title})`;
                      labelClass = "bg-amber-500/10 text-amber-400 border-amber-500/25";
                    } else if (planItem.type === "gap") {
                      labelText = `🔍 Probing a skipped/failed gap: Day ${msg.focusDay} (${planItem.title})`;
                      labelClass = "bg-rose-500/10 text-rose-400 border-rose-500/25";
                    } else {
                      labelText = `📘 Digging into core completed topic: Day ${msg.focusDay} (${planItem.title})`;
                      labelClass = "bg-sky-500/10 text-sky-400 border-sky-500/25";
                    }

                    return (
                      <span className={`text-[9px] uppercase font-mono font-bold px-2 py-0.5 rounded border w-fit mb-1.5 animate-fade-in ${labelClass}`}>
                        {labelText}
                      </span>
                    );
                  })()}

                  <div
                    className={`px-4 py-3 border leading-relaxed break-words shadow-sm ${
                      isInterviewer
                        ? "bg-slate-800/80 border-slate-700/60 text-slate-100 rounded-2xl rounded-tl-none"
                        : "bg-teal-600 border-teal-500/20 text-white rounded-2xl rounded-tr-none"
                    }`}
                  >
                    {msg.text}
                  </div>
                  {isInterviewer && msg.focusDay && (() => {
                    const planItem = interviewPlan.find(item => item.day === msg.focusDay);
                    if (!planItem) return null;
                    const isExpanded = expandedReasons.has(index);
                    return (
                      <div className="mt-1.5 print:hidden">
                        <button
                          type="button"
                          onClick={() => toggleReason(index)}
                          className="flex items-center gap-1.5 text-[10.5px] text-slate-500 hover:text-teal-400 font-mono transition-colors focus:outline-none cursor-pointer animate-fade-in"
                        >
                          <HelpCircle className="w-3.5 h-3.5" />
                          <span>{isExpanded ? "Hide reasoning" : "Why this question?"}</span>
                        </button>
                        {isExpanded && (
                          <div className="mt-1.5 p-2.5 rounded-xl bg-slate-900/60 border border-slate-700/30 text-[11px] text-slate-300 font-mono leading-relaxed animate-fade-in max-w-md">
                            🎯 {planItem.reason}
                          </div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              </div>
            );
          })}

          {/* Thinking / Typing placeholder */}
          {loading && (
            <div className="flex w-full items-start space-x-3 text-sm justify-start animate-fade-in">
              <div className="w-8 h-8 rounded-xl border bg-teal-500/10 border-teal-500/20 text-teal-400 flex items-center justify-center shrink-0">
                <Sparkles className="w-4 h-4 animate-spin" />
              </div>
              <div className="max-w-[80%] flex flex-col">
                <span className="text-[10px] font-mono text-slate-500 mb-1 px-1">
                  AI Technical Interviewer
                </span>
                <div className="px-4 py-3 bg-darkBg/60 border border-darkBorder rounded-2xl text-slate-400 font-mono text-xs flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 bg-teal-400 rounded-full animate-bounce"></span>
                  <span className="w-1.5 h-1.5 bg-teal-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                  <span className="w-1.5 h-1.5 bg-teal-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
                  <span className="pl-1">Analyzing feedback & framing question...</span>
                </div>
              </div>
            </div>
          )}

          {/* Error Message Bubble */}
          {error && (
            <div className="max-w-md mx-auto p-4 border border-red-500/30 bg-red-950/20 rounded-2xl flex items-start space-x-3 text-xs text-red-400">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <div className="flex-1">
                <p className="font-bold uppercase tracking-wider font-mono">Connection Error</p>
                <p className="mt-0.5 leading-relaxed">{error}</p>
                <button
                  onClick={() => submitAnswer(messages[messages.length - 1]?.text)}
                  className="mt-3 flex items-center px-3 py-1.5 bg-red-900/50 hover:bg-red-900 border border-red-500/40 rounded-lg text-[10px] font-bold uppercase font-mono tracking-wider text-red-200 transition-colors"
                >
                  <RefreshCw className="w-3 h-3 mr-1.5" />
                  Retry Submission
                </button>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Panel */}
        <div className="p-4 border-t border-darkBorder bg-darkBg/30">
          <form onSubmit={handleSubmit} className="relative flex items-end space-x-2">
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                rows={2}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
                placeholder={
                  loading
                    ? "Evaluating responses..."
                    : "Type your technical answer here... (Press Enter to submit)"
                }
                className="w-full bg-darkBg/80 border border-darkBorder hover:border-slate-700 focus:border-teal-500 rounded-2xl pl-4 pr-12 py-3.5 text-slate-100 placeholder-slate-500 focus:outline-none transition-all resize-none text-sm leading-relaxed"
              />
              <div className="absolute right-3.5 bottom-3.5 text-[10px] font-mono text-slate-600">
                {input.length} chars
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !input.trim()}
              className={`p-3.5 rounded-2xl flex items-center justify-center shrink-0 transition-all ${
                loading || !input.trim()
                  ? "bg-slate-800 text-slate-600 border border-slate-700/50 cursor-not-allowed"
                  : "bg-teal-600 hover:bg-teal-500 text-white border border-teal-500/30 hover:scale-105 active:scale-95 shadow-md shadow-teal-500/5"
              }`}
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
          <div className="flex justify-between text-[10px] font-mono text-slate-600 mt-2 px-1">
            <span>Press Enter to Submit</span>
            <span>Shift + Enter for new line</span>
          </div>
        </div>
      </div>
    </div>
  );
}
