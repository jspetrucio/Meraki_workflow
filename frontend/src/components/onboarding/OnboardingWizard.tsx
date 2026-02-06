import { useOnboarding } from '@/hooks/useOnboarding';
import { WelcomeStep } from './WelcomeStep';
import { MerakiKeyStep } from './MerakiKeyStep';
import { AIProviderStep } from './AIProviderStep';
import { SuccessStep } from './SuccessStep';

interface OnboardingWizardProps {
  onComplete: () => void;
}

export function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const {
    currentStep,
    formData,
    updateFormData,
    nextStep,
    prevStep,
    validateMerakiCredentials,
    validateAICredentials,
    saveMerakiCredentials,
    saveAICredentials,
    completeOnboarding,
  } = useOnboarding();

  const handleMerakiNext = async () => {
    // Save Meraki credentials
    const saved = await saveMerakiCredentials(
      formData.meraki.apiKey,
      formData.meraki.orgId
    );
    if (saved) {
      nextStep();
    }
  };

  const handleAINext = async () => {
    // Save AI credentials
    const saved = await saveAICredentials(
      formData.ai.provider,
      formData.ai.apiKey
    );
    if (saved) {
      nextStep();
    }
  };

  const handleComplete = async () => {
    // Mark onboarding as complete
    const completed = await completeOnboarding();
    if (completed) {
      onComplete();
    }
  };

  const totalSteps = 4;
  const stepNumber =
    currentStep === 'welcome'
      ? 1
      : currentStep === 'meraki'
        ? 2
        : currentStep === 'ai-provider'
          ? 3
          : 4;

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-2xl space-y-4">
        {/* Progress indicator */}
        <div className="text-center text-sm text-muted-foreground">
          Step {stepNumber} of {totalSteps}
        </div>

        <div className="w-full bg-muted rounded-full h-2">
          <div
            className="bg-primary h-2 rounded-full transition-all duration-300"
            style={{ width: `${(stepNumber / totalSteps) * 100}%` }}
          />
        </div>

        {/* Step content */}
        {currentStep === 'welcome' && <WelcomeStep onNext={nextStep} />}

        {currentStep === 'meraki' && (
          <MerakiKeyStep
            credentials={formData.meraki}
            onUpdate={(meraki) => updateFormData({ meraki })}
            onValidate={validateMerakiCredentials}
            onNext={handleMerakiNext}
            onBack={prevStep}
          />
        )}

        {currentStep === 'ai-provider' && (
          <AIProviderStep
            credentials={formData.ai}
            onUpdate={(ai) => updateFormData({ ai })}
            onValidate={validateAICredentials}
            onNext={handleAINext}
            onBack={prevStep}
          />
        )}

        {currentStep === 'success' && (
          <SuccessStep
            onStartDiscovery={handleComplete}
            onGoToSettings={handleComplete}
          />
        )}
      </div>
    </div>
  );
}
