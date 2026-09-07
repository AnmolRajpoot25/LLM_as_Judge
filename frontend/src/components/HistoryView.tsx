import React from "react";
import type { SavedSessionSummary } from "../types/evaluation";
import { History, Eye, RefreshCw } from "lucide-react";

interface HistoryViewProps {
  sessions: SavedSessionSummary[];
  onSelectSession: (sessionId: string) => void;
  isLoading: boolean;
  onRefresh: () => void;
}

export const HistoryView: React.FC<HistoryViewProps> = ({
  sessions,
  onSelectSession,
  isLoading,
  onRefresh,
}) => {
  return (
    <div className="glass-card" style={{ padding: "28px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <div>
          <h2 style={{ fontSize: "20px", fontWeight: 800 }}>Evaluation Session History</h2>
          <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>
            Review and reload past LLM comparison benchmarks saved in SQLite database.
          </p>
        </div>
        <button className="btn-secondary" onClick={onRefresh} disabled={isLoading}>
          <RefreshCw className={isLoading ? "animate-spin" : ""} size={14} />
          Refresh
        </button>
      </div>

      {sessions.length === 0 ? (
        <div style={{ padding: "40px", textAlign: "center", color: "var(--text-dim)" }}>
          <History size={40} style={{ opacity: 0.4, marginBottom: "12px" }} />
          <p>No saved evaluation sessions found.</p>
          <p style={{ fontSize: "12px" }}>Run a comparison and click "Save Session" to persist it here.</p>
        </div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table className="history-table">
            <thead>
              <tr>
                <th>Mode</th>
                <th>Prompt / Problem</th>
                <th>Models Compared</th>
                <th>Saved At</th>
                <th>Status</th>
                <th style={{ textAlign: "right" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((sess) => (
                <tr key={sess.session_id}>
                  <td>
                    <span style={{
                      fontSize: "11px",
                      fontWeight: 700,
                      padding: "2px 8px",
                      borderRadius: "10px",
                      background: sess.mode === "GENERATE_AND_COMPARE" ? "rgba(99, 102, 241, 0.15)" : "rgba(16, 185, 129, 0.15)",
                      color: sess.mode === "GENERATE_AND_COMPARE" ? "#818CF8" : "#34D399"
                    }}>
                      {sess.mode === "GENERATE_AND_COMPARE" ? "Gen & Compare" : "Manual"}
                    </span>
                  </td>
                  <td style={{ maxWidth: "320px", color: "var(--text-main)" }}>
                    <div style={{ textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                      {sess.prompt_preview}
                    </div>
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                      {sess.models.length > 0 ? (
                        sess.models.map((m, i) => (
                          <span key={i} style={{
                            fontSize: "11px",
                            fontFamily: "var(--font-mono)",
                            background: "rgba(255, 255, 255, 0.05)",
                            padding: "2px 6px",
                            borderRadius: "4px"
                          }}>
                            {m}
                          </span>
                        ))
                      ) : (
                        <span style={{ fontSize: "12px", color: "var(--text-dim)" }}>{sess.rankings_count} models</span>
                      )}
                    </div>
                  </td>
                  <td style={{ fontSize: "12px", color: "var(--text-dim)", whiteSpace: "nowrap" }}>
                    {sess.created_at ? new Date(sess.created_at).toLocaleString() : "Recently"}
                  </td>
                  <td>
                    <span style={{
                      fontSize: "11px",
                      fontWeight: 700,
                      color: sess.status === "COMPLETED" ? "#34D399" : "#FBBF24"
                    }}>
                      ● {sess.status}
                    </span>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <button
                      className="btn-secondary"
                      onClick={() => onSelectSession(sess.session_id)}
                      style={{ padding: "6px 12px", fontSize: "12px" }}
                    >
                      <Eye size={13} />
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
