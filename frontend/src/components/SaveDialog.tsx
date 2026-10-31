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
            <h3 style={{ fontSize: "18px", fontWeight: 700 }}>Choose what to save</h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
          >
            <X size={20} />
          </button>
        </div>

        <p style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "20px" }}>
          Keep the details you’ll want to revisit later. You can choose what goes into this saved session.
        </p>

        <div style={{ marginBottom: "24px" }}>
          <label className="checkbox-row" onClick={() => handleToggle("prompt")}>
            <input
              type="checkbox"
              checked={options.prompt}
              onChange={() => {}}
            />
            <div>
              <div style={{ fontSize: "14px", fontWeight: 600 }}>Your question and guidance</div>
              <div style={{ fontSize: "12px", color: "var(--text-dim)" }}>The prompt and any extra instructions you added</div>
            </div>
          </label>

          <label className="checkbox-row" onClick={() => handleToggle("answers")}>
            <input
              type="checkbox"
              checked={options.answers}
              onChange={() => {}}
            />
            <div>
              <div style={{ fontSize: "14px", fontWeight: 600 }}>Model answers</div>
              <div style={{ fontSize: "12px", color: "var(--text-dim)" }}>The full responses from each model</div>
            </div>
          </label>

          <label className="checkbox-row" onClick={() => handleToggle("evaluations")}>
            <input
              type="checkbox"
              checked={options.evaluations}
              onChange={() => {}}
            />
            <div>
              <div style={{ fontSize: "14px", fontWeight: 600 }}>Comparison and scores</div>
              <div style={{ fontSize: "12px", color: "var(--text-dim)" }}>How the judge scored each answer, with its feedback and confidence</div>
            </div>
          </label>

          <label className="checkbox-row" onClick={() => handleToggle("metrics")}>
            <input
              type="checkbox"
              checked={options.metrics}
              onChange={() => {}}
            />
            <div>
              <div style={{ fontSize: "14px", fontWeight: 600 }}>Usage and timing details</div>
              <div style={{ fontSize: "12px", color: "var(--text-dim)" }}>Token counts, estimated cost, and how long each response took</div>
            </div>
          </label>

          <label className="checkbox-row" onClick={() => handleToggle("raw_responses")}>
            <input
              type="checkbox"
              checked={options.raw_responses}
              onChange={() => {}}
            />
            <div>
              <div style={{ fontSize: "14px", fontWeight: 600 }}>Original judge data</div>
              <div style={{ fontSize: "12px", color: "var(--text-dim)" }}>The judge’s full response, including its structured data</div>
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
                Saving your session…
              </>
            ) : savedSuccess ? (
              <>
                <Check size={16} color="#34D399" />
                Session saved!
              </>
            ) : (
              <>
                <Bookmark size={16} />
                Save session
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
