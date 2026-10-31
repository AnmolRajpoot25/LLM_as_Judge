import React, { useState, useEffect, useRef } from "react";
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
import { WelcomePage } from "./components/WelcomePage";
import { ThemeToggle } from "./components/ThemeToggle";
import type { AppTheme } from "./components/ThemeToggle";
import {
  Scale,
  Sparkles,
  Edit3,
  History,
  AlertCircle,
  Key,
  LogOut,
  LogIn,
  ChevronDown,
  Check,
} from "lucide-react";

export const App: React.FC = () => {
  // Navigation
  // Authentication State
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(localStorage.getItem("llm_judge_token"));
  const [activeMode, setActiveMode] = useState<"welcome" | "generate" | "manual" | "keys" | "history" | "login">(
    () => localStorage.getItem("llm_judge_token") ? "generate" : "welcome"
  );
  const [isAuthChecking, setIsAuthChecking] = useState<boolean>(() => Boolean(localStorage.getItem("llm_judge_token")));
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);
  const [theme, setTheme] = useState<AppTheme>(() =>
    localStorage.getItem("llm_judge_theme") === "light" ? "light" : "dark"
  );

  // Models catalog
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);
  const [selectedModelIds, setSelectedModelIds] = useState<string[]>([]);

  // Mode 1 State: Generate & Compare
  const [prompt, setPrompt] = useState<string>(
    "Explain how rainbows form in a way a curious 10-year-old would enjoy."
  );
  const [systemPrompt, setSystemPrompt] = useState<string>("");
  const [temperature, setTemperature] = useState<number>(0.7);
  const [maxTokens, setMaxTokens] = useState<number>(1024);
  const [positionSwapGen, setPositionSwapGen] = useState<boolean>(false);

  // Mode 2 State: Manual Compare
  const [manualProblem, setManualProblem] = useState<string>(
    "How would you explain a black hole to someone curious about space?"
  );
  const [manualAnswers, setManualAnswers] = useState<ManualAnswer[]>([
    {
      model_name: "GPT-4.1",
      answer: "A black hole is a place in space where gravity is so strong that nothing—not even light—can escape once it passes the event horizon.",
    },
    {
      model_name: "Claude Sonnet",
      answer: "A black hole is an empty tunnel through space that sucks up everything around it.",
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
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("llm_judge_theme", theme);
  }, [theme]);

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
      setActiveMode("generate");
    } catch {
      // Token invalid or expired
      localStorage.removeItem("llm_judge_token");
      setAuthToken(null);
      setCurrentUser(null);
      setActiveMode("welcome");
    } finally {
      setIsAuthChecking(false);
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
    setIsProfileMenuOpen(false);
    localStorage.removeItem("llm_judge_token");
    setAuthToken(null);
    setCurrentUser(null);
    setSavedSessions([]);
    loadModels(null);
    setActiveMode("welcome");
  };

  useEffect(() => {
    if (!isProfileMenuOpen) return;

    const closeOnOutsideClick = (event: MouseEvent) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target as Node)) {
        setIsProfileMenuOpen(false);
      }
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsProfileMenuOpen(false);
    };

    document.addEventListener("mousedown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [isProfileMenuOpen]);

  const handleToggleModel = (id: string) => {
    if (selectedModelIds.includes(id)) {
      if (selectedModelIds.length > 1) {
        setSelectedModelIds(selectedModelIds.filter((m) => m !== id));
        setErrorMessage(null);
      } else {
        setErrorMessage("Choose at least one model to continue.");
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

  if (isAuthChecking) {
    return (
      <main className="welcome-shell welcome-auth-checking" aria-live="polite">
        Checking your sign-in…
      </main>
    );
  }

  if (!authToken || !currentUser) {
    return (
      <main className="welcome-shell">
        {activeMode === "login" ? (
          <LoginPage
            onLoginSuccess={handleLoginSuccess}
            onCancel={() => setActiveMode("welcome")}
            theme={theme}
            onToggleTheme={() => setTheme((current) => current === "dark" ? "light" : "dark")}
          />
        ) : (
          <WelcomePage
            onNext={() => setActiveMode("login")}
            onSignIn={() => setActiveMode("login")}
            theme={theme}
            onToggleTheme={() => setTheme((current) => current === "dark" ? "light" : "dark")}
          />
        )}
      </main>
    );
  }

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
              Compare AI answers and choose with confidence.
            </p>
          </div>
        </div>

        {/* Navigation and account actions */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
          <ThemeToggle
            theme={theme}
            onToggle={() => setTheme((current) => current === "dark" ? "light" : "dark")}
          />

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

          </nav>

          {currentUser ? (
            <div className="profile-menu-wrap" ref={profileMenuRef}>
              <button
                type="button"
                className="profile-button"
                aria-haspopup="menu"
                aria-expanded={isProfileMenuOpen}
                onClick={() => setIsProfileMenuOpen((open) => !open)}
              >
                <span className="profile-avatar" aria-hidden="true">
                  {currentUser.username.charAt(0).toUpperCase()}
                </span>
                <span className="profile-button-name">@{currentUser.username}</span>
                <ChevronDown size={15} />
              </button>
              {isProfileMenuOpen && (
                <div className="profile-menu" role="menu" aria-label="Account menu">
                  <div className="profile-menu-heading">
                    <span className="profile-avatar profile-avatar-large" aria-hidden="true">
                      {currentUser.username.charAt(0).toUpperCase()}
                    </span>
                    <div>
                      <div className="profile-menu-title">You’re signed in</div>
                      <div className="profile-menu-username">@{currentUser.username}</div>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="profile-menu-item"
                    role="menuitem"
                    onClick={() => {
                      setActiveMode("keys");
                      setErrorMessage(null);
                      setIsProfileMenuOpen(false);
                    }}
                  >
                    <Key size={16} />
                    API Keys
                  </button>
                  <button
                    type="button"
                    className="profile-menu-item"
                    role="menuitem"
                    onClick={() => {
                      setActiveMode("history");
                      loadHistory();
                      setErrorMessage(null);
                      setIsProfileMenuOpen(false);
                    }}
                  >
                    <History size={16} />
                    History
                  </button>
                  <div className="profile-menu-divider" />
                  <button
                    type="button"
                    className="profile-menu-item"
                    role="menuitem"
                    onClick={() => setIsProfileMenuOpen(false)}
                  >
                    <Check size={16} />
                    Stay signed in
                  </button>
                  <button
                    type="button"
                    className="profile-menu-item profile-menu-logout"
                    role="menuitem"
                    onClick={handleLogout}
                  >
                    <LogOut size={16} />
                    Log out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button
              className="btn-secondary"
              onClick={() => setActiveMode("login")}
              style={{ padding: "6px 14px", fontSize: "13px" }}
            >
              <LogIn size={14} color="var(--accent-primary)" />
              Sign in or create an account
            </button>
          )}
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
              <h2>Compare answers from different models</h2>
              <p>
                Try one model on its own or compare up to four answers side by side with the Qwen judge.
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
              <h2>Compare answers you already have</h2>
              <p>
                Add a question and at least two responses. The Qwen judge compares them and helps you see which answer fits best.
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
          theme={theme}
          onToggleTheme={() => setTheme((current) => current === "dark" ? "light" : "dark")}
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
