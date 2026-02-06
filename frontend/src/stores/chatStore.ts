import { create } from 'zustand';
import type { Message, ChatSession } from '@/lib/types';

interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  isStreaming: boolean;

  activeSession: () => ChatSession | undefined;
  activeMessages: () => Message[];

  createSession: (title?: string) => string;
  setActiveSession: (id: string) => void;
  deleteSession: (id: string) => void;
  addMessage: (sessionId: string, message: Omit<Message, 'id' | 'timestamp'>) => void;
  appendToLastAssistant: (sessionId: string, chunk: string) => void;
  setStreaming: (streaming: boolean) => void;
}

let nextMsgId = 1;

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  isStreaming: false,

  activeSession: () => {
    const { sessions, activeSessionId } = get();
    return sessions.find((s) => s.id === activeSessionId);
  },

  activeMessages: () => {
    const session = get().activeSession();
    return session?.messages ?? [];
  },

  createSession: (title?: string) => {
    const id = `session-${Date.now()}`;
    const now = new Date().toISOString();
    const session: ChatSession = {
      id,
      title: title ?? 'New Chat',
      createdAt: now,
      updatedAt: now,
      messages: [],
    };
    set((state) => ({
      sessions: [session, ...state.sessions],
      activeSessionId: id,
    }));
    return id;
  },

  setActiveSession: (id) => set({ activeSessionId: id }),

  deleteSession: (id) =>
    set((state) => {
      const sessions = state.sessions.filter((s) => s.id !== id);
      const activeSessionId =
        state.activeSessionId === id
          ? sessions[0]?.id ?? null
          : state.activeSessionId;
      return { sessions, activeSessionId };
    }),

  addMessage: (sessionId, message) =>
    set((state) => ({
      sessions: state.sessions.map((s) =>
        s.id === sessionId
          ? {
              ...s,
              updatedAt: new Date().toISOString(),
              messages: [
                ...s.messages,
                {
                  ...message,
                  id: `msg-${nextMsgId++}`,
                  timestamp: new Date().toISOString(),
                  sessionId,
                },
              ],
            }
          : s
      ),
    })),

  appendToLastAssistant: (sessionId, chunk) =>
    set((state) => ({
      sessions: state.sessions.map((s) => {
        if (s.id !== sessionId) return s;
        const msgs = [...s.messages];
        const last = msgs[msgs.length - 1];
        if (last?.role === 'assistant') {
          msgs[msgs.length - 1] = { ...last, content: last.content + chunk };
        }
        return { ...s, messages: msgs };
      }),
    })),

  setStreaming: (streaming) => set({ isStreaming: streaming }),
}));
