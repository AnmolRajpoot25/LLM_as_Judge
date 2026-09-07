import React from "react";
import { Plus, Trash2, Scale, RefreshCw } from "lucide-react";

export interface ManualAnswer {
  model_name: string;
  answer: string;
}

interface AnswerInputProps {
  problem: string;
  onChangeProblem: (val: string) => void;
  answers: ManualAnswer[];
  onChangeAnswers: (answers: ManualAnswer[]) => void;
  positionSwapCheck: boolean;
  onChangePositionSwapCheck: (val: boolean) => void;
  onSubmit: () => void;
  isLoading: boolean;
  canSubmit: boolean;
}

export const AnswerInput: React.FC<AnswerInputProps> = ({
  problem,
  onChangeProblem,
  answers,
  onChangeAnswers,
  positionSwapCheck,
  onChangePositionSwapCheck,
  onSubmit,
  isLoading,
  canSubmit,
}) => {
  const handleAddAnswer = () => {
    if (answers.length < 4) {
      onChangeAnswers([
        ...answers,
        { model_name: `Model ${answers.length + 1}`, answer: "" },
      ]);
    }
  };

  const handleRemoveAnswer = (index: number) => {
    if (answers.length > 2) {
      const updated = answers.filter((_, i) => i !== index);
      onChangeAnswers(updated);
    }
  };

  const handleUpdate = (index: number, field: "model_name" | "answer", val: string) => {
    const updated = [...answers];
    updated[index][field] = val;
    onChangeAnswers(updated);
  };

  return (
    <div className="glass-card prompt-box">
      <div style={{ marginBottom: "24px" }}>
        <label className="form-label">
          Problem / Ground Truth Context
        </label>
        <textarea
          className="textarea-custom"
          placeholder="Enter the problem statement, prompt, or question that both candidate answers address..."
          value={problem}
          onChange={(e) => onChangeProblem(e.target.value)}
          rows={4}
        />
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <h3 style={{ fontSize: "16px", fontWeight: 700 }}>
          Candidate Model Answers ({answers.length} / 4)
        </h3>
        {answers.length < 4 && (
          <button
            type="button"
            className="btn-secondary"
            onClick={handleAddAnswer}
            style={{ padding: "6px 14px", fontSize: "12px" }}
          >
            <Plus size={14} />
            Add Candidate Answer ({answers.length + 1}/4)
          </button>
        )}
      </div>

      {answers.map((ans, idx) => (
        <div key={idx} className="manual-answer-card">
          <div className="manual-header">
            <div style={{ display: "flex", alignItems: "center", gap: "10px", flex: 1, marginRight: "12px" }}>
              <span style={{
                width: "24px",
                height: "24px",
                borderRadius: "50%",
                background: "var(--accent-primary)",
                color: "#FFFFFF",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "12px",
                fontWeight: 700
              }}>
                {idx + 1}
              </span>
              <input
                type="text"
                className="input-custom"
                style={{ maxWidth: "240px", fontWeight: 600 }}
                placeholder="Model Name (e.g. GPT-4o, Claude)"
                value={ans.model_name}
                onChange={(e) => handleUpdate(idx, "model_name", e.target.value)}
              />
            </div>
            {answers.length > 2 && (
              <button
                type="button"
                onClick={() => handleRemoveAnswer(idx)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--accent-rose)",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  padding: "4px"
                }}
                title="Remove Candidate"
              >
                <Trash2 size={16} />
              </button>
            )}
          </div>

          <textarea
            className="textarea-custom"
            placeholder={`Enter or paste full answer from ${ans.model_name || `Model ${idx + 1}`}...`}
            value={ans.answer}
            onChange={(e) => handleUpdate(idx, "answer", e.target.value)}
            rows={5}
          />
        </div>
      ))}

      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "16px",
        paddingTop: "16px",
        borderTop: "1px solid var(--border-subtle)",
        marginTop: "16px"
      }}>
        <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", cursor: "pointer", color: "var(--text-muted)" }}>
          <input
            type="checkbox"
            checked={positionSwapCheck}
            onChange={(e) => onChangePositionSwapCheck(e.target.checked)}
            style={{ accentColor: "var(--accent-primary)", width: "16px", height: "16px" }}
          />
          <span>Mitigate Position Bias (Swap order & verify consistency)</span>
        </label>

        <button
          className="btn-primary"
          onClick={onSubmit}
          disabled={!canSubmit || isLoading}
        >
          {isLoading ? (
            <>
              <RefreshCw className="animate-spin" size={18} />
              Evaluating Answers...
            </>
          ) : (
            <>
              <Scale size={18} />
              Run Pairwise Judge Evaluation
            </>
          )}
        </button>
      </div>
    </div>
  );
};
