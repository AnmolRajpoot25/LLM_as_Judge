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

const rawBase = (import.meta as any).env?.VITE_API_BASE_URL || "http://localhost:8000/api";
export const API_BASE = rawBase.replace(/\/+$/, "");

async function safeFetch(url: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init);
  } catch (err: any) {
    const msg = err?.message || String(err);
    if (msg.includes("Failed to fetch") || msg.includes("NetworkError") || msg.includes("Load failed") || msg.includes("aborted")) {
      throw new Error(
        `Unable to reach API server at ${API_BASE}. If using Render free tier, the instance may be starting up (takes ~30-45s), or ensure VITE_API_BASE_URL is configured in your Vercel project settings.`
      );
    }
    throw err;
  }
}

export async function fetchAvailableModels(authToken?: string | null): Promise<ModelInfo[]> {
  const headers: Record<string, string> = {};
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  const res = await safeFetch(`${API_BASE}/models`, { headers });
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
  const res = await safeFetch(`${API_BASE}/generate-compare`, {
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
  authToken?: string | null;
}): Promise<EvaluationReport> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (payload.authToken) {
    headers["Authorization"] = `Bearer ${payload.authToken}`;
  }

  const { authToken, ...bodyData } = payload;
  const res = await safeFetch(`${API_BASE}/manual-compare`, {
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

export async function saveSessionReport(
  sessionId: string,
  sessionData: EvaluationReport,
  saveOptions: SaveOptions,
  authToken?: string | null
): Promise<any> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  const res = await safeFetch(`${API_BASE}/sessions/${sessionId}/save`, {
    method: "POST",
    headers,
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

export async function fetchSavedSession(sessionId: string, authToken?: string | null): Promise<EvaluationReport> {
  const headers: Record<string, string> = {};
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  const res = await safeFetch(`${API_BASE}/sessions/${sessionId}`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to load session ${sessionId}`);
  }
  const data = await res.json();
  return data.data;
}

export async function fetchSavedSessions(authToken?: string | null): Promise<SavedSessionSummary[]> {
  const headers: Record<string, string> = {};
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  const res = await safeFetch(`${API_BASE}/sessions`, { headers });
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
  const res = await safeFetch(`${API_BASE}/auth/register`, {
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
  const res = await safeFetch(`${API_BASE}/auth/login`, {
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
  const res = await safeFetch(`${API_BASE}/auth/me`, {
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
  const res = await safeFetch(`${API_BASE}/user/keys`, {
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
  const res = await safeFetch(`${API_BASE}/user/keys`, {
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
  const res = await safeFetch(`${API_BASE}/user/keys/test`, {
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
