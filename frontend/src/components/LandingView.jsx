import React, { useState, useEffect, useRef } from "react";
import { useInterview } from "../context/InterviewContext";
import { User, Briefcase, GraduationCap, Award, PlayCircle, Loader2, ChevronDown, Search } from "lucide-react";

export default function LandingView() {
  const { candidates, loadingCandidates, candidatesError, startSession, loading, fetchCandidates } = useInterview();
  const [selectedId, setSelectedId] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleStart = () => {
    if (!selectedId) return;
    startSession(selectedId);
  };

  const selectedCand = candidates.find(c => c.member.id === selectedId);

  const filteredCandidates = candidates.filter(cand => 
    cand.member.name.toLowerCase().includes(search.toLowerCase()) ||
    cand.member.jobRole.toLowerCase().includes(search.toLowerCase())
  );

  if (loadingCandidates) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="w-12 h-12 text-teal-500 animate-spin mb-4" />
        <p className="text-slate-400 font-mono text-sm">Loading candidates database...</p>
      </div>
    );
  }

  if (candidatesError) {
    return (
      <div className="max-w-md mx-auto p-6 bg-red-950/20 border border-red-500/30 rounded-2xl text-center">
        <h3 className="text-lg font-semibold text-red-400 mb-2">Database Error</h3>
        <p className="text-sm text-slate-300 mb-4">{candidatesError}</p>
        <button
          onClick={fetchCandidates}
          className="px-4 py-2 bg-red-900/50 hover:bg-red-900 border border-red-500/40 rounded-xl text-xs font-mono font-bold text-red-200 transition-colors cursor-pointer"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto w-full animate-fade-in text-slate-100">
      <div className="bg-darkCard border border-darkBorder rounded-3xl p-6 md:p-8 shadow-2xl relative">
        {/* Glow accent */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-teal-500/5 rounded-full filter blur-[80px] pointer-events-none"></div>
        <div className="absolute -bottom-10 -left-10 w-80 h-80 bg-indigo-500/5 rounded-full filter blur-[80px] pointer-events-none"></div>

        <div className="text-center mb-8 relative z-10">
          <span className="text-xs uppercase tracking-widest text-teal-400 font-mono bg-teal-500/10 px-3.5 py-1.5 rounded-full border border-teal-500/20">
            Cohort Hackathon 2026
          </span>
          <h2 className="text-3xl font-extrabold text-white mt-4 tracking-tight">
            Personalized AI Interview Panel
          </h2>
          <p className="text-slate-400 text-sm mt-2 max-w-xl mx-auto">
            Experience a tailored, multi-turn technical evaluation. Our agent analyzes your learning signals, checks your struggles, and tests your knowledge gaps dynamically.
          </p>
        </div>

        <div className="space-y-6 relative z-10">
          {/* Custom Searchable Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Select Candidate Profile
            </label>
            <button
              type="button"
              onClick={() => setIsOpen(!isOpen)}
              className="w-full bg-darkBg border border-darkBorder hover:border-slate-700 focus:border-teal-500 rounded-2xl px-4 py-3.5 text-slate-100 flex items-center justify-between focus:outline-none focus:ring-2 focus:ring-teal-500/25 transition-all font-sans text-left"
            >
              <span className={selectedCand ? "text-slate-100" : "text-slate-500"}>
                {selectedCand 
                  ? `${selectedCand.member.name} — ${selectedCand.member.jobRole} (${selectedCand.member.yearsExperience} yrs exp)` 
                  : "Search or select a candidate..."}
              </span>
              <ChevronDown className={`w-5 h-5 text-slate-500 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} />
            </button>

            {/* Dropdown Menu */}
            {isOpen && (
              <div className="absolute z-20 w-full mt-2 bg-darkCard border border-darkBorder rounded-2xl shadow-2xl p-2 animate-fade-in">
                {/* Search Input */}
                <div className="relative mb-2">
                  <Search className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Type to filter by name or job role..."
                    className="w-full bg-darkBg border border-darkBorder focus:border-teal-500 rounded-xl pl-10 pr-4 py-2.5 text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 transition-all font-sans"
                    autoFocus
                  />
                </div>

                {/* Candidate List */}
                <div className="max-h-60 overflow-y-auto space-y-1">
                  {filteredCandidates.length > 0 ? (
                    filteredCandidates.map((cand) => (
                      <button
                        key={cand.member.id}
                        type="button"
                        onClick={() => {
                          setSelectedId(cand.member.id);
                          setIsOpen(false);
                          setSearch("");
                        }}
                        className={`w-full text-left px-3 py-2.5 rounded-xl text-sm flex flex-col transition-colors ${
                          selectedId === cand.member.id
                            ? "bg-teal-500/10 border border-teal-500/20 text-teal-300"
                            : "hover:bg-slate-800/80 text-slate-300 border border-transparent"
                        }`}
                      >
                        <span className="font-bold text-white">{cand.member.name}</span>
                        <span className="text-xs text-slate-400 mt-0.5">
                          {cand.member.jobRole} • {cand.member.yearsExperience} yrs experience
                        </span>
                      </button>
                    ))
                  ) : (
                    <div className="py-4 text-center text-xs text-slate-500 font-mono">
                      No candidates match your search.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Candidate Card Preview */}
          {selectedCand && (
            <div className="border border-darkBorder bg-darkBg/50 rounded-2xl p-5 space-y-4 animate-fade-in">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center space-x-3">
                  <User className="w-5 h-5 text-teal-400 shrink-0" />
                  <div>
                    <p className="text-[10px] uppercase font-mono text-slate-500">Name</p>
                    <p className="text-sm font-medium text-white">{selectedCand.member.name}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <Briefcase className="w-5 h-5 text-teal-400 shrink-0" />
                  <div>
                    <p className="text-[10px] uppercase font-mono text-slate-500">Job Role</p>
                    <p className="text-sm font-medium text-white">{selectedCand.member.jobRole}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <GraduationCap className="w-5 h-5 text-teal-400 shrink-0" />
                  <div>
                    <p className="text-[10px] uppercase font-mono text-slate-500">Education</p>
                    <p className="text-sm font-medium text-white">{selectedCand.member.education}</p>
                  </div>
                </div>
              </div>

              {/* Signals / Stats */}
              <div className="pt-3 border-t border-darkBorder/60">
                <h4 className="text-[11px] uppercase tracking-wider font-mono text-slate-500 mb-3 flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-indigo-400" />
                  Cohort Learning Signals
                </h4>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="bg-darkCard p-3 rounded-xl border border-darkBorder/40">
                    <p className="text-lg font-bold text-teal-400">{selectedCand.signals.commitDays}</p>
                    <p className="text-[9px] uppercase font-mono text-slate-500 mt-0.5">Commit Days</p>
                  </div>
                  <div className="bg-darkCard p-3 rounded-xl border border-darkBorder/40">
                    <p className="text-lg font-bold text-indigo-400">{selectedCand.signals.missionsCompleted}</p>
                    <p className="text-[9px] uppercase font-mono text-slate-500 mt-0.5">Missions Completed</p>
                  </div>
                  <div className="bg-darkCard p-3 rounded-xl border border-darkBorder/40">
                    <p className="text-lg font-bold text-white">{selectedCand.signals.missionsFirstTry}</p>
                    <p className="text-[9px] uppercase font-mono text-slate-500 mt-0.5">First Try Pass</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Description of interview rules */}
          <div className="text-xs text-slate-500 bg-darkBg/20 border border-darkBorder/50 rounded-xl p-4 font-mono leading-relaxed">
            <span className="text-teal-400 font-bold block mb-1">INTERVIEW STANDARDS:</span>
            * Ask a minimum of 8 questions covering at least 4 curriculum topics.<br />
            * Explores your custom learning profile from candidates.json.<br />
            * Strict model-side evaluation with score report and next steps.
          </div>

          {/* Action Button */}
          <button
            onClick={handleStart}
            disabled={!selectedId || loading}
            className={`w-full py-4 rounded-2xl flex items-center justify-center font-bold tracking-wide transition-all shadow-lg ${
              !selectedId
                ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50"
                : loading
                ? "bg-teal-600/30 text-teal-300 border border-teal-500/40 cursor-wait"
                : "bg-teal-600 hover:bg-teal-500 text-white hover:scale-[1.01] hover:shadow-teal-500/10 active:scale-[0.99] border border-teal-500/30"
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin mr-2" />
                Initializing Personal Session...
              </>
            ) : (
              <>
                <PlayCircle className="w-5 h-5 mr-2" />
                Start Technical Interview
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
