import React, { useState } from "react";
import { apiLogin, apiRegister } from "../services/api";
import type { UserProfile } from "../types/auth";
import { Lock, Mail, User, Eye, EyeOff, LogIn, UserPlus, Sparkles, RefreshCw, AlertCircle } from "lucide-react";

interface LoginPageProps {
  onLoginSuccess: (user: UserProfile, token: string) => void;
  onCancel?: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess, onCancel }) => {
  const [tab, setTab] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (tab === "login") {
        if (!username.trim() || !password) {
          throw new Error("Username/email and password are required.");
        }
        const res = await apiLogin(username.trim(), password);
        onLoginSuccess(res.user, res.token);
      } else {
        if (!username.trim() || !email.trim() || !password) {
          throw new Error("All fields are required.");
        }
        const res = await apiRegister(username.trim(), email.trim(), password);
        onLoginSuccess(res.user, res.token);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickDemo = async () => {
    setError(null);
    setIsLoading(true);
    try {
      // Auto register or login demo account
      const demoUser = "demo_engineer";
      const demoPass = "evaluator123";
      try {
        const res = await apiLogin(demoUser, demoPass);
        onLoginSuccess(res.user, res.token);
      } catch {
        const res = await apiRegister(demoUser, "engineer@example.com", demoPass);
        onLoginSuccess(res.user, res.token);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "460px", margin: "40px auto" }} className="glass-card">
      <div style={{ padding: "32px" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "24px" }}>
          <div style={{
            width: "48px",
            height: "48px",
            borderRadius: "var(--radius-md)",
            background: "var(--accent-gradient)",
            margin: "0 auto 12px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "var(--shadow-glow)"
          }}>
            <Lock size={22} color="#FFFFFF" />
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: 800 }}>
            {tab === "login" ? "Sign In to LLM-Judge" : "Create Evaluator Account"}
          </h2>
          <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px" }}>
            {tab === "login"
              ? "Access your saved evaluations and personal LLM provider API keys."
              : "Register to configure your personal OpenAI, Anthropic, Gemini, & DeepSeek keys."}
          </p>
        </div>

        {/* Tab Switcher */}
        <div style={{
          display: "flex",
          background: "var(--bg-secondary)",
          padding: "4px",
          borderRadius: "var(--radius-sm)",
          marginBottom: "20px"
        }}>
          <button
            type="button"
            onClick={() => { setTab("login"); setError(null); }}
            style={{
              flex: 1,
              padding: "8px",
              background: tab === "login" ? "var(--accent-primary)" : "transparent",
              color: tab === "login" ? "#FFFFFF" : "var(--text-muted)",
              border: "none",
              borderRadius: "6px",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              transition: "all 0.2s"
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setTab("register"); setError(null); }}
            style={{
              flex: 1,
              padding: "8px",
              background: tab === "register" ? "var(--accent-primary)" : "transparent",
              color: tab === "register" ? "#FFFFFF" : "var(--text-muted)",
              border: "none",
              borderRadius: "6px",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              transition: "all 0.2s"
            }}
          >
            Create Account
          </button>
        </div>

        {/* Error notice */}
        {error && (
          <div style={{
            padding: "12px 14px",
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            borderRadius: "var(--radius-sm)",
            color: "#FCA5A5",
            fontSize: "13px",
            marginBottom: "18px",
            display: "flex",
            alignItems: "center",
            gap: "8px"
          }}>
            <AlertCircle size={16} color="#EF4444" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "16px" }}>
            <label className="form-label" style={{ fontSize: "13px" }}>
              {tab === "login" ? "Username or Email" : "Username"}
            </label>
            <div style={{ position: "relative" }}>
              <input
                type="text"
                className="input-custom"
                style={{ paddingLeft: "36px" }}
                placeholder={tab === "login" ? "Username or your@email.com" : "Choose username"}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
              <User size={16} color="var(--text-dim)" style={{ position: "absolute", left: "12px", top: "12px" }} />
            </div>
          </div>

          {tab === "register" && (
            <div style={{ marginBottom: "16px" }}>
              <label className="form-label" style={{ fontSize: "13px" }}>Email Address</label>
              <div style={{ position: "relative" }}>
                <input
                  type="email"
                  className="input-custom"
                  style={{ paddingLeft: "36px" }}
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
                <Mail size={16} color="var(--text-dim)" style={{ position: "absolute", left: "12px", top: "12px" }} />
              </div>
            </div>
          )}

          <div style={{ marginBottom: "24px" }}>
            <label className="form-label" style={{ fontSize: "13px" }}>Password</label>
            <div style={{ position: "relative" }}>
              <input
                type={showPassword ? "text" : "password"}
                className="input-custom"
                style={{ paddingLeft: "36px", paddingRight: "36px" }}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <Lock size={16} color="var(--text-dim)" style={{ position: "absolute", left: "12px", top: "12px" }} />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: "absolute",
                  right: "10px",
                  top: "10px",
                  background: "transparent",
                  border: "none",
                  color: "var(--text-dim)",
                  cursor: "pointer"
                }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary"
            style={{ width: "100%", justifyContent: "center" }}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <RefreshCw className="animate-spin" size={16} />
                Processing...
              </>
            ) : tab === "login" ? (
              <>
                <LogIn size={16} />
                Sign In
              </>
            ) : (
              <>
                <UserPlus size={16} />
                Register Account
              </>
            )}
          </button>
        </form>

        {/* Quick Demo Access */}
        <div style={{ marginTop: "20px", textAlign: "center", borderTop: "1px solid var(--border-subtle)", paddingTop: "16px" }}>
          <button
            type="button"
            onClick={handleQuickDemo}
            className="btn-secondary"
            style={{ width: "100%", justifyContent: "center", fontSize: "13px" }}
            disabled={isLoading}
          >
            <Sparkles size={14} color="var(--accent-amber)" />
            Quick Demo Login (1-Click)
          </button>
        </div>

        {onCancel && (
          <div style={{ marginTop: "12px", textAlign: "center" }}>
            <button
              type="button"
              onClick={onCancel}
              style={{ background: "transparent", border: "none", color: "var(--text-dim)", fontSize: "12px", cursor: "pointer" }}
            >
              Cancel and return
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
