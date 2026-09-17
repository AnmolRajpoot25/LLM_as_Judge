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
  const [activeTab, setActiveTab] = useState<
    "ranking" | "pairwise" | "answers" | "telemetry"
  >("ranking");

  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const [expandedComparisons, setExpandedComparisons] = useState<
    Record<string, boolean>
  >({});

  const toggleComparison = (id: string) => {
    setExpandedComparisons((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const handleCopy = async (text: string, idx: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(idx);

      setTimeout(() => {
        setCopiedIndex(null);
      }, 2000);
    } catch {
      // Clipboard access can fail in some browser contexts.
    }
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

  const getWinnerName = (
    winnerId: string | null | undefined,
    modelA: { model_id: string; name: string },
    modelB: { model_id: string; name: string }
  ) => {
    if (winnerId === modelA.model_id) return modelA.name;
    if (winnerId === modelB.model_id) return modelB.name;
    return "TIE";
  };

  const getCorrectnessLabel = (
    label: "correct" | "incorrect" | undefined
  ) => {
    if (label === "correct") {
      return {
        text: "Correct",
        icon: <CheckCircle2 size={14} />,
        className: "correct",
      };
    }

    if (label === "incorrect") {
      return {
        text: "Incorrect",
        icon: <AlertTriangle size={14} />,
        className: "incorrect",
      };
    }

    return {
      text: "N/A",
      icon: null,
      className: "",
    };
  };

  return (
    <div style={{ marginTop: "32px" }}>
      {/* Results Header */}
      <div className="results-header">
        <div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              marginBottom: "8px",
            }}
          >
            <h2 style={{ fontSize: "24px", fontWeight: 800 }}>
              Evaluation Results
            </h2>

            <span
              style={{
                fontSize: "12px",
                fontWeight: 700,
                padding: "3px 10px",
                borderRadius: "12px",
                background:
                  report.status === "COMPLETED"
                    ? "rgba(16, 185, 129, 0.15)"
                    : "rgba(245, 158, 11, 0.15)",
                color:
                  report.status === "COMPLETED" ? "#34D399" : "#FBBF24",
                border: `1px solid ${
                  report.status === "COMPLETED"
                    ? "rgba(16, 185, 129, 0.3)"
                    : "rgba(245, 158, 11, 0.3)"
                }`,
              }}
            >
              {report.status}
            </span>
          </div>

          <div
            style={{
              display: "flex",
              gap: "12px",
              alignItems: "center",
              flexWrap: "wrap",
            }}
          >
            <span className="session-badge">
              Session: {report.session_id}
            </span>

            <span
              style={{
                fontSize: "13px",
                color: "var(--text-dim)",
              }}
            >
              Mode:{" "}
              {report.mode === "GENERATE_AND_COMPARE"
                ? "Generate & Compare"
                : report.mode === "SINGLE_GENERATION"
                  ? "Single Model Generation"
                  : "Manual Compare"}
            </span>
          </div>
        </div>

        <button className="btn-secondary" onClick={onOpenSaveModal}>
          <Bookmark size={15} color="var(--accent-primary)" />
          Save Session
        </button>
      </div>

      {/* Top Metrics */}
      <div className="metrics-strip">
        <div className="metric-tile">
          <div
            className="metric-label"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "5px",
            }}
          >
            <Clock size={13} />
            Total Latency
          </div>

          <div className="metric-val">
            {report.metrics.total_session_latency_seconds.toFixed(2)}s
          </div>
        </div>

        <div className="metric-tile">
          <div
            className="metric-label"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "5px",
            }}
          >
            <Zap size={13} />
            Pairwise Comparisons
          </div>

          <div className="metric-val">
            {report.pairwise_comparisons.length} pairs
          </div>
        </div>

        {report.metrics.generation && (
          <div className="metric-tile">
            <div
              className="metric-label"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "5px",
              }}
            >
              <DollarSign size={13} />
              Est. API Cost
            </div>

            <div
              className="metric-val"
              style={{ color: "var(--accent-emerald)" }}
            >
              {report.metrics.generation.total_estimated_cost !== null &&
              report.metrics.generation.total_estimated_cost !== undefined
                ? `$${report.metrics.generation.total_estimated_cost.toFixed(4)}`
                : "Manual / N/A"}
            </div>
          </div>
        )}

        <div className="metric-tile">
          <div
            className="metric-label"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "5px",
            }}
          >
            <Award size={13} />
            Top Ranked Model
          </div>

          <div
            className="metric-val"
            style={{
              color: "var(--accent-amber)",
              fontSize: "18px",
            }}
          >
            {report.rankings[0]?.model_name || "TIE"}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs-header">
        <button
          className={`tab-pill ${
            activeTab === "ranking" ? "active" : ""
          }`}
          onClick={() => setActiveTab("ranking")}
        >
          🏆 Leaderboard
        </button>

        <button
          className={`tab-pill ${
            activeTab === "pairwise" ? "active" : ""
          }`}
          onClick={() => setActiveTab("pairwise")}
        >
          ⚔️ Pairwise Battles ({report.pairwise_comparisons.length})
        </button>

        <button
          className={`tab-pill ${
            activeTab === "answers" ? "active" : ""
          }`}
          onClick={() => setActiveTab("answers")}
        >
          📝 Full Model Answers ({report.answers.length})
        </button>

        <button
          className={`tab-pill ${
            activeTab === "telemetry" ? "active" : ""
          }`}
          onClick={() => setActiveTab("telemetry")}
        >
          📊 Telemetry
        </button>
      </div>

      {/* ========================================================= */}
      {/* TAB 1: RANKING                                           */}
      {/* ========================================================= */}

      {activeTab === "ranking" && (
        <div>
          <h3
            style={{
              fontSize: "18px",
              fontWeight: 800,
              marginBottom: "16px",
            }}
          >
            Model Rankings
          </h3>

          <div className="podium-grid">
            {report.rankings.map((rk) => (
              <div
                key={rk.model_id}
                className={`podium-card ${getRankClass(rk.rank)}`}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <div className="podium-rank-badge">
                    {getRankBadge(rk.rank)}
                  </div>

                  <span
                    style={{
                      fontSize: "12px",
                      fontWeight: 700,
                      padding: "3px 8px",
                      borderRadius: "10px",
                      background: "rgba(255, 255, 255, 0.08)",
                      color: "var(--text-main)",
                    }}
                  >
                    Rank #{rk.rank}
                  </span>
                </div>

                <div className="podium-model-name">
                  {rk.model_name}
                </div>

                <div className="podium-score-row">
                  <span style={{ color: "var(--text-muted)" }}>
                    Win Rate:
                  </span>

                  <span className="podium-score-val">
                    {(rk.win_rate * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="podium-score-row">
                  <span style={{ color: "var(--text-muted)" }}>
                    Correctness:
                  </span>

                  <span className="podium-score-val">
                    {(rk.average_correctness * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="podium-score-row">
                  <span style={{ color: "var(--text-muted)" }}>
                    Record:
                  </span>

                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontWeight: 600,
                    }}
                  >
                    {rk.wins}W - {rk.losses}L - {rk.ties}T
                  </span>
                </div>

                <div className="podium-score-row">
                  <span style={{ color: "var(--text-muted)" }}>
                    Evaluations:
                  </span>

                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontWeight: 600,
                    }}
                  >
                    {rk.successful_evaluations}/
                    {rk.total_comparisons}
                  </span>
                </div>

                <div
                  style={{
                    marginTop: "14px",
                    paddingTop: "12px",
                    borderTop:
                      "1px solid var(--border-subtle)",
                  }}
                >
                  <div
                    style={{
                      fontSize: "11px",
                      fontWeight: 700,
                      color: "var(--text-dim)",
                      textTransform: "uppercase",
                      marginBottom: "8px",
                    }}
                  >
                    Correctness
                  </div>

                  <div
                    style={{
                      height: "7px",
                      background: "rgba(255,255,255,0.08)",
                      borderRadius: "10px",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        width: `${Math.min(
                          100,
                          Math.max(
                            0,
                            rk.average_correctness * 100
                          )
                        )}%`,
                        height: "100%",
                        background:
                          "var(--accent-primary)",
                        borderRadius: "10px",
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* TAB 2: PAIRWISE                                          */}
      {/* ========================================================= */}

      {activeTab === "pairwise" && (
        <div>
          <h3
            style={{
              fontSize: "18px",
              fontWeight: 800,
              marginBottom: "16px",
            }}
          >
            Pairwise Evaluations (
            {report.pairwise_comparisons.length} Comparisons)
          </h3>

          {report.pairwise_comparisons.length === 0 ? (
            <div
              className="glass-card"
              style={{
                padding: "32px",
                textAlign: "center",
                color: "var(--text-muted)",
              }}
            >
              No pairwise comparisons for this run.
            </div>
          ) : (
            report.pairwise_comparisons.map((comp, idx) => {
              const isExpanded =
                expandedComparisons[comp.comparison_id];

              const judgeRes = comp.judge_result;

              const scoreA = judgeRes?.scores?.A;
              const scoreB = judgeRes?.scores?.B;

              const winnerName = getWinnerName(
                comp.winner_model_id,
                comp.model_a,
                comp.model_b
              );

              const labelA = getCorrectnessLabel(
                scoreA?.label
              );

              const labelB = getCorrectnessLabel(
                scoreB?.label
              );

              return (
                <div
                  key={comp.comparison_id}
                  className="comparison-card"
                >
                  {/* Comparison Header */}
                  <div className="comparison-header">
                    <div>
                      <span
                        style={{
                          fontSize: "12px",
                          color: "var(--text-dim)",
                          textTransform: "uppercase",
                          fontWeight: 700,
                        }}
                      >
                        Comparison #{idx + 1}
                      </span>

                      <div
                        style={{
                          fontSize: "16px",
                          fontWeight: 700,
                          marginTop: "2px",
                        }}
                      >
                        {comp.model_a.name}

                        <span
                          style={{
                            color: "var(--text-dim)",
                            margin: "0 6px",
                          }}
                        >
                          vs
                        </span>

                        {comp.model_b.name}
                      </div>
                    </div>

                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "16px",
                      }}
                    >
                      <div className="comparison-winner">
                        <Trophy size={16} />
                        Winner: {winnerName}
                      </div>

                      <button
                        type="button"
                        onClick={() =>
                          toggleComparison(
                            comp.comparison_id
                          )
                        }
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "var(--text-muted)",
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          gap: "4px",
                          fontSize: "13px",
                        }}
                      >
                        {isExpanded ? (
                          <ChevronUp size={16} />
                        ) : (
                          <ChevronDown size={16} />
                        )}

                        {isExpanded ? "Less" : "Details"}
                      </button>
                    </div>
                  </div>

                  {/* Candidate Boxes */}
                  <div className="comparison-candidates">
                    {/* Candidate A */}
                    <div
                      className={`candidate-box ${
                        comp.winner_model_id ===
                        comp.model_a.model_id
                          ? "winner-box"
                          : ""
                      }`}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent:
                            "space-between",
                          alignItems: "center",
                          marginBottom: "12px",
                        }}
                      >
                        <span
                          style={{
                            fontWeight: 700,
                            fontSize: "15px",
                          }}
                        >
                          Candidate A:{" "}
                          {comp.model_a.name}
                        </span>

                        <span
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "5px",
                            fontSize: "12px",
                            fontWeight: 700,
                            color:
                              labelA.className ===
                              "correct"
                                ? "#34D399"
                                : "#FBBF24",
                          }}
                        >
                          {labelA.icon}
                          {labelA.text}
                        </span>
                      </div>

                      <div
                        style={{
                          display: "flex",
                          gap: "8px",
                          flexWrap: "wrap",
                          fontSize: "11px",
                          color: "var(--text-dim)",
                        }}
                      >
                        <span>
                          Correctness:{" "}
                          {scoreA?.correctness === 1
                            ? "1"
                            : "0"}
                        </span>

                        <span>
                          Label:{" "}
                          {scoreA?.label || "N/A"}
                        </span>
                      </div>
                    </div>

                    {/* Candidate B */}
                    <div
                      className={`candidate-box ${
                        comp.winner_model_id ===
                        comp.model_b.model_id
                          ? "winner-box"
                          : ""
                      }`}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent:
                            "space-between",
                          alignItems: "center",
                          marginBottom: "12px",
                        }}
                      >
                        <span
                          style={{
                            fontWeight: 700,
                            fontSize: "15px",
                          }}
                        >
                          Candidate B:{" "}
                          {comp.model_b.name}
                        </span>

                        <span
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "5px",
                            fontSize: "12px",
                            fontWeight: 700,
                            color:
                              labelB.className ===
                              "correct"
                                ? "#34D399"
                                : "#FBBF24",
                          }}
                        >
                          {labelB.icon}
                          {labelB.text}
                        </span>
                      </div>

                      <div
                        style={{
                          display: "flex",
                          gap: "8px",
                          flexWrap: "wrap",
                          fontSize: "11px",
                          color: "var(--text-dim)",
                        }}
                      >
                        <span>
                          Correctness:{" "}
                          {scoreB?.correctness === 1
                            ? "1"
                            : "0"}
                        </span>

                        <span>
                          Label:{" "}
                          {scoreB?.label || "N/A"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Position Swap */}
                  {comp.position_swap_check?.executed && (
                    <div
                      style={{
                        marginTop: "14px",
                        padding: "10px 14px",
                        borderRadius: "var(--radius-sm)",
                        background:
                          comp.position_swap_check
                            .consistent
                            ? "rgba(16, 185, 129, 0.08)"
                            : "rgba(245, 158, 11, 0.08)",
                        border: `1px solid ${
                          comp.position_swap_check
                            .consistent
                            ? "rgba(16, 185, 129, 0.25)"
                            : "rgba(245, 158, 11, 0.25)"
                        }`,
                        fontSize: "12px",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      {comp.position_swap_check.consistent ? (
                        <>
                          <CheckCircle2
                            size={16}
                            color="#34D399"
                          />

                          <span style={{ color: "#34D399" }}>
                            Position-swap check passed:
                            winner remained consistent.
                          </span>
                        </>
                      ) : (
                        <>
                          <AlertTriangle
                            size={16}
                            color="#FBBF24"
                          />

                          <span style={{ color: "#FBBF24" }}>
                            Position-swap warning:
                            swapping A/B changed the
                            outcome.
                          </span>
                        </>
                      )}
                    </div>
                  )}

                  {/* Expanded Details */}
                  {isExpanded && judgeRes && (
                    <div
                      style={{
                        marginTop: "16px",
                        paddingTop: "14px",
                        borderTop:
                          "1px solid var(--border-subtle)",
                        fontSize: "13px",
                      }}
                    >
                      <div style={{ marginBottom: "8px" }}>
                        <strong>Judge Confidence:</strong>{" "}
                        {(judgeRes.confidence * 100).toFixed(
                          0
                        )}
                        %
                      </div>

                      <div style={{ marginBottom: "8px" }}>
                        <strong>Judge Reason:</strong>{" "}
                        {judgeRes.reason}
                      </div>

                      {comp.judge_latency !== undefined && (
                        <div>
                          <strong>Judge Latency:</strong>{" "}
                          {comp.judge_latency.toFixed(3)}s
                        </div>
                      )}

                      {comp.raw_judge_response && (
                        <div style={{ marginTop: "10px" }}>
                          <strong>Raw Judge Response:</strong>

                          <pre
                            className="code-block"
                            style={{
                              marginTop: "8px",
                              whiteSpace: "pre-wrap",
                              wordBreak: "break-word",
                            }}
                          >
                            {comp.raw_judge_response}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {/* ========================================================= */}
      {/* TAB 3: ANSWERS                                           */}
      {/* ========================================================= */}

      {activeTab === "answers" && (
        <div>
          <h3
            style={{
              fontSize: "18px",
              fontWeight: 800,
              marginBottom: "16px",
            }}
          >
            Model Answers ({report.answers.length})
          </h3>

          {report.answers.map((ans, idx) => (
            <div
              key={`${ans.model_id}-${idx}`}
              className="glass-card"
              style={{
                padding: "20px",
                marginBottom: "20px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "12px",
                  gap: "12px",
                  flexWrap: "wrap",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                  }}
                >
                  <span
                    style={{
                      fontSize: "18px",
                      fontWeight: 700,
                    }}
                  >
                    {ans.model_name}
                  </span>

                  <span
                    className={`provider-tag ${ans.provider}`}
                  >
                    {ans.provider}
                  </span>
                </div>

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                  }}
                >
                  <span
                    style={{
                      fontSize: "12px",
                      color: "var(--text-dim)",
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {ans.latency_seconds
                      ? `${ans.latency_seconds.toFixed(2)}s`
                      : ""}

                    {ans.output_tokens
                      ? ` • ${ans.output_tokens} tokens`
                      : ""}

                    {ans.estimated_cost !== null &&
                    ans.estimated_cost !== undefined
                      ? ` • $${ans.estimated_cost.toFixed(
                          4
                        )}`
                      : ""}
                  </span>

                  <button
                    className="btn-secondary"
                    onClick={() =>
                      handleCopy(ans.answer, idx)
                    }
                    style={{
                      padding: "6px 12px",
                      fontSize: "12px",
                    }}
                  >
                    {copiedIndex === idx ? (
                      <Check
                        size={14}
                        color="#34D399"
                      />
                    ) : (
                      <Copy size={14} />
                    )}

                    {copiedIndex === idx
                      ? "Copied"
                      : "Copy"}
                  </button>
                </div>
              </div>

              {ans.success ? (
                <pre
                  className="code-block"
                  style={{
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                  }}
                >
                  {ans.answer}
                </pre>
              ) : (
                <div
                  style={{
                    padding: "14px",
                    borderRadius: "8px",
                    background:
                      "rgba(245, 158, 11, 0.08)",
                    border:
                      "1px solid rgba(245, 158, 11, 0.2)",
                    color: "#FBBF24",
                  }}
                >
                  Generation failed:
                  <br />
                  {ans.error?.message ||
                    "Unknown generation error."}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ========================================================= */}
      {/* TAB 4: TELEMETRY                                         */}
      {/* ========================================================= */}

      {activeTab === "telemetry" && (
        <div>
          <h3
            style={{
              fontSize: "18px",
              fontWeight: 800,
              marginBottom: "16px",
            }}
          >
            Evaluation Telemetry
          </h3>

          <div
            className="glass-card"
            style={{
              padding: "18px",
              marginBottom: "16px",
            }}
          >
            <div className="podium-score-row">
              <span style={{ color: "var(--text-muted)" }}>
                Total Session Latency
              </span>

              <span
                style={{
                  fontFamily: "var(--font-mono)",
                }}
              >
                {report.metrics.total_session_latency_seconds.toFixed(
                  3
                )}
                s
              </span>
            </div>

            {report.metrics.evaluation && (
              <>
                <div className="podium-score-row">
                  <span
                    style={{
                      color: "var(--text-muted)",
                    }}
                  >
                    Total Evaluation Latency
                  </span>

                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {report.metrics.evaluation.total_evaluation_latency_seconds.toFixed(
                      3
                    )}
                    s
                  </span>
                </div>

                <div className="podium-score-row">
                  <span
                    style={{
                      color: "var(--text-muted)",
                    }}
                  >
                    Average Judge Latency
                  </span>

                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {report.metrics.evaluation.average_judge_latency_seconds.toFixed(
                      3
                    )}
                    s
                  </span>
                </div>

                <div className="podium-score-row">
                  <span
                    style={{
                      color: "var(--text-muted)",
                    }}
                  >
                    Successful Evaluations
                  </span>

                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {
                      report.metrics.evaluation
                        .successful_evaluations
                    }
                  </span>
                </div>

                <div className="podium-score-row">
                  <span
                    style={{
                      color: "var(--text-muted)",
                    }}
                  >
                    Failed Evaluations
                  </span>

                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {
                      report.metrics.evaluation
                        .failed_evaluations
                    }
                  </span>
                </div>
              </>
            )}
          </div>

          <pre
            className="code-block"
            style={{
              maxHeight: "450px",
              overflow: "auto",
            }}
          >
            {JSON.stringify(report, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
