import React, { useState, useEffect } from "react";
import type {
  ModelInfo,
  EvaluationReport,
  SaveOptions,
  SavedSessionSummary,
} from "./types/evaluation";
import type { UserProfile } from "./types/auth";
import {
  fetchAvailableModels,
  executeGenerateCompare,
  executeManualCompare,
  saveSessionReport,
  fetchSavedSession,
  fetchSavedSessions,
  apiGetMe,
} from "./services/api";
import { ModelSelector } from "./components/ModelSelector";
import { PromptInput } from "./components/PromptInput";
import { AnswerInput } from "./components/AnswerInput";
import type { ManualAnswer } from "./components/AnswerInput";
import { ResultsDashboard } from "./components/ResultsDashboard";
import { SaveDialog } from "./components/SaveDialog";
import { HistoryView } from "./components/HistoryView";
import { LoginPage } from "./components/LoginPage";
import { ApiKeysPage } from "./components/ApiKeysPage";
import {
  Scale,
  Sparkles,
  Edit3,
  History,
  AlertCircle,
  Key,
  User,
  LogOut,
  LogIn,
} from "lucide-react";

export const App: React.FC = () => {
  // Navigation
  const [activeMode, setActiveMode] = useState<"generate" | "manual" | "keys" | "history" | "login">("generate");

  // Authentication State
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(localStorage.getItem("llm_judge_token"));

  // Models catalog
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);
  const [selectedModelIds, setSelectedModelIds] = useState<string[]>([]);

  // Mode 1 State: Generate & Compare
  const [prompt, setPrompt] = useState<string>(
    "Design a distributed URL shortener system (like bit.ly) supporting 100M new URLs created per month and 10B clicks per month. Provide architecture, data model, and API endpoints."
  );
  const [systemPrompt, setSystemPrompt] = useState<string>("");
  const [temperature, setTemperature] = useState<number>(0.7);
  const [maxTokens, setMaxTokens] = useState<number>(1024);
  const [positionSwapGen, setPositionSwapGen] = useState<boolean>(false);

  // Mode 2 State: Manual Compare
  const [manualProblem, setManualProblem] = useState<string>(
    "Explain the difference between optimistic and pessimistic locking in database transaction management."
  );
  const [manualAnswers, setManualAnswers] = useState<ManualAnswer[]>([
    {
      model_name: "GPT-4.1",
      answer: "Optimistic locking assumes conflict is rare and validates on commit using version/timestamp columns without taking database locks. Pessimistic locking acquires exclusive locks upon reading (SELECT ... FOR UPDATE) preventing concurrent access.",
    },
    {
      model_name: "Claude Sonnet",
      answer: "Optimistic locking delays validation until write time via version checks (good for high read, low collision). Pessimistic locking locks records immediately to avoid collision altogether (good for high write contention).",
    },
  ]);
  const [positionSwapMan, setPositionSwapMan] = useState<boolean>(false);

  // Active Report & Execution state
  const [currentReport, setCurrentReport] = useState<EvaluationReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // History State
  const [savedSessions, setSavedSessions] = useState<SavedSessionSummary[]>([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState<boolean>(false);

  // Save Modal State
  const [isSaveModalOpen, setIsSaveModalOpen] = useState<boolean>(false);

  // Initial Load
  useEffect(() => {
    loadModels();
    if (authToken) {
      validateSession(authToken);
    }
  }, []);

  const validateSession = async (token: string) => {
    try {
      const profile = await apiGetMe(token);
      setCurrentUser(profile);
      loadModels(token);
    } catch {
      // Token invalid or expired
      localStorage.removeItem("llm_judge_token");
      setAuthToken(null);
      setCurrentUser(null);
    }
  };

  const loadModels = async (token?: string | null) => {
    try {
      const activeToken = token !== undefined ? token : authToken;
      const models = await fetchAvailableModels(activeToken);
      setAvailableModels(models);
      setSelectedModelIds((prev) => {
        // Discard any stale or removed model IDs (such as legacy mock models)
        const valid = prev.filter((id) => models.some((m) => m.id === id));
        if (valid.length > 0) return valid;
        // Default to the first ready/available model, or first catalog model
        const readyModel = models.find((m) => m.available) || models[0];
        return readyModel ? [readyModel.id] : [];
      });
    } catch (err) {
      console.warn("Could not connect to backend API yet:", err);
    }
  };

  const loadHistory = async () => {
    setIsHistoryLoading(true);
    try {
      const sessions = await fetchSavedSessions(authToken);
      setSavedSessions(sessions);
    } catch (err) {
      console.error(err);
    } finally {
      setIsHistoryLoading(false);
    }
  };

  const handleLoginSuccess = (user: UserProfile, token: string) => {
    setCurrentUser(user);
    setAuthToken(token);
    localStorage.setItem("llm_judge_token", token);
    fetchSavedSessions(token).then((res) => setSavedSessions(res)).catch(() => {});
    loadModels(token);
    setActiveMode("keys"); // Direct user to configure their keys
    setErrorMessage(null);
  };

  const handleLogout = () => {
    localStorage.removeItem("llm_judge_token");
    setAuthToken(null);
    setCurrentUser(null);
    fetchSavedSessions(null).then((res) => setSavedSessions(res)).catch(() => {});
    loadModels(null);
    setActiveMode("generate");
  };

  const handleToggleModel = (id: string) => {
    if (selectedModelIds.includes(id)) {
      if (selectedModelIds.length > 1) {
        setSelectedModelIds(selectedModelIds.filter((m) => m !== id));
        setErrorMessage(null);
      } else {
        setErrorMessage("Please keep at least 1 model selected.");
      }
    } else {
      if (selectedModelIds.length < 4) {
        setSelectedModelIds([...selectedModelIds, id]);
        setErrorMessage(null);
      }
    }
  };

  const handleRunGenerateCompare = async () => {
    setErrorMessage(null);
    setIsLoading(true);
    setCurrentReport(null);

    try {
      const report = await executeGenerateCompare({
        models: selectedModelIds,
        prompt: prompt.trim(),
        system_prompt: systemPrompt.trim() || undefined,
        generation_config: {
          temperature,
          max_tokens: maxTokens,
        },
        position_swap_check: positionSwapGen,
        authToken: authToken,
      });
      setCurrentReport(report);
    } catch (err) {
      setErrorMessage((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunManualCompare = async () => {
    setErrorMessage(null);
    setIsLoading(true);
    setCurrentReport(null);

    try {
      const report = await executeManualCompare({
        problem: manualProblem.trim(),
        answers: manualAnswers.map((a) => ({
          model_name: a.model_name.trim(),
          answer: a.answer.trim(),
        })),
        position_swap_check: positionSwapMan,
        authToken: authToken,
      });
      setCurrentReport(report);
    } catch (err) {
      setErrorMessage((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveSession = async (options: SaveOptions) => {
    if (!currentReport) return;
    await saveSessionReport(currentReport.session_id, currentReport, options, authToken);
    loadHistory();
  };

  const handleSelectHistorySession = async (sessionId: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const fullSession = await fetchSavedSession(sessionId, authToken);
      setCurrentReport(fullSession);
      setActiveMode(fullSession.mode === "GENERATE_AND_COMPARE" ? "generate" : "manual");
    } catch (err) {
      setErrorMessage((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Top Brand & User Header */}
      <header className="app-header">
        <div className="brand">
          <div className="brand-icon">
            <Scale size={24} color="#FFFFFF" />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span className="brand-title">LLM-Judge</span>
              <span className="brand-badge">Qwen-Powered</span>
            </div>
            <p style={{ fontSize: "12px", color: "var(--text-dim)", marginTop: "2px" }}>
              Production Multi-Model LLM Comparison & Pairwise Evaluation Platform
            </p>
          </div>
        </div>

        {/* User Status Chip & Navigation */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
          {currentUser ? (
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              background: "var(--bg-secondary)",
              padding: "6px 12px",
              borderRadius: "20px",
              border: "1px solid var(--border-subtle)",
              fontSize: "13px"
            }}>
              <span style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                background: "var(--accent-emerald)",
                display: "inline-block"
              }} />
              <User size={14} color="var(--text-dim)" />
              <span style={{ fontWeight: 600, color: "var(--text-main)" }}>@{currentUser.username}</span>
              <button
                type="button"
                onClick={handleLogout}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-dim)",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  padding: "2px",
                  marginLeft: "4px"
                }}
                title="Sign Out"
              >
                <LogOut size={13} />
              </button>
            </div>
          ) : (
            <button
              className="btn-secondary"
              onClick={() => setActiveMode("login")}
              style={{ padding: "6px 14px", fontSize: "13px" }}
            >
              <LogIn size={14} color="var(--accent-primary)" />
              Sign In / Register
            </button>
          )}

          {/* Navigation Tabs */}
          <nav className="nav-tabs">
            <button
              className={`nav-tab-btn ${activeMode === "generate" ? "active" : ""}`}
              onClick={() => {
                setActiveMode("generate");
                loadModels(authToken);
                setErrorMessage(null);
              }}
            >
              <Sparkles size={16} />
              Generate & Compare
            </button>

            <button
              className={`nav-tab-btn ${activeMode === "manual" ? "active" : ""}`}
              onClick={() => {
                setActiveMode("manual");
                setErrorMessage(null);
              }}
            >
              <Edit3 size={16} />
              Compare Existing Answers
            </button>

            <button
              className={`nav-tab-btn ${activeMode === "keys" ? "active" : ""}`}
              onClick={() => {
                setActiveMode("keys");
                setErrorMessage(null);
              }}
            >
              <Key size={16} />
              API Keys
            </button>

            <button
              className={`nav-tab-btn ${activeMode === "history" ? "active" : ""}`}
              onClick={() => {
                setActiveMode("history");
                loadHistory();
                setErrorMessage(null);
              }}
            >
              <History size={16} />
              History
            </button>
          </nav>
        </div>
      </header>

      {/* Error / Alert Banner */}
      {errorMessage && (
        <div style={{
          padding: "16px 20px",
          background: "rgba(239, 68, 68, 0.1)",
          border: "1px solid rgba(239, 68, 68, 0.3)",
          borderRadius: "var(--radius-md)",
          color: "#FCA5A5",
          fontSize: "14px",
          marginBottom: "24px",
          display: "flex",
          alignItems: "center",
          gap: "12px"
        }}>
          <AlertCircle size={20} color="#EF4444" />
          <div style={{ flex: 1 }}>{errorMessage}</div>
        </div>
      )}

      {/* VIEW 1: GENERATE AND COMPARE */}
      {activeMode === "generate" && (
        <div>
          <div className="glass-card mode-banner">
            <div className="mode-info">
              <h2>Mode 1: Generate & Compare (Single or Multi-Model)</h2>
              <p>
                Select 1 model for direct single generation, or 2 to 4 models for simultaneous generation and pairwise Qwen judge evaluations.
                {currentUser ? " Using your configured personal API keys." : " Sign in to use your personal API keys."}
              </p>
            </div>
          </div>

          <ModelSelector
            availableModels={availableModels}
            selectedModelIds={selectedModelIds}
            onToggleModel={handleToggleModel}
          />

          <PromptInput
            prompt={prompt}
            onChangePrompt={setPrompt}
            systemPrompt={systemPrompt}
            onChangeSystemPrompt={setSystemPrompt}
            temperature={temperature}
            onChangeTemperature={setTemperature}
            maxTokens={maxTokens}
            onChangeMaxTokens={setMaxTokens}
            positionSwapCheck={positionSwapGen}
            onChangePositionSwapCheck={setPositionSwapGen}
            onSubmit={handleRunGenerateCompare}
            isLoading={isLoading}
            canSubmit={selectedModelIds.length >= 1 && selectedModelIds.length <= 4 && prompt.trim().length > 0}
            selectedCount={selectedModelIds.length}
          />
        </div>
      )}

      {/* VIEW 2: MANUAL COMPARE */}
      {activeMode === "manual" && (
        <div>
          <div className="glass-card mode-banner">
            <div className="mode-info">
              <h2>Mode 2: Compare Existing Answers</h2>
              <p>
                Provide between 2 and 4 candidate answers manually. The platform bypasses API generation,
                invokes pairwise Qwen evaluation, and computes rigorous win rates and criteria metrics.
              </p>
            </div>
          </div>

          <AnswerInput
            problem={manualProblem}
            onChangeProblem={setManualProblem}
            answers={manualAnswers}
            onChangeAnswers={setManualAnswers}
            positionSwapCheck={positionSwapMan}
            onChangePositionSwapCheck={setPositionSwapMan}
            onSubmit={handleRunManualCompare}
            isLoading={isLoading}
            canSubmit={
              manualProblem.trim().length > 0 &&
              manualAnswers.length >= 2 &&
              manualAnswers.every((a) => a.model_name.trim() && a.answer.trim())
            }
          />
        </div>
      )}

      {/* VIEW 3: USER API KEYS MANAGEMENT */}
      {activeMode === "keys" && (
        <ApiKeysPage
          authToken={authToken}
          onNavigateToLogin={() => setActiveMode("login")}
          onKeysUpdated={() => loadModels(authToken)}
        />
      )}

      {/* VIEW 4: HISTORY */}
      {activeMode === "history" && (
        <HistoryView
          sessions={savedSessions}
          onSelectSession={handleSelectHistorySession}
          isLoading={isHistoryLoading}
          onRefresh={loadHistory}
        />
      )}

      {/* VIEW 5: LOGIN / REGISTER */}
      {activeMode === "login" && (
        <LoginPage
          onLoginSuccess={handleLoginSuccess}
          onCancel={() => setActiveMode("generate")}
        />
      )}

      {/* RESULTS DASHBOARD */}
      {currentReport && (
        <ResultsDashboard
          report={currentReport}
          onOpenSaveModal={() => setIsSaveModalOpen(true)}
        />
      )}

      {/* SAVE MODAL */}
      <SaveDialog
        isOpen={isSaveModalOpen}
        onClose={() => setIsSaveModalOpen(false)}
        onSave={handleSaveSession}
      />
    </div>
  );
};

export default App;
