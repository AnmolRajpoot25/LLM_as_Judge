

































































































import type {
  ModelInfo,
  EvaluationReport,
  SaveOptions,
  SavedSessionSummary,
} from "../types/evaluation";
import type {
  AuthResponse,
  UserProfile,
  ProviderKeyStatus,
} from "../types/auth";

const API_BASE = "http://localhost:8000/api";

export async function fetchAvailableModels(): Promise<ModelInfo[]> {
  const res = await fetch(`${API_BASE}/models`);
  if (!res.ok) {
    throw new Error(`Failed to fetch models (HTTP ${res.status})`);
  }
  const data = await res.json();
  return data.models || [];
}

export async function executeGenerateCompare(payload: {
  models: string[];
  prompt: string;
  system_prompt?: string;
  generation_config?: {
    temperature: number;
    max_tokens: number;
  };
  position_swap_check?: boolean;
  custom_api_keys?: Record<string, string>;
  authToken?: string | null;
}): Promise<EvaluationReport> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (payload.authToken) {
    headers["Authorization"] = `Bearer ${payload.authToken}`;
  }

  const { authToken, ...bodyData } = payload;
  const res = await fetch(`${API_BASE}/generate-compare`, {
    method: "POST",
    headers,
    body: JSON.stringify(bodyData),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    const message = errData.detail || `Request failed with status ${res.status}`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return res.json();
}

export async function executeManualCompare(payload: {
  problem: string;
  answers: { model_name: string; answer: string }[];
  position_swap_check?: boolean;
}): Promise<EvaluationReport> {
  const res = await fetch(`${API_BASE}/manual-compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    const message = errData.detail || `Request failed with status ${res.status}`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return res.json();
}

export async function saveSessionReport(
  sessionId: string,
  sessionData: EvaluationReport,
  saveOptions: SaveOptions
): Promise<any> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      save_options: saveOptions,
      session_data: sessionData,
    }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to save session");
  }

  return res.json();
}

export async function fetchSavedSession(sessionId: string): Promise<EvaluationReport> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
  if (!res.ok) {
    throw new Error(`Failed to load session ${sessionId}`);
  }
  const data = await res.json();
  return data.data;
}

export async function fetchSavedSessions(): Promise<SavedSessionSummary[]> {
  const res = await fetch(`${API_BASE}/sessions`);
  if (!res.ok) {
    throw new Error("Failed to load session history");
  }
  const data = await res.json();
  return data.data || [];
}

/* Authentication API Calls */
export async function apiRegister(
  username: string,
  email: string,
  password: string
): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Registration failed");
  }
  return res.json();
}

export async function apiLogin(
  username_or_email: string,
  password: string
): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username_or_email, password }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Invalid credentials");
  }
  return res.json();
}

export async function apiGetMe(token: string): Promise<UserProfile> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    throw new Error("Invalid or expired session token");
  }
  const data = await res.json();
  return data.user;
}

/* User API Keys Management API Calls */
export async function apiGetUserKeys(token: string): Promise<Record<string, ProviderKeyStatus>> {
  const res = await fetch(`${API_BASE}/user/keys`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    throw new Error("Failed to retrieve user API keys");
  }
  const data = await res.json();
  return data.keys || {};
}

export async function apiSaveUserKeys(
  token: string,
  keys: Record<string, string | null>
): Promise<any> {
  const res = await fetch(`${API_BASE}/user/keys`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ keys }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to save API keys");
  }
  return res.json();
}

export async function apiTestUserKey(
  token: string,
  provider: string,
  api_key?: string
): Promise<{ success: boolean; provider: string; message: string }> {
  const res = await fetch(`${API_BASE}/user/keys/test`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ provider, api_key }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Connectivity test failed");
  }
  return res.json();
}
