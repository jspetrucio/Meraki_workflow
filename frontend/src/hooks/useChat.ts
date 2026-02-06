import { useEffect, useCallback } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { useWebSocket } from './useWebSocket';

const STORAGE_KEY = 'cnl-chat-sessions';

export function useChat() {
  const {
    sessions,
    activeSessionId,
    isStreaming,
    createSession,
    addMessage,
    setStreaming,
  } = useChatStore();

  const { send, status } = useWebSocket();

  // Load sessions from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        // const parsed = JSON.parse(stored);
        // TODO: Restore sessions to store
        // This would require a restoreSessions action in chatStore
      }
    } catch (error) {
      console.error('Failed to load chat sessions:', error);
    }
  }, []);

  // Save sessions to localStorage whenever they change
  useEffect(() => {
    try {
      // Don't save full API responses to avoid localStorage size limits
      const lightSessions = sessions.map(session => ({
        ...session,
        messages: session.messages.map(msg => ({
          ...msg,
          // Exclude large data payloads
          data: msg.data ? { format: msg.data.format } : undefined,
        })),
      }));
      localStorage.setItem(STORAGE_KEY, JSON.stringify(lightSessions));
    } catch (error) {
      console.error('Failed to save chat sessions:', error);
    }
  }, [sessions]);

  const sendMessage = useCallback(
    (content: string) => {
      if (!content.trim() || isStreaming) return;

      let sessionId = activeSessionId;

      // Create session if none exists
      if (!sessionId) {
        sessionId = createSession();
      }

      // Add user message to store
      addMessage(sessionId, {
        role: 'user',
        content: content.trim(),
        sessionId,
      });

      // Create placeholder assistant message for streaming
      addMessage(sessionId, {
        role: 'assistant',
        content: '',
        sessionId,
        streaming: true,
      });

      // Send via WebSocket
      send({
        type: 'message',
        content: content.trim(),
        session_id: sessionId,
      });

      setStreaming(true);
    },
    [activeSessionId, isStreaming, createSession, addMessage, send, setStreaming]
  );

  const sendConfirmResponse = useCallback(
    (requestId: string, approved: boolean) => {
      send({
        type: 'confirm_response',
        request_id: requestId,
        approved,
        session_id: activeSessionId || undefined,
      });
    },
    [activeSessionId, send]
  );

  return {
    sessions,
    activeSessionId,
    isStreaming,
    connectionStatus: status,
    sendMessage,
    sendConfirmResponse,
    createSession,
  };
}
