import React, { useState } from "react";
import type { SaveOptions } from "../types/evaluation";
import { X, Check, Bookmark, RefreshCw } from "lucide-react";

interface SaveDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (options: SaveOptions) => Promise<void>;
}

export const SaveDialog: React.FC<SaveDialogProps> = ({
  isOpen,
  onClose,
  onSave,
}) => {
  const [options, setOptions] = useState<SaveOptions>({
    prompt: true,
    answers: true,
    evaluations: true,
    metrics: true,
    raw_responses: false,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  if (!isOpen) return null;

  const handleToggle = (key: keyof SaveOptions) => {
    setOptions((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleConfirmSave = async () => {
    setIsSaving(true);
    try {
      await onSave(options);
      setSavedSuccess(true);
      setTimeout(() => {
        setSavedSuccess(false);
        onClose();
      }, 1500);
    } catch (err) {
      alert("Failed to save session: " + (err as Error).message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Bookmark size={20} color="var(--accent-primary)" />
            <h3 style={{ fontSize: "18px", fontWeight: 700 }}>Selective Session Persistence</h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
          >
            <X size={20} />
          </button>
        </div>

        <p style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "20px" }}>
          Choose which evaluation components you wish to permanently save to SQLite database.
        </p>

        <div style={{ marginBottom: "24px" }}>
          <label className="checkbox-row" onClick={() => handleToggle("prompt")}>
            <input
              type="checkbox"
              checked={options.prompt}
              onChange={() => {}}
            />
            <div>
              <div style={{ fontSize: "14px", fontWeight: 600 }}>Original Prompt / Problem</div>
              <div style={{ fontSize: "12px", color: "var(--text-dim)" }}>Include user prompt and system instruction context</div>
            </div>
          </label>

          <label className="checkbox-row" onClick={() => handleToggle("answers")}>
            <input
              type="checkbox"
              checked={options.answers}
              onChange={() => {}}
            />
            <div>
              <div style={{ fontSize: "14px", fontWeight: 600 }}>Selected Model Answers</div>
              <div style={{ fontSize: "12px", color: "var(--text-dim)" }}>Full text response from each evaluated candidate model</div>
            </div>
          </label>

          <label className="checkbox-row" onClick={() => handleToggle("evaluations")}>
            <input
              type="checkbox"
              checked={options.evaluations}
              onChange={() => {}}
            />
            <div>
              <div style={{ fontSize: "14px", fontWeight: 600 }}>Pairwise Evaluations & Scores</div>
              <div style={{ fontSize: "12px", color: "var(--text-dim)" }}>Qwen judge criterion breakdown, feedback, and confidence</div>
            </div>
          </label>

          <label className="checkbox-row" onClick={() => handleToggle("metrics")}>
            <input
              type="checkbox"
              checked={options.metrics}
              onChange={() => {}}
            />
            <div>
              <div style={{ fontSize: "14px", fontWeight: 600 }}>Cost & Latency Telemetry</div>
              <div style={{ fontSize: "12px", color: "var(--text-dim)" }}>Token counts, estimated API fees, and wall-clock latencies</div>
            </div>
          </label>

          <label className="checkbox-row" onClick={() => handleToggle("raw_responses")}>
            <input
              type="checkbox"
              checked={options.raw_responses}
              onChange={() => {}}
            />
            <div>
              <div style={{ fontSize: "14px", fontWeight: 600 }}>Raw Judge Responses</div>
              <div style={{ fontSize: "12px", color: "var(--text-dim)" }}>Raw unparsed JSON string outputs from Qwen judge</div>
            </div>
          </label>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
          <button className="btn-secondary" onClick={onClose} disabled={isSaving}>
            Cancel
          </button>
          <button
            className="btn-primary"
            onClick={handleConfirmSave}
            disabled={isSaving || savedSuccess}
          >
            {isSaving ? (
              <>
                <RefreshCw className="animate-spin" size={16} />
                Saving...
              </>
            ) : savedSuccess ? (
              <>
                <Check size={16} color="#34D399" />
                Saved to Database!
              </>
            ) : (
              <>
                <Bookmark size={16} />
                Confirm & Save
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
