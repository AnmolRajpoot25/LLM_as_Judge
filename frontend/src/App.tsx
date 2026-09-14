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
  const [selectedModelIds, setSelectedModelIds] = useState<string[]>([
    "mock:model-a",
    "mock:model-b",
  ]);

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
    } catch {
      // Token invalid or expired
      localStorage.removeItem("llm_judge_token");
      setAuthToken(null);
      setCurrentUser(null);
    }
  };

  const loadModels = async () => {
    try {
      const models = await fetchAvailableModels();
      setAvailableModels(models);
      if (models.length >= 2 && selectedModelIds.length === 0) {
        setSelectedModelIds([models[0].id, models[1].id]);
      }
    } catch (err) {
      console.warn("Could not connect to backend API yet:", err);
    }
  };

  const loadHistory = async () => {
    setIsHistoryLoading(true);
    try {
      const sessions = await fetchSavedSessions();
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
    setActiveMode("keys"); // Direct user to configure their keys
    setErrorMessage(null);
  };

  const handleLogout = () => {
    localStorage.removeItem("llm_judge_token");
    setAuthToken(null);
    setCurrentUser(null);
    setActiveMode("generate");
  };

  const handleToggleModel = (id: string) => {
    if (selectedModelIds.includes(id)) {
      if (selectedModelIds.length > 2) {
        setSelectedModelIds(selectedModelIds.filter((m) => m !== id));
      } else {
        setErrorMessage("Minimum 2 models required for comparison.");
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
    await saveSessionReport(currentReport.session_id, currentReport, options);
    loadHistory();
  };

  const handleSelectHistorySession = async (sessionId: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const fullSession = await fetchSavedSession(sessionId);
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
              <h2>Mode 1: Generate & Pairwise Compare</h2>
              <p>
                Select between 2 and 4 models. The system concurrently queries all providers,
                measures latency and tokens, and executes exhaustive N*(N-1)/2 pairwise Qwen judge evaluations.
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
            canSubmit={selectedModelIds.length >= 2 && selectedModelIds.length <= 4 && prompt.trim().length > 0}
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
