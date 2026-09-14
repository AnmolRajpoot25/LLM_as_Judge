export interface UserProfile {
  id: string;
  username: string;
  email: string;
  created_at?: string;
}

export interface AuthResponse {
  success: boolean;
  user: UserProfile;
  token: string;
}

export interface ProviderKeyStatus {
  provider: string;
  is_set: boolean;
  masked_key: string | null;
  updated_at?: string | null;
}

export interface UserKeysResponse {
  success: boolean;
  keys: Record<string, ProviderKeyStatus>;
}
