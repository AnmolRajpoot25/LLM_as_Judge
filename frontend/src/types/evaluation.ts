export interface ModelPricing {
  input_price_per_million: number;
  output_price_per_million: number;
  currency: string;
  estimated: boolean;
  pricing_date?: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  enabled: boolean;
  available: boolean;
  pricing?: ModelPricing;
  description?: string;
}

export interface AnswerItem {
  model_id: string;
  model_name: string;
  provider: string;
  answer: string;
  latency_seconds: number;
  input_tokens?: number | null;
  output_tokens?: number | null;
  estimated_cost?: number | null;
  cost_source?: string | null;
  success: boolean;

  error?: {
    type: string;
    message: string;
    retryable?: boolean;
  };
}

// ============================================================
// CORRECTNESS-ONLY JUDGE
// ============================================================

export type CorrectnessLabel = "correct" | "incorrect";

export interface CandidateJudgeScore {
  correctness: number;
  label: CorrectnessLabel;
}

export interface JudgeResult {
  winner: "A" | "B" | "TIE";

  scores: {
    A: CandidateJudgeScore;
    B: CandidateJudgeScore;
  };

  confidence: number;

  reason: string;
}

// ============================================================
// POSITION SWAP
// ============================================================

export interface PositionSwapInfo {
  executed: boolean;

  consistent: boolean;

  original_winner?: string;

  swapped_winner?: string;

  swap_judge_result?: JudgeResult;

  swap_raw_judge_response?: string;

  swap_latency?: number;

  error?: {
    type?: string;
    message?: string;
    [key: string]: any;
  };
}

// ============================================================
// PAIRWISE COMPARISON
// ============================================================

export interface PairwiseComparison {
  comparison_id: string;

  pair_number?: number;

  model_a: {
    model_id: string;
    name: string;
  };

  model_b: {
    model_id: string;
    name: string;
  };

  winner_model_id?: string | null;

  success: boolean;

  judge_latency?: number;

  judge_result?: JudgeResult;

  raw_judge_response?: string;

  error?: {
    type?: string;
    message?: string;
    [key: string]: any;
  } | null;

  position_swap_check?: PositionSwapInfo | null;
}

// ============================================================
// MODEL RANKING
// ============================================================

export interface ModelRanking {
  rank: number;

  model_id: string;

  model_name: string;

  wins: number;

  losses: number;

  ties: number;

  total_comparisons: number;

  successful_evaluations: number;

  failed_evaluations: number;

  win_rate: number;

  // Kept optional for compatibility with the existing
  // backend/reporting layer. The new judge does not
  // produce a weighted final score.
  average_final_score?: number;

  average_correctness: number;

  // The new correctness-only judge does not provide
  // these criterion scores.
  average_relevance?: number;

  average_completeness?: number;

  average_reasoning?: number;

  average_clarity?: number;
}

// ============================================================
// SESSION METRICS
// ============================================================

export interface SessionMetrics {
  total_session_latency_seconds: number;

  generation?: {
    average_latency_seconds: number;

    successful_models: number;

    failed_models: number;

    total_input_tokens: number;

    total_output_tokens: number;

    total_estimated_cost?: number;

    currency: string;
  };

  evaluation?: {
    total_evaluation_latency_seconds: number;

    average_judge_latency_seconds: number;

    total_comparisons: number;

    successful_evaluations: number;

    failed_evaluations: number;
  };
}

// ============================================================
// EVALUATION REPORT
// ============================================================

export interface EvaluationReport {
  session_id: string;

  mode:
    | "GENERATE_AND_COMPARE"
    | "MANUAL_COMPARE"
    | "SINGLE_GENERATION";

  status:
    | "COMPLETED"
    | "COMPLETED_WITH_WARNINGS"
    | "INSUFFICIENT_SUCCESSFUL_MODELS"
    | "FAILED";

  timestamp: number;

  input: {
    prompt: string;

    system_prompt?: string | null;
  };

  answers: AnswerItem[];

  pairwise_comparisons: PairwiseComparison[];

  rankings: ModelRanking[];

  metrics: SessionMetrics;
}

// ============================================================
// SAVE OPTIONS
// ============================================================

export interface SaveOptions {
  prompt: boolean;

  answers: boolean;

  evaluations: boolean;

  metrics: boolean;

  raw_responses: boolean;
}

// ============================================================
// SAVED SESSION
// ============================================================

export interface SavedSessionSummary {
  session_id: string;

  mode: string;

  status: string;

  prompt_preview: string;

  models: string[];

  rankings_count: number;

  created_at?: string;

  saved_options?: SaveOptions;
}
