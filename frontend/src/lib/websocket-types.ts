export interface WebSocketMessage {
  type: 'message' | 'stream' | 'data' | 'confirm' | 'confirmation_required' | 'classification' | 'agent_status' | 'error' | 'done' | 'confirm_response' | 'ping' | 'pong' | 'function_result' | 'function_error';
  content?: string;
  chunk?: string;
  session_id?: string;
  request_id?: string;
  approved?: boolean;
  data?: unknown;
  agent?: string | { name: string; icon: string };
  action?: string;
  preview?: unknown;
  danger_level?: 'low' | 'medium' | 'high';
  format?: 'code' | 'table' | 'html' | 'diff' | 'json';
  language?: string;
  error?: string;
  message?: string;
  confidence?: number;
  reasoning?: string;
  status?: string;
  function?: string;
  result?: unknown;
}

export interface SendMessageOptions {
  type: 'message' | 'confirm_response' | 'ping';
  content?: string;
  session_id?: string;
  request_id?: string;
  approved?: boolean;
}
