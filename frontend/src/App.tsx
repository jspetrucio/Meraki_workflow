import { useEffect, useState } from 'react';
import { AppLayout } from '@/components/common/AppLayout';
import { OnboardingWizard } from '@/components/onboarding';
import { UpdateBanner } from '@/components/common/UpdateBanner';
import { ChatView } from '@/components/chat/ChatView';
import { api, fetchWithErrorHandling } from '@/lib/api';
import { tauriInvoke } from '@/lib/tauri';
import type { OnboardingStatus } from '@/components/onboarding';

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false);

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
        setShowOnboarding(!result.data.complete);
      } else {
        setShowOnboarding(true);
      }
    } catch (error) {
      console.error('Failed to check onboarding status:', error);
      setShowOnboarding(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOnboardingComplete = () => {
    setShowOnboarding(false);
  };

  const handleInstallUpdate = async () => {
    try {
      await tauriInvoke('install_update');
    } catch (error) {
      console.error('Failed to install update:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="h-16 w-16 mx-auto rounded-2xl bg-primary flex items-center justify-center animate-pulse">
            <span className="text-primary-foreground font-bold text-2xl">C</span>
          </div>
          <p className="text-muted-foreground">Loading CNL...</p>
        </div>
      </div>
    );
  }

  if (showOnboarding) {
    return <OnboardingWizard onComplete={handleOnboardingComplete} />;
  }

  return (
    <>
      <UpdateBanner onInstallUpdate={handleInstallUpdate} />
      <AppLayout>
        <ChatView />
      </AppLayout>
    </>
  );
}

export default App;
