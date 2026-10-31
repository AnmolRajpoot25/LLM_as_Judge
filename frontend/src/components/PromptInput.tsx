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
  selectedCount?: number;
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
  selectedCount = 2,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showSystemPrompt, setShowSystemPrompt] = useState(false);

  return (
    <div className="glass-card prompt-box">
      <div style={{ marginBottom: "16px" }}>
        <label className="form-label">
          What would you like the models to answer?
        </label>
        <textarea
          className="textarea-custom"
          placeholder="Ask a question, describe a task, or paste a prompt…"
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
          {showSystemPrompt ? "Hide extra guidance" : "+ Add optional guidance"}
        </button>

        {showSystemPrompt && (
          <div style={{ marginTop: "10px" }}>
            <textarea
              className="textarea-custom"
              style={{ minHeight: "80px", fontSize: "13px" }}
              placeholder="For example: Keep the explanation friendly and use a simple example."
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
          {showAdvanced ? "Hide settings" : "Fine-tune the response"}
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
                <span>Creativity</span>
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
                <span>Answer length</span>
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
        {selectedCount > 1 ? (
          <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", cursor: "pointer", color: "var(--text-muted)" }}>
            <input
              type="checkbox"
              checked={positionSwapCheck}
              onChange={(e) => onChangePositionSwapCheck(e.target.checked)}
              style={{ accentColor: "var(--accent-primary)", width: "16px", height: "16px" }}
            />
            <span>Check whether answer order changes the result</span>
          </label>
        ) : (
          <span style={{ fontSize: "13px", color: "var(--text-dim)" }}>
            One model is selected, so it will answer without a comparison.
          </span>
        )}

        <button
          className="btn-primary"
          onClick={onSubmit}
          disabled={!canSubmit || isLoading}
        >
          {isLoading ? (
            <>
              <RefreshCw className="animate-spin" size={18} />
              {selectedCount === 1 ? "Putting an answer together…" : "Comparing the answers…"}
            </>
          ) : (
            <>
              <Sparkles size={18} />
              {selectedCount === 1 ? "Get an answer" : "Get answers & compare"}
            </>
          )}
        </button>
      </div>
    </div>
  );
};
