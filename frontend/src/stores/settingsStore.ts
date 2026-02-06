import { create } from 'zustand';
import type { ConnectionStatus, Settings } from '@/lib/types';

interface SettingsState {
  settings: Settings;
  wsStatus: ConnectionStatus;
  merakiConnected: boolean;
  aiConfigured: boolean;
  loading: boolean;
  error: string | null;

  updateSettings: (partial: Partial<Settings>) => void;
  setWsStatus: (status: ConnectionStatus) => void;
  setMerakiConnected: (connected: boolean) => void;
  setAiConfigured: (configured: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  toggleTheme: () => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  settings: {
    theme: 'dark',
    language: 'en',
    apiBaseUrl: '/api',
    wsBaseUrl: `ws://${typeof window !== 'undefined' ? window.location.host : 'localhost:3141'}/ws`,
    ai_provider: 'anthropic',
    ai_model: 'claude-sonnet',
    has_ai_key: false,
    meraki_profile: 'default',
    n8n_enabled: false,
    has_n8n_key: false,
    port: 3141,
  },
  wsStatus: 'disconnected',
  merakiConnected: false,
  aiConfigured: false,
  loading: false,
  error: null,

  updateSettings: (partial) =>
    set((state) => ({
      settings: { ...state.settings, ...partial },
    })),

  setWsStatus: (status) => set({ wsStatus: status }),
  setMerakiConnected: (connected) => set({ merakiConnected: connected }),
  setAiConfigured: (configured) => set({ aiConfigured: configured }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),

  toggleTheme: () =>
    set((state) => ({
      settings: {
        ...state.settings,
        theme: state.settings.theme === 'dark' ? 'light' : 'dark',
      },
    })),
}));
