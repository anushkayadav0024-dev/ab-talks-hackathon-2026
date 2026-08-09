import React, { createContext, useContext, useState, useEffect } from "react";
import { getCandidates, submitInterviewTurn } from "../api/interview";

const InterviewContext = createContext(null);

export function InterviewProvider({ children }) {
  const [candidates, setCandidates] = useState([]);
  const [loadingCandidates, setLoadingCandidates] = useState(true);
  const [candidatesError, setCandidatesError] = useState(null);

  // Interview state
  const [sessionId, setSessionId] = useState(null);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [done, setDone] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [questionCount, setQuestionCount] = useState(0);
  const [daysCovered, setDaysCovered] = useState([]);
  const [interviewPlan, setInterviewPlan] = useState([]);
  const [focusDay, setFocusDay] = useState(null);

  const fetchCandidates = async () => {
    try {
      setLoadingCandidates(true);
      setCandidatesError(null);
      const data = await getCandidates();
      setCandidates(data.candidates || []);
    } catch (err) {
      console.error(err);
      setCandidatesError(`Failed to fetch candidates: ${err.message || err}. Make sure the backend server is running.`);
    } finally {
      setLoadingCandidates(false);
    }
  };

  // Load candidates on mount
  useEffect(() => {
    fetchCandidates();
  }, []);

  // Start new session
  const startSession = async (candidateId) => {
    try {
      setLoading(true);
      setError(null);

      const sessionUuid = `session-${Math.random().toString(36).substring(2, 11)}-${Date.now()}`;
      setSessionId(sessionUuid);

      // Find full candidate info to keep client-side info
      const candidateInfo = candidates.find(c => c.member.id === candidateId);
      setSelectedCandidate(candidateInfo || { member: { id: candidateId, name: "Candidate" } });

      const payload = {
        sessionId: sessionUuid,
        candidate: {
          candidateId: candidateId
        },
        message: "Hello, I am ready to begin the interview."
      };

      const data = await submitInterviewTurn(payload);

      setMessages([
        { sender: "candidate", text: payload.message },
        { sender: "interviewer", text: data.reply, focusDay: data.focusDay }
      ]);
      setDone(data.done || false);
      setFeedback(data.feedback || null);
      setQuestionCount(data.questionsAsked || 1);
      setDaysCovered(data.daysCovered || []);
      setInterviewPlan(data.plan || []);
      setFocusDay(data.focusDay || null);
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to initialize interview session.");
    } finally {
      setLoading(false);
    }
  };

  // Submit answer
  const submitAnswer = async (answerText) => {
    if (!sessionId) return;

    try {
      setLoading(true);
      setError(null);

      // Add user answer to state immediately
      setMessages(prev => [...prev, { sender: "candidate", text: answerText }]);

      const payload = {
        sessionId: sessionId,
        message: answerText
      };

      console.log(`[Interview] submitting answer / [Interview] sessionId: ${sessionId} / [Interview] endpoint: /api/interview`);
      const data = await submitInterviewTurn(payload);

      setMessages(prev => [...prev, { sender: "interviewer", text: data.reply, focusDay: data.focusDay }]);
      setDone(data.done || false);
      setFeedback(data.feedback || null);
      if (data.questionsAsked !== undefined && data.questionsAsked !== null) {
        setQuestionCount(data.questionsAsked);
      } else {
        setQuestionCount(prev => prev + 1);
      }
      setDaysCovered(data.daysCovered || []);
      setInterviewPlan(data.plan || []);
      setFocusDay(data.focusDay || null);
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to submit answer. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Reset interview session state
  const resetSession = () => {
    setSessionId(null);
    setSelectedCandidate(null);
    setMessages([]);
    setDone(false);
    setFeedback(null);
    setQuestionCount(0);
    setDaysCovered([]);
    setInterviewPlan([]);
    setFocusDay(null);
    setError(null);
  };

  return (
    <InterviewContext.Provider
      value={{
        candidates,
        loadingCandidates,
        candidatesError,
        sessionId,
        selectedCandidate,
        messages,
        loading,
        error,
        done,
        feedback,
        questionCount,
        daysCovered,
        interviewPlan,
        focusDay,
        startSession,
        submitAnswer,
        resetSession,
        fetchCandidates
      }}
    >
      {children}
    </InterviewContext.Provider>
  );
}

export function useInterview() {
  const context = useContext(InterviewContext);
  if (!context) {
    throw new Error("useInterview must be used within an InterviewProvider");
  }
  return context;
}
