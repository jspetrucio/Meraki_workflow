import { useState } from 'react';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useSettingsStore } from '@/stores/settingsStore';
import { api } from '@/lib/api';
import type { Settings, ValidationResult } from '@/lib/types';

export function N8NTab() {
  const { settings, updateSettings } = useSettingsStore();
  const [n8nUrl, setN8nUrl] = useState(settings.n8n_url || '');
  const [apiKey, setApiKey] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<ValidationResult | null>(null);

  const handleToggleN8N = async (enabled: boolean) => {
    const previous = settings.n8n_enabled;
    updateSettings({ n8n_enabled: enabled });

    try {
      await api.patch<Settings>('/api/v1/settings', { n8n_enabled: enabled });
    } catch (err) {
      updateSettings({ n8n_enabled: previous });
      console.error('Failed to toggle N8N:', err);
    }
  };

  const handleSaveUrl = async () => {
    if (!n8nUrl.trim()) return;

    setIsSaving(true);
    const previous = settings.n8n_url;
    updateSettings({ n8n_url: n8nUrl });

    try {
      await api.patch<Settings>('/api/v1/settings', { n8n_url: n8nUrl });
    } catch (err) {
      updateSettings({ n8n_url: previous });
      console.error('Failed to save N8N URL:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveKey = async () => {
    if (!apiKey.trim()) return;

    setIsSaving(true);
    try {
      // Save N8N API key (endpoint needs to be created in backend)
      await api.patch<Settings>('/api/v1/settings', { n8n_api_key: apiKey });

      // Update has_n8n_key status
      updateSettings({ has_n8n_key: true });

      // Clear input after successful save
      setApiKey('');
      setTestResult({ valid: true, message: 'N8N API key saved successfully' });
    } catch (err) {
      console.error('Failed to save N8N API key:', err);
      setTestResult({ valid: false, message: 'Failed to save N8N API key' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestConnection = async () => {
    if (!n8nUrl.trim()) {
      setTestResult({ valid: false, message: 'Please enter N8N URL first' });
      return;
    }

    setIsTesting(true);
    setTestResult(null);

    try {
      const result = await api.post<ValidationResult>('/api/v1/credentials/validate', {
        type: 'n8n',
        url: n8nUrl,
        api_key: apiKey || undefined,
      });

      setTestResult(result);
    } catch (err) {
      console.error('Failed to test N8N connection:', err);
      setTestResult({ valid: false, message: 'Connection test failed' });
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="space-y-4 py-4">
      <Card>
        <CardHeader>
          <CardTitle>N8N Integration</CardTitle>
          <CardDescription>
            Connect to N8N for advanced workflow automation
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="n8n-enabled">Enable N8N Integration</Label>
              <p className="text-sm text-muted-foreground">
                Allow the system to trigger N8N workflows
              </p>
            </div>
            <Switch
              id="n8n-enabled"
              checked={settings.n8n_enabled}
              onCheckedChange={handleToggleN8N}
            />
          </div>

          {settings.n8n_enabled && (
            <>
              <div className="space-y-2">
                <Label htmlFor="n8n-url">N8N URL</Label>
                <div className="flex gap-2">
                  <Input
                    id="n8n-url"
                    type="url"
                    placeholder="https://n8n.example.com"
                    value={n8nUrl}
                    onChange={(e) => setN8nUrl(e.target.value)}
                    className="flex-1"
                  />
                  <Button
                    onClick={handleSaveUrl}
                    disabled={isSaving || !n8nUrl.trim()}
                  >
                    {isSaving ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      'Save'
                    )}
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="n8n-api-key">API Key (Optional)</Label>
                  {settings.has_n8n_key && (
                    <Badge variant="outline" className="text-green-600">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Configured
                    </Badge>
                  )}
                </div>
                <div className="flex gap-2">
                  <Input
                    id="n8n-api-key"
                    type="password"
                    placeholder={settings.has_n8n_key ? '••••••••••••••••' : 'Enter API key'}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="flex-1"
                  />
                  <Button
                    onClick={handleSaveKey}
                    disabled={isSaving || !apiKey.trim()}
                  >
                    {isSaving ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      'Save'
                    )}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  API key is required for authenticated N8N instances
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  onClick={handleTestConnection}
                  disabled={isTesting || !n8nUrl.trim()}
                >
                  {isTesting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Testing...
                    </>
                  ) : (
                    'Test Connection'
                  )}
                </Button>

                {testResult && (
                  <div className="flex items-center gap-2">
                    {testResult.valid ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-600" />
                    )}
                    <span
                      className={`text-sm ${testResult.valid ? 'text-green-600' : 'text-red-600'}`}
                    >
                      {testResult.message}
                    </span>
                  </div>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
