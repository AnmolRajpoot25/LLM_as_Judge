import React, { useState, useEffect } from "react";
import { apiGetUserKeys, apiSaveUserKeys, apiTestUserKey } from "../services/api";
import type { ProviderKeyStatus } from "../types/auth";
import {
  Key,
  ShieldCheck,
  Check,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  Save,
  CheckCircle2,
} from "lucide-react";

interface ApiKeysPageProps {
  authToken: string | null;
  onNavigateToLogin: () => void;
}

interface ProviderConfigMeta {
  id: string;
  name: string;
  placeholder: string;
  docsUrl: string;
  description: string;
}

const PROVIDERS: ProviderConfigMeta[] = [
  {
    id: "openai",
    name: "OpenAI",
    placeholder: "sk-proj-...",
    docsUrl: "https://platform.openai.com/api-keys",
    description: "Powers GPT-4o, GPT-4o Mini, and GPT-4.1 comparisons.",
  },
  {
    id: "anthropic",
    name: "Anthropic Claude",
    placeholder: "sk-ant-api03-...",
    docsUrl: "https://console.anthropic.com/settings/keys",
    description: "Powers Claude 3.5 Sonnet and Claude 3.5 Haiku comparisons.",
  },
  {
    id: "gemini",
    name: "Google Gemini",
    placeholder: "AIzaSy...",
    docsUrl: "https://aistudio.google.com/app/apikey",
    description: "Powers Gemini 1.5 Pro, Flash, and 2.0 Flash comparisons.",
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    placeholder: "sk-...",
    docsUrl: "https://platform.deepseek.com/api_keys",
    description: "Powers DeepSeek V3 and DeepSeek R1 reasoning models.",
  },
  {
    id: "mistral",
    name: "Mistral AI",
    placeholder: "...",
    docsUrl: "https://console.mistral.ai/api-keys/",
    description: "Powers Mistral Large and Mistral Small comparisons.",
  },
  {
    id: "ollama",
    name: "Ollama (Local URL)",
    placeholder: "http://localhost:11434",
    docsUrl: "https://ollama.ai",
    description: "Local inference URL for Qwen, Llama, and DeepSeek R1 without API charges.",
  },
];

export const ApiKeysPage: React.FC<ApiKeysPageProps> = ({
  authToken,
  onNavigateToLogin,
}) => {
  const [keysStatus, setKeysStatus] = useState<Record<string, ProviderKeyStatus>>({});
  const [inputValues, setInputValues] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({});
  const [saveSuccessMap, setSaveSuccessMap] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (authToken) {
      loadKeys();
    }
  }, [authToken]);

  const loadKeys = async () => {
    if (!authToken) return;
    setIsLoading(true);
    try {
      const keys = await apiGetUserKeys(authToken);
      setKeysStatus(keys);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (provider: string, val: string) => {
    setInputValues((prev) => ({ ...prev, [provider]: val }));
  };

  const handleSaveSingle = async (provider: string) => {
    if (!authToken) return;
    const val = inputValues[provider];
    if (val === undefined) return;

    try {
      await apiSaveUserKeys(authToken, { [provider]: val });
      setSaveSuccessMap((prev) => ({ ...prev, [provider]: true }));
      setTimeout(() => {
        setSaveSuccessMap((prev) => ({ ...prev, [provider]: false }));
      }, 2000);
      loadKeys();
    } catch (err) {
      alert("Failed to save key: " + (err as Error).message);
    }
  };

  const handleTestKey = async (provider: string) => {
    if (!authToken) return;
    setTestingProvider(provider);
    const keyToTest = inputValues[provider];

    try {
      const result = await apiTestUserKey(authToken, provider, keyToTest || undefined);
      setTestResults((prev) => ({
        ...prev,
        [provider]: { success: result.success, message: result.message },
      }));
    } catch (err) {
      setTestResults((prev) => ({
        ...prev,
        [provider]: { success: false, message: (err as Error).message },
      }));
    } finally {
      setTestingProvider(null);
    }
  };

  if (!authToken) {
    return (
      <div className="glass-card" style={{ maxWidth: "560px", margin: "40px auto", padding: "36px", textAlign: "center" }}>
        <ShieldCheck size={48} color="var(--accent-primary)" style={{ margin: "0 auto 16px" }} />
        <h2 style={{ fontSize: "22px", fontWeight: 800, marginBottom: "8px" }}>
          Authentication Required
        </h2>
        <p style={{ fontSize: "14px", color: "var(--text-muted)", marginBottom: "24px" }}>
          Please sign in to securely save and manage your personal LLM provider API keys.
        </p>
        <button className="btn-primary" onClick={onNavigateToLogin}>
          Sign In / Register
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="glass-card mode-banner">
        <div className="mode-info">
          <h2>Personal LLM Provider API Keys</h2>
          <p>
            Configure your own provider keys. When you run benchmarks in <strong>Generate & Compare</strong>,
            your personal credentials will be dynamically called to generate answers.
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {isLoading && <RefreshCw size={15} className="animate-spin" color="var(--accent-primary)" />}
          <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--accent-emerald)", fontSize: "13px", fontWeight: 600 }}>
            <ShieldCheck size={18} />
            <span>Encrypted Storage</span>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "20px" }}>
        {PROVIDERS.map((prov) => {
          const status = keysStatus[prov.id];
          const isSaved = status?.is_set;
          const masked = status?.masked_key;
          const currentInput = inputValues[prov.id] ?? "";
          const isTesting = testingProvider === prov.id;
          const testRes = testResults[prov.id];
          const isSavedSuccess = saveSuccessMap[prov.id];

          return (
            <div key={prov.id} className="glass-card" style={{ padding: "24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <Key size={18} color="var(--accent-primary)" />
                  <h3 style={{ fontSize: "16px", fontWeight: 700 }}>{prov.name}</h3>
                </div>
                <span style={{
                  fontSize: "11px",
                  fontWeight: 700,
                  padding: "3px 8px",
                  borderRadius: "10px",
                  background: isSaved ? "rgba(16, 185, 129, 0.15)" : "rgba(255, 255, 255, 0.05)",
                  color: isSaved ? "#34D399" : "var(--text-dim)",
                  border: `1px solid ${isSaved ? "rgba(16, 185, 129, 0.3)" : "var(--border-subtle)"}`
                }}>
                  {isSaved ? "● Configured" : "○ Not Set"}
                </span>
              </div>

              <p style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "16px" }}>
                {prov.description}
              </p>

              {isSaved && masked && (
                <div style={{
                  marginBottom: "12px",
                  padding: "8px 12px",
                  background: "rgba(0, 0, 0, 0.3)",
                  borderRadius: "var(--radius-sm)",
                  fontSize: "12px",
                  fontFamily: "var(--font-mono)",
                  color: "var(--text-muted)",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center"
                }}>
                  <span>Saved Key: <strong>{masked}</strong></span>
                  <span style={{ fontSize: "10px", color: "var(--accent-emerald)" }}>Active</span>
                </div>
              )}

              <div style={{ marginBottom: "14px" }}>
                <input
                  type="password"
                  className="input-custom"
                  placeholder={isSaved ? "Enter new key to replace..." : prov.placeholder}
                  value={currentInput}
                  onChange={(e) => handleInputChange(prov.id, e.target.value)}
                />
              </div>

              {/* Test Result Banner */}
              {testRes && (
                <div style={{
                  padding: "8px 12px",
                  borderRadius: "var(--radius-sm)",
                  background: testRes.success ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
                  border: `1px solid ${testRes.success ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
                  color: testRes.success ? "#34D399" : "#F87171",
                  fontSize: "12px",
                  marginBottom: "14px",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px"
                }}>
                  {testRes.success ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                  <span>{testRes.message}</span>
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: "12px", borderTop: "1px solid var(--border-subtle)" }}>
                <a
                  href={prov.docsUrl}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    fontSize: "12px",
                    color: "var(--text-dim)",
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                    textDecoration: "none"
                  }}
                >
                  Get Key <ExternalLink size={11} />
                </a>

                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => handleTestKey(prov.id)}
                    disabled={isTesting || (!isSaved && !currentInput)}
                    style={{ padding: "6px 12px", fontSize: "12px" }}
                  >
                    {isTesting ? <RefreshCw className="animate-spin" size={13} /> : "Test"}
                  </button>

                  <button
                    type="button"
                    className="btn-primary"
                    onClick={() => handleSaveSingle(prov.id)}
                    disabled={!currentInput}
                    style={{ padding: "6px 14px", fontSize: "12px" }}
                  >
                    {isSavedSuccess ? (
                      <>
                        <Check size={13} color="#34D399" />
                        Saved!
                      </>
                    ) : (
                      <>
                        <Save size={13} />
                        Save
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
