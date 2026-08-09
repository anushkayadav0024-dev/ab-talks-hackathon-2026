import React from "react";
import { InterviewProvider, useInterview } from "./context/InterviewContext";
import Layout from "./components/Layout";
import LandingView from "./components/LandingView";
import InterviewView from "./components/InterviewView";
import ReportView from "./components/ReportView";
import ConfirmationView from "./components/ConfirmationView";

import { Sparkles } from "lucide-react";

function InterviewAppContent() {
  const { sessionId, done, loading, messages, selectedCandidate } = useInterview();
  const [showReport, setShowReport] = React.useState(false);

  // Reset report view toggle when session is cleared
  React.useEffect(() => {
    if (!sessionId) {
      setShowReport(false);
    }
  }, [sessionId]);

  // Show a loading screen on initial start session
  if (loading && messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center space-y-5 max-w-md mx-auto animate-pulse">
        <div className="relative">
          <div className="absolute inset-0 bg-teal-500/20 rounded-full blur-xl animate-ping"></div>
          <div className="p-4 bg-teal-500/10 border border-teal-500/20 rounded-3xl text-teal-400 relative z-10">
            <Sparkles className="w-10 h-10 animate-spin" />
          </div>
        </div>
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-white">Initializing Interview Panel</h3>
          <p className="text-xs text-slate-400 font-mono leading-relaxed">
            Analyzing candidate {selectedCandidate?.member?.name || "profile"}...<br />
            Personalizing syllabus days & mapping technical constraints...
          </p>
        </div>
      </div>
    );
  }

  // Route views based on state
  if (!sessionId) {
    return <LandingView />;
  }

  if (!done) {
    return <InterviewView />;
  }

  if (!showReport) {
    return <ConfirmationView onProceed={() => setShowReport(true)} />;
  }

  return <ReportView />;
}

export default function App() {
  return (
    <InterviewProvider>
      <Layout>
        <InterviewAppContent />
      </Layout>
    </InterviewProvider>
  );
}
