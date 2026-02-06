import { useState, useEffect } from 'react';
import { tauriInvoke, isTauri } from '@/lib/tauri';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Separator } from '../ui/separator';
import { RefreshCw, Info, Download, CheckCircle2, XCircle } from 'lucide-react';
import { Badge } from '../ui/badge';

interface AppVersion {
  version: string;
  buildDate: string;
}

interface CheckUpdateResult {
  available: boolean;
  version?: string;
  error?: string;
}

export function AboutSection() {
  const [appVersion, setAppVersion] = useState<AppVersion>({
    version: '0.1.0',
    buildDate: 'Unknown',
  });
  const [isChecking, setIsChecking] = useState(false);
  const [lastCheckTime, setLastCheckTime] = useState<number>(0);
  const [checkResult, setCheckResult] = useState<CheckUpdateResult | null>(null);

  useEffect(() => {
    loadAppVersion();
  }, []);

  const loadAppVersion = async () => {
    try {
      const version = await tauriInvoke<string>('get_version');
      if (version) {
        setAppVersion({
          version,
          buildDate: new Date().toISOString().split('T')[0],
        });
      }
    } catch (error) {
      console.error('Failed to load app version:', error);
    }
  };

  const handleCheckForUpdates = async () => {
    const now = Date.now();
    if (now - lastCheckTime < 60000) {
      const remainingSeconds = Math.ceil((60000 - (now - lastCheckTime)) / 1000);
      setCheckResult({
        available: false,
        error: `Please wait ${remainingSeconds}s before checking again`,
      });
      return;
    }

    setIsChecking(true);
    setCheckResult(null);
    setLastCheckTime(now);

    try {
      if (!isTauri()) {
        setCheckResult({ available: false, error: 'Updates only available in desktop app' });
        return;
      }
      const result = await tauriInvoke<{ available: boolean; version?: string }>(
        'check_for_updates'
      );

      setCheckResult({
        available: result?.available ?? false,
        version: result?.version,
      });
    } catch (error) {
      console.error('Failed to check for updates:', error);
      setCheckResult({
        available: false,
        error: String(error),
      });
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-4">About CNL</h3>
        <Card className="p-6">
          <div className="flex items-start gap-4">
            <div className="h-16 w-16 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Info className="h-8 w-8 text-white" />
            </div>
            <div className="flex-1 space-y-4">
              <div>
                <h4 className="font-semibold text-xl mb-1">
                  Cisco Neural Language
                </h4>
                <p className="text-sm text-muted-foreground">
                  Network automation through natural language
                </p>
              </div>

              <Separator />

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Version</p>
                  <p className="font-mono font-medium">{appVersion.version}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Build Date</p>
                  <p className="font-mono font-medium">{appVersion.buildDate}</p>
                </div>
              </div>

              <Separator />

              <div className="space-y-3">
                <Button
                  onClick={handleCheckForUpdates}
                  disabled={isChecking}
                  className="w-full"
                  variant="outline"
                >
                  {isChecking ? (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      Checking for Updates...
                    </>
                  ) : (
                    <>
                      <Download className="mr-2 h-4 w-4" />
                      Check for Updates
                    </>
                  )}
                </Button>

                {checkResult && (
                  <div className="rounded-md p-3 bg-muted">
                    {checkResult.error ? (
                      <div className="flex items-center gap-2 text-sm text-destructive">
                        <XCircle className="h-4 w-4" />
                        <span>{checkResult.error}</span>
                      </div>
                    ) : checkResult.available ? (
                      <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                        <Download className="h-4 w-4" />
                        <span>
                          Update available: v{checkResult.version}
                        </span>
                        <Badge variant="outline" className="ml-auto">
                          New
                        </Badge>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                        <CheckCircle2 className="h-4 w-4" />
                        <span>You're up to date!</span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <Separator />

              <div className="text-xs text-muted-foreground space-y-1">
                <p>© 2026 Cisco Systems, Inc.</p>
                <p>All rights reserved.</p>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
