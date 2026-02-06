export type MessageRole = 'user' | 'assistant' | 'system';

export interface AgentInfo {
  name: string;
  icon: string;
}

export interface MessageData {
  format: 'code' | 'table' | 'html' | 'diff' | 'json';
  content: unknown;
  language?: string;
}

export interface ConfirmRequest {
  request_id: string;
  action: string;
  preview: unknown;
  danger_level: 'low' | 'medium' | 'high';
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  sessionId: string;
  streaming?: boolean;
  agent?: AgentInfo;
  data?: MessageData;
  confirmRequest?: ConfirmRequest;
  metadata?: Record<string, unknown>;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: Message[];
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'error';

export interface Agent {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'inactive' | 'busy';
  capabilities: string[];
  icon?: string;
}

export interface ApiError {
  message: string;
  status: number;
  detail?: string;
}

export interface Settings {
  theme: 'light' | 'dark';
  language: string;
  apiBaseUrl: string;
  wsBaseUrl: string;
  ai_provider: string;
  ai_model: string;
  has_ai_key: boolean;
  meraki_profile: string;
  n8n_enabled: boolean;
  n8n_url?: string;
  has_n8n_key: boolean;
  port: number;
  [key: string]: unknown;
}

export interface MerakiProfile {
  name: string;
  has_api_key: boolean;
  has_org_id: boolean;
  api_key_preview?: string;
}

export interface ProviderInfo {
  name: string;
  has_key: boolean;
}

export interface ValidationResult {
  valid: boolean;
  message: string;
}

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}
