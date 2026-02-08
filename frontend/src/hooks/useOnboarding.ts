import { useState, useEffect, useCallback } from 'react';
import { api, fetchWithErrorHandling } from '@/lib/api';
import type {
  OnboardingStep,
  OnboardingFormData,
  ValidationResult,
  OnboardingStatus,
  AIProvider,
} from '@/components/onboarding/types';

export function useOnboarding() {
  const [currentStep, setCurrentStep] = useState<OnboardingStep>('welcome');
  const [isLoading, setIsLoading] = useState(false);
  const [onboardingComplete, setOnboardingComplete] = useState<boolean | null>(null);
  const [formData, setFormData] = useState<OnboardingFormData>({
    meraki: { apiKey: '', orgId: '' },
    ai: { provider: 'anthropic', apiKey: '' },
  });

  // Check onboarding status on mount
  useEffect(() => {
    checkOnboardingStatus();
  }, []);

  const checkOnboardingStatus = async () => {
    setIsLoading(true);
    try {
      const result = await fetchWithErrorHandling<OnboardingStatus>(
        api.get('/v1/settings/onboarding-status')
      );
      if (result.success) {
        setOnboardingComplete(result.data.complete);
      }
    } catch (error) {
      console.error('Failed to check onboarding status:', error);
      // If API fails, assume onboarding not complete
      setOnboardingComplete(false);
    } finally {
      setIsLoading(false);
    }
  };

  const validateMerakiCredentials = async (
    apiKey: string,
    orgId: string
  ): Promise<ValidationResult> => {
    try {
      const result = await fetchWithErrorHandling<ValidationResult>(
        api.post('/v1/credentials/validate', {
          type: 'meraki',
          api_key: apiKey,
          org_id: orgId,
        })
      );

      if (result.success) {
        return result.data;
      }
      return {
        valid: false,
        message: result.message || 'Validation failed',
      };
    } catch (error) {
      return {
        valid: false,
        message: 'Network error: Could not validate credentials',
      };
    }
  };

  const validateAICredentials = async (
    provider: AIProvider,
    apiKey?: string
  ): Promise<ValidationResult> => {
    try {
      const result = await fetchWithErrorHandling<ValidationResult>(
        api.post('/v1/credentials/validate', {
          type: 'ai',
          provider,
          api_key: apiKey,
        })
      );

      if (result.success) {
        return result.data;
      }
      return {
        valid: false,
        message: result.message || 'Validation failed',
      };
    } catch (error) {
      return {
        valid: false,
        message: 'Network error: Could not validate credentials',
      };
    }
  };

  const saveMerakiCredentials = async (_apiKey: string, _orgId: string): Promise<boolean> => {
    try {
      // Meraki credentials are validated via /v1/credentials/validate (already done).
      // Save the profile setting so the backend knows which profile to use.
      const result = await fetchWithErrorHandling<{ success: boolean }>(
        api.patch('/v1/settings', {
          meraki_profile: 'default',
        })
      );
      return result.success;
    } catch (error) {
      console.error('Failed to save Meraki credentials:', error);
      return false;
    }
  };

  const saveAICredentials = async (provider: AIProvider, apiKey?: string): Promise<boolean> => {
    try {
      const result = await fetchWithErrorHandling<{ success: boolean }>(
        api.post(`/v1/credentials/provider/${provider}`, {
          api_key: apiKey,
        })
      );
      return result.success;
    } catch (error) {
      console.error('Failed to save AI credentials:', error);
      return false;
    }
  };

  const completeOnboarding = async (): Promise<boolean> => {
    // Onboarding is "complete" when both meraki_profile and ai_api_key exist.
    // The backend checks this via GET /v1/settings/onboarding-status.
    // No separate flag needs to be written — just mark local state as done.
    setOnboardingComplete(true);
    return true;
  };

  const updateFormData = useCallback((updates: Partial<OnboardingFormData>) => {
    setFormData((prev) => ({
      ...prev,
      ...updates,
    }));
  }, []);

  const nextStep = useCallback(() => {
    const steps: OnboardingStep[] = ['welcome', 'meraki', 'ai-provider', 'success'];
    const currentIndex = steps.indexOf(currentStep);
    if (currentIndex < steps.length - 1) {
      setCurrentStep(steps[currentIndex + 1]);
    }
  }, [currentStep]);

  const prevStep = useCallback(() => {
    const steps: OnboardingStep[] = ['welcome', 'meraki', 'ai-provider', 'success'];
    const currentIndex = steps.indexOf(currentStep);
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1]);
    }
  }, [currentStep]);

  return {
    currentStep,
    formData,
    isLoading,
    onboardingComplete,
    setCurrentStep,
    updateFormData,
    nextStep,
    prevStep,
    validateMerakiCredentials,
    validateAICredentials,
    saveMerakiCredentials,
    saveAICredentials,
    completeOnboarding,
  };
}
