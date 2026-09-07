import React from "react";
import type { ModelInfo } from "../types/evaluation";
import { Check } from "lucide-react";

interface ModelSelectorProps {
  availableModels: ModelInfo[];
  selectedModelIds: string[];
  onToggleModel: (id: string) => void;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  availableModels,
  selectedModelIds,
  onToggleModel,
}) => {
  const count = selectedModelIds.length;
  const isMax = count >= 4;

  return (
    <div style={{ marginBottom: "28px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <div>
          <h3 style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-main)" }}>
            Select LLMs to Compare
          </h3>
          <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>
            Choose between 2 and 4 models for simultaneous generation and pairwise evaluation.
          </p>
        </div>
        <div style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "6px",
          padding: "6px 14px",
          borderRadius: "20px",
          fontSize: "13px",
          fontWeight: 700,
          background: count >= 2 && count <= 4 ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
          color: count >= 2 && count <= 4 ? "#34D399" : "#F87171",
          border: `1px solid ${count >= 2 && count <= 4 ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"}`
        }}>
          {count} / 4 Selected {count < 2 ? "(Min 2 Required)" : isMax ? "(Max Reached)" : ""}
        </div>
      </div>

      <div className="model-grid">
        {availableModels.map((model) => {
          const isSelected = selectedModelIds.includes(model.id);
          const isDisabled = !isSelected && isMax;

          return (
            <div
              key={model.id}
              className={`model-card ${isSelected ? "selected" : ""}`}
              onClick={() => !isDisabled && onToggleModel(model.id)}
              style={{
                opacity: isDisabled ? 0.45 : 1,
                cursor: isDisabled ? "not-allowed" : "pointer"
              }}
            >
              <div className="model-card-header">
                <span className={`provider-tag ${model.provider}`}>
                  {model.provider}
                </span>
                <div style={{
                  width: "20px",
                  height: "20px",
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: isSelected ? "var(--accent-primary)" : "rgba(255, 255, 255, 0.1)",
                  border: isSelected ? "none" : "1px solid var(--border-subtle)"
                }}>
                  {isSelected && <Check size={13} color="#FFFFFF" strokeWidth={3} />}
                </div>
              </div>

              <div className="model-name">{model.name}</div>
              <div className="model-desc">
                {model.description || "Production LLM model"}
              </div>

              <div className="model-footer">
                <span className="pricing-info">
                  {model.pricing ? (
                    model.pricing.input_price_per_million === 0
                      ? "Free / Local"
                      : `$${model.pricing.input_price_per_million}/M in`
                  ) : (
                    "Standard"
                  )}
                </span>
                <span style={{ color: model.available ? "var(--accent-emerald)" : "var(--text-dim)" }}>
                  {model.available ? "● Ready" : "○ Offline"}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
