export type OnboardingStep = 'welcome' | 'meraki' | 'ai-provider' | 'success';

export type AIProvider = 'anthropic' | 'openai' | 'google' | 'ollama';

export interface MerakiCredentials {
  apiKey: string;
  orgId: string;
}

export interface AICredentials {
  provider: AIProvider;
  apiKey?: string; // Optional for Ollama
}

export interface OnboardingFormData {
  meraki: MerakiCredentials;
  ai: AICredentials;
}

export interface ValidationResult {
  valid: boolean;
  message: string;
  orgName?: string; // Returned for Meraki validation
}

export interface OnboardingStatus {
  complete: boolean;
  missing: string[];
}
