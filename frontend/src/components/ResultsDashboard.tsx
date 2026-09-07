import React, { useState } from "react";
import type { EvaluationReport } from "../types/evaluation";
import {
  Trophy,
  Award,
  Zap,
  DollarSign,
  Clock,
  Bookmark,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
} from "lucide-react";

interface ResultsDashboardProps {
  report: EvaluationReport;
  onOpenSaveModal: () => void;
}

export const ResultsDashboard: React.FC<ResultsDashboardProps> = ({
  report,
  onOpenSaveModal,
}) => {
  const [activeTab, setActiveTab] = useState<"ranking" | "pairwise" | "answers" | "telemetry">("ranking");
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [expandedComparisons, setExpandedComparisons] = useState<Record<string, boolean>>({});

  const toggleComparison = (id: string) => {
    setExpandedComparisons((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCopy = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const getRankBadge = (rank: number) => {
    if (rank === 1) return "🥇";
    if (rank === 2) return "🥈";
    if (rank === 3) return "🥉";
    return `#${rank}`;
  };

  const getRankClass = (rank: number) => {
    if (rank === 1) return "rank-1";
    if (rank === 2) return "rank-2";
    if (rank === 3) return "rank-3";
    return "";
  };

  return (
    <div style={{ marginTop: "32px" }}>
      {/* Results Header */}
      <div className="results-header">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
            <h2 style={{ fontSize: "24px", fontWeight: 800 }}>Evaluation Results</h2>
            <span style={{
              fontSize: "12px",
              fontWeight: 700,
              padding: "3px 10px",
              borderRadius: "12px",
              background: report.status === "COMPLETED" ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
              color: report.status === "COMPLETED" ? "#34D399" : "#FBBF24",
              border: `1px solid ${report.status === "COMPLETED" ? "rgba(16, 185, 129, 0.3)" : "rgba(245, 158, 11, 0.3)"}`
            }}>
              {report.status}
            </span>
          </div>
          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <span className="session-badge">Session: {report.session_id}</span>
            <span style={{ fontSize: "13px", color: "var(--text-dim)" }}>
              Mode: {report.mode === "GENERATE_AND_COMPARE" ? "Generate & Compare" : "Manual Compare"}
            </span>
          </div>
        </div>

        <button className="btn-secondary" onClick={onOpenSaveModal}>
          <Bookmark size={15} color="var(--accent-primary)" />
          Save Session
        </button>
      </div>

      {/* Top Metrics Strip */}
      <div className="metrics-strip">
        <div className="metric-tile">
          <div className="metric-label" style={{ display: "flex", alignItems: "center", gap: "5px" }}>
            <Clock size={13} /> Total Latency
          </div>
          <div className="metric-val">
            {report.metrics.total_session_latency_seconds}s
          </div>
        </div>

        <div className="metric-tile">
          <div className="metric-label" style={{ display: "flex", alignItems: "center", gap: "5px" }}>
            <Zap size={13} /> Pairwise Comparisons
          </div>
          <div className="metric-val">
            {report.pairwise_comparisons.length} pairs
          </div>
        </div>

        {report.metrics.generation && (
          <div className="metric-tile">
            <div className="metric-label" style={{ display: "flex", alignItems: "center", gap: "5px" }}>
              <DollarSign size={13} /> Est. API Cost
            </div>
            <div className="metric-val" style={{ color: "var(--accent-emerald)" }}>
              {report.metrics.generation.total_estimated_cost !== null && report.metrics.generation.total_estimated_cost !== undefined
                ? `$${report.metrics.generation.total_estimated_cost.toFixed(4)}`
                : "Manual / N/A"}
            </div>
          </div>
        )}

        <div className="metric-tile">
          <div className="metric-label" style={{ display: "flex", alignItems: "center", gap: "5px" }}>
            <Award size={13} /> Top Winner
          </div>
          <div className="metric-val" style={{ color: "var(--accent-amber)", fontSize: "18px" }}>
            {report.rankings[0]?.model_name || "TIE"}
          </div>
        </div>
      </div>

      {/* View Tabs */}
      <div className="tabs-header">
        <button
          className={`tab-pill ${activeTab === "ranking" ? "active" : ""}`}
          onClick={() => setActiveTab("ranking")}
        >
          🏆 Leaderboard & Criteria Breakdown
        </button>
        <button
          className={`tab-pill ${activeTab === "pairwise" ? "active" : ""}`}
          onClick={() => setActiveTab("pairwise")}
        >
          ⚔️ Pairwise Battles ({report.pairwise_comparisons.length})
        </button>
        <button
          className={`tab-pill ${activeTab === "answers" ? "active" : ""}`}
          onClick={() => setActiveTab("answers")}
        >
          📝 Full Model Answers ({report.answers.length})
        </button>
        <button
          className={`tab-pill ${activeTab === "telemetry" ? "active" : ""}`}
          onClick={() => setActiveTab("telemetry")}
        >
          📊 Telemetry & Raw Data
        </button>
      </div>

      {/* TAB 1: RANKING PODIUM & CRITERIA */}
      {activeTab === "ranking" && (
        <div>
          <h3 style={{ fontSize: "18px", fontWeight: 800, marginBottom: "16px" }}>
            Final Model Rankings
          </h3>
          <div className="podium-grid">
            {report.rankings.map((rk) => (
              <div key={rk.model_id} className={`podium-card ${getRankClass(rk.rank)}`}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div className="podium-rank-badge">{getRankBadge(rk.rank)}</div>
                  <span style={{
                    fontSize: "12px",
                    fontWeight: 700,
                    padding: "3px 8px",
                    borderRadius: "10px",
                    background: "rgba(255, 255, 255, 0.08)",
                    color: "var(--text-main)"
                  }}>
                    Rank #{rk.rank}
                  </span>
                </div>

                <div className="podium-model-name">{rk.model_name}</div>

                <div className="podium-score-row">
                  <span style={{ color: "var(--text-muted)" }}>Win Rate:</span>
                  <span className="podium-score-val">{(rk.win_rate * 100).toFixed(0)}%</span>
                </div>
                <div className="podium-score-row">
                  <span style={{ color: "var(--text-muted)" }}>Average Score:</span>
                  <span className="podium-score-val">{rk.average_final_score} / 10</span>
                </div>
                <div className="podium-score-row">
                  <span style={{ color: "var(--text-muted)" }}>Record (W - L - T):</span>
                  <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>
                    {rk.wins}W - {rk.losses}L - {rk.ties}T
                  </span>
                </div>

                {/* Criteria breakdown bars */}
                <div className="criteria-bar-container">
                  <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: "4px" }}>
                    Weighted Criteria (Qwen Evaluator)
                  </div>

                  <div className="criteria-row">
                    <span>Correctness (40%)</span>
                    <span style={{ fontFamily: "var(--font-mono)" }}>{rk.average_correctness}/10</span>
                  </div>
                  <div className="meter-track">
                    <div className="meter-fill" style={{ width: `${(rk.average_correctness / 10) * 100}%` }} />
                  </div>

                  <div className="criteria-row" style={{ marginTop: "4px" }}>
                    <span>Relevance (20%)</span>
                    <span style={{ fontFamily: "var(--font-mono)" }}>{rk.average_relevance}/10</span>
                  </div>
                  <div className="meter-track">
                    <div className="meter-fill" style={{ width: `${(rk.average_relevance / 10) * 100}%` }} />
                  </div>

                  <div className="criteria-row" style={{ marginTop: "4px" }}>
                    <span>Completeness (15%)</span>
                    <span style={{ fontFamily: "var(--font-mono)" }}>{rk.average_completeness}/10</span>
                  </div>
                  <div className="meter-track">
                    <div className="meter-fill" style={{ width: `${(rk.average_completeness / 10) * 100}%` }} />
                  </div>

                  <div className="criteria-row" style={{ marginTop: "4px" }}>
                    <span>Reasoning (15%)</span>
                    <span style={{ fontFamily: "var(--font-mono)" }}>{rk.average_reasoning}/10</span>
                  </div>
                  <div className="meter-track">
                    <div className="meter-fill" style={{ width: `${(rk.average_reasoning / 10) * 100}%` }} />
                  </div>

                  <div className="criteria-row" style={{ marginTop: "4px" }}>
                    <span>Clarity (10%)</span>
                    <span style={{ fontFamily: "var(--font-mono)" }}>{rk.average_clarity}/10</span>
                  </div>
                  <div className="meter-track">
                    <div className="meter-fill" style={{ width: `${(rk.average_clarity / 10) * 100}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 2: PAIRWISE BATTLES */}
      {activeTab === "pairwise" && (
        <div>
          <h3 style={{ fontSize: "18px", fontWeight: 800, marginBottom: "16px" }}>
            Pairwise Evaluation Breakdowns (N*(N-1)/2 Comparisons)
          </h3>

          {report.pairwise_comparisons.map((comp, idx) => {
            const isExpanded = expandedComparisons[comp.comparison_id];
            const judgeRes = comp.judge_result;
            const scoreA = judgeRes?.scores?.A;
            const scoreB = judgeRes?.scores?.B;
            const winnerName = comp.winner_model_id === comp.model_a.model_id
              ? comp.model_a.name
              : comp.winner_model_id === comp.model_b.model_id
              ? comp.model_b.name
              : "TIE";

            return (
              <div key={comp.comparison_id} className="comparison-card">
                <div className="comparison-header">
                  <div>
                    <span style={{ fontSize: "12px", color: "var(--text-dim)", textTransform: "uppercase", fontWeight: 700 }}>
                      Comparison #{idx + 1}
                    </span>
                    <div style={{ fontSize: "16px", fontWeight: 700, marginTop: "2px" }}>
                      {comp.model_a.name} <span style={{ color: "var(--text-dim)", margin: "0 6px" }}>vs</span> {comp.model_b.name}
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                    <div className="comparison-winner">
                      <Trophy size={16} /> Winner: {winnerName}
                    </div>
                    <button
                      type="button"
                      onClick={() => toggleComparison(comp.comparison_id)}
                      style={{
                        background: "transparent",
                        border: "none",
                        color: "var(--text-muted)",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "4px",
                        fontSize: "13px"
                      }}
                    >
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      {isExpanded ? "Less" : "Details"}
                    </button>
                  </div>
                </div>

                <div className="comparison-candidates">
                  {/* Candidate A Box */}
                  <div className={`candidate-box ${comp.winner_model_id === comp.model_a.model_id ? "winner-box" : ""}`}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                      <span style={{ fontWeight: 700, fontSize: "15px" }}>Candidate A: {comp.model_a.name}</span>
                      <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--accent-cyan)" }}>
                        {scoreA?.final_score} / 10
                      </span>
                    </div>
                    <p style={{ fontSize: "13px", color: "var(--text-muted)", fontStyle: "italic", marginBottom: "10px" }}>
                      "{scoreA?.feedback || "Evaluated by Qwen Judge"}"
                    </p>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", fontSize: "11px", color: "var(--text-dim)" }}>
                      <span>Corr: {scoreA?.correctness}</span>
                      <span>Rel: {scoreA?.relevance}</span>
                      <span>Comp: {scoreA?.completeness}</span>
                      <span>Reas: {scoreA?.reasoning}</span>
                      <span>Clar: {scoreA?.clarity}</span>
                    </div>
                  </div>

                  {/* Candidate B Box */}
                  <div className={`candidate-box ${comp.winner_model_id === comp.model_b.model_id ? "winner-box" : ""}`}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                      <span style={{ fontWeight: 700, fontSize: "15px" }}>Candidate B: {comp.model_b.name}</span>
                      <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--accent-cyan)" }}>
                        {scoreB?.final_score} / 10
                      </span>
                    </div>
                    <p style={{ fontSize: "13px", color: "var(--text-muted)", fontStyle: "italic", marginBottom: "10px" }}>
                      "{scoreB?.feedback || "Evaluated by Qwen Judge"}"
                    </p>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", fontSize: "11px", color: "var(--text-dim)" }}>
                      <span>Corr: {scoreB?.correctness}</span>
                      <span>Rel: {scoreB?.relevance}</span>
                      <span>Comp: {scoreB?.completeness}</span>
                      <span>Reas: {scoreB?.reasoning}</span>
                      <span>Clar: {scoreB?.clarity}</span>
                    </div>
                  </div>
                </div>

                {/* Optional Position Swap Results */}
                {comp.position_swap_check?.executed && (
                  <div style={{
                    marginTop: "14px",
                    padding: "10px 14px",
                    borderRadius: "var(--radius-sm)",
                    background: comp.position_swap_check.consistent ? "rgba(16, 185, 129, 0.08)" : "rgba(245, 158, 11, 0.08)",
                    border: `1px solid ${comp.position_swap_check.consistent ? "rgba(16, 185, 129, 0.25)" : "rgba(245, 158, 11, 0.25)"}`,
                    fontSize: "12px",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px"
                  }}>
                    {comp.position_swap_check.consistent ? (
                      <>
                        <CheckCircle2 size={16} color="#34D399" />
                        <span style={{ color: "#34D399" }}>
                          Position Bias Verification Passed: Consistent winner ({winnerName}) in both A vs B and B vs A orders.
                        </span>
                      </>
                    ) : (
                      <>
                        <AlertTriangle size={16} color="#FBBF24" />
                        <span style={{ color: "#FBBF24" }}>
                          Position Bias Warning: Swapping answer order produced differing outcomes.
                        </span>
                      </>
                    )}
                  </div>
                )}

                {/* Expanded Details */}
                {isExpanded && judgeRes && (
                  <div style={{ marginTop: "16px", paddingTop: "14px", borderTop: "1px solid var(--border-subtle)", fontSize: "13px" }}>
                    <div style={{ marginBottom: "6px" }}>
                      <strong>Judge Confidence:</strong> {judgeRes.confidence * 100}%
                    </div>
                    <div>
                      <strong>Overall Comparative Reason:</strong> {judgeRes.reason}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* TAB 3: FULL CANDIDATE ANSWERS */}
      {activeTab === "answers" && (
        <div>
          <h3 style={{ fontSize: "18px", fontWeight: 800, marginBottom: "16px" }}>
            Model Answers ({report.answers.length})
          </h3>
          {report.answers.map((ans, idx) => (
            <div key={idx} className="glass-card" style={{ padding: "20px", marginBottom: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ fontSize: "18px", fontWeight: 700 }}>{ans.model_name}</span>
                  <span className={`provider-tag ${ans.provider}`}>{ans.provider}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <span style={{ fontSize: "12px", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                    {ans.latency_seconds ? `${ans.latency_seconds}s` : ""}
                    {ans.output_tokens ? ` • ${ans.output_tokens} tokens` : ""}
                    {ans.estimated_cost ? ` • $${ans.estimated_cost.toFixed(4)}` : ""}
                  </span>
                  <button
                    className="btn-secondary"
                    onClick={() => handleCopy(ans.answer, idx)}
                    style={{ padding: "6px 12px", fontSize: "12px" }}
                  >
                    {copiedIndex === idx ? <Check size={14} color="#34D399" /> : <Copy size={14} />}
                    {copiedIndex === idx ? "Copied" : "Copy"}
                  </button>
                </div>
              </div>

              <pre className="code-block" style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                {ans.answer}
              </pre>
            </div>
          ))}
        </div>
      )}

      {/* TAB 4: TELEMETRY & RAW DATA */}
      {activeTab === "telemetry" && (
        <div>
          <h3 style={{ fontSize: "18px", fontWeight: 800, marginBottom: "16px" }}>
            Raw Session Telemetry & Metadata
          </h3>
          <pre className="code-block" style={{ maxHeight: "450px" }}>
            {JSON.stringify(report, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
