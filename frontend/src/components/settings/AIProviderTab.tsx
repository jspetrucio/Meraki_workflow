import { useState } from 'react';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useSettingsStore } from '@/stores/settingsStore';
import { api } from '@/lib/api';
import type { Settings, ValidationResult } from '@/lib/types';

const PROVIDERS = [
  { value: 'anthropic', label: 'Anthropic (Claude)', models: ['claude-sonnet', 'claude-opus'] },
  { value: 'openai', label: 'OpenAI (GPT)', models: ['gpt-4o', 'gpt-4o-mini'] },
  { value: 'google', label: 'Google (Gemini)', models: ['gemini-2.0-flash', 'gemini-pro'] },
  { value: 'ollama', label: 'Ollama (Local)', models: ['llama3', 'mistral'] },
];

export function AIProviderTab() {
  const { settings, updateSettings } = useSettingsStore();
  const [apiKey, setApiKey] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<ValidationResult | null>(null);

  const currentProvider = PROVIDERS.find((p) => p.value === settings.ai_provider) || PROVIDERS[0];

  const handleProviderChange = async (provider: string) => {
    const previous = settings.ai_provider;
    updateSettings({ ai_provider: provider });

    try {
      await api.patch<Settings>('/api/v1/settings', { ai_provider: provider });
    } catch (err) {
      updateSettings({ ai_provider: previous });
      console.error('Failed to save provider:', err);
    }
  };

  const handleModelChange = async (model: string) => {
    const previous = settings.ai_model;
    updateSettings({ ai_model: model });

    try {
      await api.patch<Settings>('/api/v1/settings', { ai_model: model });
    } catch (err) {
      updateSettings({ ai_model: previous });
      console.error('Failed to save model:', err);
    }
  };

  const handleSaveKey = async () => {
    if (!apiKey.trim()) return;

    setIsSaving(true);
    try {
      await api.post<Settings>(`/api/v1/credentials/provider/${settings.ai_provider}`, {
        api_key: apiKey,
      });

      // Update has_ai_key status
      updateSettings({ has_ai_key: true });

      // Clear input after successful save
      setApiKey('');
      setTestResult({ valid: true, message: 'API key saved successfully' });
    } catch (err) {
      console.error('Failed to save API key:', err);
      setTestResult({ valid: false, message: 'Failed to save API key' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestConnection = async () => {
    if (!settings.has_ai_key && !apiKey.trim()) {
      setTestResult({ valid: false, message: 'Please enter an API key first' });
      return;
    }

    setIsTesting(true);
    setTestResult(null);

    try {
      const result = await api.post<ValidationResult>('/api/v1/credentials/validate', {
        type: 'ai',
        provider: settings.ai_provider,
        api_key: apiKey || undefined,
      });

      setTestResult(result);
    } catch (err) {
      console.error('Failed to test connection:', err);
      setTestResult({ valid: false, message: 'Connection test failed' });
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="space-y-4 py-4">
      <Card>
        <CardHeader>
          <CardTitle>AI Provider Configuration</CardTitle>
          <CardDescription>
            Select your AI provider and configure the connection
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="provider">Provider</Label>
            <Select
              value={settings.ai_provider}
              onValueChange={handleProviderChange}
            >
              <SelectTrigger id="provider">
                <SelectValue placeholder="Select provider" />
              </SelectTrigger>
              <SelectContent>
                {PROVIDERS.map((provider) => (
                  <SelectItem key={provider.value} value={provider.value}>
                    {provider.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="model">Model</Label>
            <Select
              value={settings.ai_model}
              onValueChange={handleModelChange}
            >
              <SelectTrigger id="model">
                <SelectValue placeholder="Select model" />
              </SelectTrigger>
              <SelectContent>
                {currentProvider.models.map((model) => (
                  <SelectItem key={model} value={model}>
                    {model}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="api-key">API Key</Label>
              {settings.has_ai_key && (
                <Badge variant="outline" className="text-green-600">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Configured
                </Badge>
              )}
            </div>
            <div className="flex gap-2">
              <Input
                id="api-key"
                type="password"
                placeholder={settings.has_ai_key ? '••••••••••••••••' : 'Enter API key'}
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
              Your API key is encrypted and stored securely
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleTestConnection}
              disabled={isTesting || (!settings.has_ai_key && !apiKey.trim())}
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
        </CardContent>
      </Card>
    </div>
  );
}
