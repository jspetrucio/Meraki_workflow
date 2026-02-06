import { useEffect, useRef, useCallback, useState } from 'react';
import { useChatStore } from '@/stores/chatStore';
import type { WebSocketMessage, SendMessageOptions } from '@/lib/websocket-types';
import type { ConnectionStatus } from '@/lib/types';

const WS_URL = 'ws://localhost:3141/ws';
const RECONNECT_DELAY = 3000;
const PING_INTERVAL = 30000;

export function useWebSocket() {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const pingTimerRef = useRef<number | null>(null);
  const activeSessionIdRef = useRef<string | null>(null);

  const {
    activeSessionId,
    addMessage,
    appendToLastAssistant,
    setStreaming,
  } = useChatStore();

  // Keep active session ID in ref for WebSocket callbacks
  useEffect(() => {
    activeSessionIdRef.current = activeSessionId;
  }, [activeSessionId]);

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const msg: WebSocketMessage = JSON.parse(event.data);
      const sessionId = activeSessionIdRef.current;

      if (!sessionId) return;

      switch (msg.type) {
        case 'pong':
          // Keepalive response, do nothing
          break;

        case 'stream':
          if (msg.content) {
            appendToLastAssistant(sessionId, msg.content);
          }
          break;

        case 'data':
          addMessage(sessionId, {
            role: 'assistant',
            content: '',
            sessionId,
            data: {
              format: msg.format || 'json',
              content: msg.data,
              language: msg.language,
            },
            agent: msg.agent,
          });
          break;

        case 'confirm':
          addMessage(sessionId, {
            role: 'assistant',
            content: msg.content || 'Confirmation required',
            sessionId,
            confirmRequest: {
              request_id: msg.request_id || '',
              action: msg.action || '',
              preview: msg.preview,
              danger_level: msg.danger_level || 'medium',
            },
            agent: msg.agent,
          });
          break;

        case 'agent_status':
          // Agent status update - could be used to show "Agent X is thinking..."
          break;

        case 'error':
          addMessage(sessionId, {
            role: 'assistant',
            content: `Error: ${msg.error || msg.message || 'Unknown error'}`,
            sessionId,
            agent: msg.agent,
          });
          setStreaming(false);
          break;

        case 'done':
          setStreaming(false);
          break;

        default:
          console.warn('Unknown WebSocket message type:', msg.type);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }, [addMessage, appendToLastAssistant, setStreaming]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setStatus('connecting');

    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setStatus('connected');
        wsRef.current = ws;

        // Start ping/pong keepalive
        if (pingTimerRef.current) {
          clearInterval(pingTimerRef.current);
        }
        pingTimerRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, PING_INTERVAL);
      };

      ws.onmessage = handleMessage;

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatus('error');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setStatus('disconnected');
        wsRef.current = null;

        if (pingTimerRef.current) {
          clearInterval(pingTimerRef.current);
          pingTimerRef.current = null;
        }

        // Auto-reconnect after delay
        if (reconnectTimerRef.current) {
          clearTimeout(reconnectTimerRef.current);
        }
        reconnectTimerRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, RECONNECT_DELAY);
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setStatus('error');
    }
  }, [handleMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    if (pingTimerRef.current) {
      clearInterval(pingTimerRef.current);
      pingTimerRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setStatus('disconnected');
  }, []);

  const send = useCallback((message: SendMessageOptions) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    status,
    send,
    connect,
    disconnect,
  };
}
