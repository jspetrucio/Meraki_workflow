export interface WebSocketMessage {
  type: 'message' | 'stream' | 'data' | 'confirm' | 'agent_status' | 'error' | 'done' | 'confirm_response' | 'ping' | 'pong';
  content?: string;
  session_id?: string;
  request_id?: string;
  approved?: boolean;
  data?: unknown;
  agent?: {
    name: string;
    icon: string;
  };
  action?: string;
  preview?: unknown;
  danger_level?: 'low' | 'medium' | 'high';
  format?: 'code' | 'table' | 'html' | 'diff' | 'json';
  language?: string;
  error?: string;
  message?: string;
}

export interface SendMessageOptions {
  type: 'message' | 'confirm_response' | 'ping';
  content?: string;
  session_id?: string;
  request_id?: string;
  approved?: boolean;
}
