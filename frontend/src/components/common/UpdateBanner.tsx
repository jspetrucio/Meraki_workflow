import { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { X, Download, SkipForward, Clock } from 'lucide-react';
import { Card } from '../ui/card';
import { tauriListen } from '@/lib/tauri';

interface UpdateInfo {
  version: string;
  notes: string;
  date?: string;
}

interface UpdateBannerProps {
  onInstallUpdate: () => void;
}

export function UpdateBanner({ onInstallUpdate }: UpdateBannerProps) {
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);

  useEffect(() => {
    const cleanup = tauriListen<UpdateInfo>('update-available', (update) => {
      const skippedVersion = localStorage.getItem('cnl-skipped-version');
      if (skippedVersion === update.version) {
        console.log(`Update ${update.version} was previously skipped`);
        return;
      }
      setUpdateInfo(update);
      setIsVisible(true);
    });

    return cleanup;
  }, []);

  const handleUpdateNow = async () => {
    setIsInstalling(true);
    setDownloadProgress(0);

    try {
      // Simulate progress (real progress tracking requires more Rust integration)
      const progressInterval = setInterval(() => {
        setDownloadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);

      // Trigger actual update installation
      await onInstallUpdate();

      setDownloadProgress(100);
    } catch (error) {
      console.error('Update installation failed:', error);
      setIsInstalling(false);
      setDownloadProgress(0);
    }
  };

  const handleSkipVersion = () => {
    if (updateInfo) {
      localStorage.setItem('cnl-skipped-version', updateInfo.version);
      setIsVisible(false);
    }
  };

  const handleRemindLater = () => {
    // Just dismiss until next app launch (no localStorage)
    setIsVisible(false);
  };

  const handleDismiss = () => {
    setIsVisible(false);
  };

  if (!isVisible || !updateInfo) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 max-w-md">
      <Card className="border-blue-500 bg-blue-50 dark:bg-blue-950 shadow-lg">
        <div className="p-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <Download className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              <div>
                <h3 className="font-semibold text-sm text-blue-900 dark:text-blue-100">
                  Update Available
                </h3>
                <p className="text-xs text-blue-700 dark:text-blue-300">
                  Version {updateInfo.version}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={handleDismiss}
              disabled={isInstalling}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {updateInfo.notes && (
            <p className="text-xs text-blue-800 dark:text-blue-200 mb-3 line-clamp-2">
              {updateInfo.notes}
            </p>
          )}

          {isInstalling && (
            <div className="mb-3">
              <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2">
                <div
                  className="bg-blue-600 dark:bg-blue-400 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${downloadProgress}%` }}
                />
              </div>
              <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                Downloading... {downloadProgress}%
              </p>
            </div>
          )}

          <div className="flex gap-2 flex-wrap">
            <Button
              size="sm"
              onClick={handleUpdateNow}
              disabled={isInstalling}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Download className="h-3 w-3 mr-1" />
              Update Now
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={handleRemindLater}
              disabled={isInstalling}
              className="border-blue-300 dark:border-blue-700"
            >
              <Clock className="h-3 w-3 mr-1" />
              Later
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={handleSkipVersion}
              disabled={isInstalling}
              className="text-blue-700 dark:text-blue-300"
            >
              <SkipForward className="h-3 w-3 mr-1" />
              Skip
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
