import React, { useState } from "react";
import { Sliders, Sparkles, ChevronDown, ChevronUp, RefreshCw } from "lucide-react";

interface PromptInputProps {
  prompt: string;
  onChangePrompt: (val: string) => void;
  systemPrompt: string;
  onChangeSystemPrompt: (val: string) => void;
  temperature: number;
  onChangeTemperature: (val: number) => void;
  maxTokens: number;
  onChangeMaxTokens: (val: number) => void;
  positionSwapCheck: boolean;
  onChangePositionSwapCheck: (val: boolean) => void;
  onSubmit: () => void;
  isLoading: boolean;
  canSubmit: boolean;
}

export const PromptInput: React.FC<PromptInputProps> = ({
  prompt,
  onChangePrompt,
  systemPrompt,
  onChangeSystemPrompt,
  temperature,
  onChangeTemperature,
  maxTokens,
  onChangeMaxTokens,
  positionSwapCheck,
  onChangePositionSwapCheck,
  onSubmit,
  isLoading,
  canSubmit,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showSystemPrompt, setShowSystemPrompt] = useState(false);

  return (
    <div className="glass-card prompt-box">
      <div style={{ marginBottom: "16px" }}>
        <label className="form-label">
          Problem / Prompt to Compare
        </label>
        <textarea
          className="textarea-custom"
          placeholder="e.g. Design a scalable URL shortener with high read throughput, or implement an O(log n) algorithm for median of two sorted arrays..."
          value={prompt}
          onChange={(e) => onChangePrompt(e.target.value)}
          rows={5}
        />
      </div>

      {/* Accordion: System Prompt */}
      <div style={{ marginBottom: "16px" }}>
        <button
          type="button"
          onClick={() => setShowSystemPrompt(!showSystemPrompt)}
          style={{
            background: "transparent",
            border: "none",
            color: "var(--text-muted)",
            fontSize: "13px",
            fontWeight: 600,
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            padding: "4px 0"
          }}
        >
          {showSystemPrompt ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          {showSystemPrompt ? "Hide System Instructions" : "+ Add Optional System Prompt"}
        </button>

        {showSystemPrompt && (
          <div style={{ marginTop: "10px" }}>
            <textarea
              className="textarea-custom"
              style={{ minHeight: "80px", fontSize: "13px" }}
              placeholder="System prompt context (e.g. You are a Staff Distributed Systems Engineer. Provide rigorous complexity analysis.)"
              value={systemPrompt}
              onChange={(e) => onChangeSystemPrompt(e.target.value)}
            />
          </div>
        )}
      </div>

      {/* Accordion: Advanced Generation Settings */}
      <div style={{ marginBottom: "20px" }}>
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          style={{
            background: "transparent",
            border: "none",
            color: "var(--text-muted)",
            fontSize: "13px",
            fontWeight: 600,
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            padding: "4px 0"
          }}
        >
          <Sliders size={14} />
          {showAdvanced ? "Hide Advanced Settings" : "Advanced Generation Parameters"}
        </button>

        {showAdvanced && (
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "16px",
            marginTop: "12px",
            padding: "16px",
            background: "var(--bg-input)",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--border-subtle)"
          }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", marginBottom: "6px" }}>
                <span>Temperature</span>
                <span style={{ fontFamily: "var(--font-mono)", color: "var(--accent-cyan)" }}>{temperature}</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.5"
                step="0.05"
                value={temperature}
                onChange={(e) => onChangeTemperature(parseFloat(e.target.value))}
                style={{ width: "100%", accentColor: "var(--accent-primary)" }}
              />
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", marginBottom: "6px" }}>
                <span>Max Output Tokens</span>
                <span style={{ fontFamily: "var(--font-mono)", color: "var(--accent-cyan)" }}>{maxTokens}</span>
              </div>
              <input
                type="range"
                min="256"
                max="4096"
                step="128"
                value={maxTokens}
                onChange={(e) => onChangeMaxTokens(parseInt(e.target.value, 10))}
                style={{ width: "100%", accentColor: "var(--accent-primary)" }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Position Swap Check Checkbox & Action Button */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "16px",
        paddingTop: "16px",
        borderTop: "1px solid var(--border-subtle)"
      }}>
        <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", cursor: "pointer", color: "var(--text-muted)" }}>
          <input
            type="checkbox"
            checked={positionSwapCheck}
            onChange={(e) => onChangePositionSwapCheck(e.target.checked)}
            style={{ accentColor: "var(--accent-primary)", width: "16px", height: "16px" }}
          />
          <span>Mitigate Position Bias (Evaluate A vs B, then B vs A)</span>
        </label>

        <button
          className="btn-primary"
          onClick={onSubmit}
          disabled={!canSubmit || isLoading}
        >
          {isLoading ? (
            <>
              <RefreshCw className="animate-spin" size={18} />
              Generating & Evaluating...
            </>
          ) : (
            <>
              <Sparkles size={18} />
              Run Generation & Comparison
            </>
          )}
        </button>
      </div>
    </div>
  );
};
