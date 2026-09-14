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
  input_tokens?: number;
  output_tokens?: number;
  estimated_cost?: number;
  cost_source?: string;
  success: boolean;
  error?: {
    type: string;
    message: string;
    retryable?: boolean;
  };
}

export interface CriteriaScores {
  correctness: number;
  relevance: number;
  completeness: number;
  reasoning: number;
  clarity: number;
  feedback: string;
  final_score: number;
}

export interface JudgeResult {
  winner: "A" | "B" | "TIE";
  scores: {
    A: CriteriaScores;
    B: CriteriaScores;
  };
  confidence: number;
  reason: string;
}

export interface PositionSwapInfo {
  executed: boolean;
  consistent: boolean;
  original_winner?: string;
  swapped_winner?: string;
  swap_judge_result?: JudgeResult;
  error?: any;
}

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
  winner_model_id?: string;
  success: boolean;
  judge_latency?: number;
  judge_result?: JudgeResult;
  raw_judge_response?: string;
  error?: any;
  position_swap_check?: PositionSwapInfo;
}

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
  average_final_score: number;
  average_correctness: number;
  average_relevance: number;
  average_completeness: number;
  average_reasoning: number;
  average_clarity: number;
}

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

export interface EvaluationReport {
  session_id: string;
  mode: "GENERATE_AND_COMPARE" | "MANUAL_COMPARE";
  status: "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "INSUFFICIENT_SUCCESSFUL_MODELS" | "FAILED";
  timestamp: number;
  input: {
    prompt: string;
    system_prompt?: string;
  };
  answers: AnswerItem[];
  pairwise_comparisons: PairwiseComparison[];
  rankings: ModelRanking[];
  metrics: SessionMetrics;
}

export interface SaveOptions {
  prompt: boolean;
  answers: boolean;
  evaluations: boolean;
  metrics: boolean;
  raw_responses: boolean;
}

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
