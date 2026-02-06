import { useState } from 'react';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import type { AICredentials, AIProvider, ValidationResult } from './types';

interface AIProviderStepProps {
  credentials: AICredentials;
  onUpdate: (credentials: AICredentials) => void;
  onValidate: (provider: AIProvider, apiKey?: string) => Promise<ValidationResult>;
  onNext: () => void;
  onBack: () => void;
}

const AI_PROVIDERS: Array<{ value: AIProvider; label: string; description: string }> = [
  { value: 'anthropic', label: 'Anthropic Claude', description: 'GPT-4 class reasoning' },
  { value: 'openai', label: 'OpenAI GPT', description: 'Industry standard' },
  { value: 'google', label: 'Google Gemini', description: 'Multimodal AI' },
  { value: 'ollama', label: 'Ollama (Local)', description: 'Run models locally' },
];

export function AIProviderStep({
  credentials,
  onUpdate,
  onValidate,
  onNext,
  onBack,
}: AIProviderStepProps) {
  const [validationState, setValidationState] = useState<
    'idle' | 'validating' | 'success' | 'error'
  >('idle');
  const [validationMessage, setValidationMessage] = useState('');

  const requiresApiKey = credentials.provider !== 'ollama';

  const handleValidate = async () => {
    if (requiresApiKey && !credentials.apiKey) {
      setValidationState('error');
      setValidationMessage('Please enter your API key');
      return;
    }

    setValidationState('validating');
    setValidationMessage('');

    const result = await onValidate(credentials.provider, credentials.apiKey);

    if (result.valid) {
      setValidationState('success');
      setValidationMessage(result.message);
    } else {
      setValidationState('error');
      setValidationMessage(result.message);
    }
  };

  const handleNext = () => {
    if (validationState === 'success') {
      onNext();
    } else {
      handleValidate();
    }
  };

  const isValid = validationState === 'success';

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Configure AI Provider</CardTitle>
        <CardDescription>
          Select your preferred AI provider for natural language processing
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">AI Provider</label>
          <div className="grid grid-cols-2 gap-3">
            {AI_PROVIDERS.map((provider) => (
              <button
                key={provider.value}
                type="button"
                onClick={() => {
                  onUpdate({ ...credentials, provider: provider.value, apiKey: '' });
                  setValidationState('idle');
                  setValidationMessage('');
                }}
                className={`p-4 rounded-lg border-2 text-left transition-all ${
                  credentials.provider === provider.value
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50'
                }`}
                disabled={validationState === 'validating'}
              >
                <div className="font-semibold">{provider.label}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {provider.description}
                </div>
              </button>
            ))}
          </div>
        </div>

        {requiresApiKey && (
          <div className="space-y-2">
            <label htmlFor="ai-api-key" className="text-sm font-medium">
              API Key
            </label>
            <Input
              id="ai-api-key"
              type="password"
              placeholder={`Enter your ${AI_PROVIDERS.find((p) => p.value === credentials.provider)?.label} API key`}
              value={credentials.apiKey || ''}
              onChange={(e) =>
                onUpdate({ ...credentials, apiKey: e.target.value })
              }
              disabled={validationState === 'validating'}
            />
          </div>
        )}

        <div className="rounded-lg bg-muted p-4 space-y-2">
          <p className="text-sm font-medium">How to get your API key:</p>
          {credentials.provider === 'anthropic' && (
            <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
              <li>
                Visit{' '}
                <a
                  href="https://console.anthropic.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  console.anthropic.com
                </a>
              </li>
              <li>Navigate to API Keys section</li>
              <li>Click "Create Key" and copy it</li>
            </ul>
          )}
          {credentials.provider === 'openai' && (
            <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
              <li>
                Visit{' '}
                <a
                  href="https://platform.openai.com/api-keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  platform.openai.com
                </a>
              </li>
              <li>Click "Create new secret key"</li>
              <li>Copy the key immediately (it won't be shown again)</li>
            </ul>
          )}
          {credentials.provider === 'google' && (
            <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
              <li>
                Visit{' '}
                <a
                  href="https://makersuite.google.com/app/apikey"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  Google AI Studio
                </a>
              </li>
              <li>Click "Get API key"</li>
              <li>Create or select a project, then copy the key</li>
            </ul>
          )}
          {credentials.provider === 'ollama' && (
            <p className="text-sm text-muted-foreground">
              Ollama runs models locally on your machine. Make sure Ollama is installed and
              running on http://localhost:11434
            </p>
          )}
        </div>

        {validationState !== 'idle' && (
          <div
            className={`rounded-lg p-4 flex items-start gap-3 ${
              validationState === 'success'
                ? 'bg-green-50 dark:bg-green-950 text-green-900 dark:text-green-100'
                : validationState === 'error'
                  ? 'bg-red-50 dark:bg-red-950 text-red-900 dark:text-red-100'
                  : 'bg-muted'
            }`}
          >
            {validationState === 'validating' && (
              <>
                <Loader2 className="h-5 w-5 animate-spin mt-0.5" />
                <div>
                  <p className="font-medium">Validating connection...</p>
                  <p className="text-sm opacity-80">Testing {credentials.provider} API</p>
                </div>
              </>
            )}
            {validationState === 'success' && (
              <>
                <CheckCircle2 className="h-5 w-5 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium">Connection successful!</p>
                  <p className="text-sm opacity-80">{validationMessage}</p>
                </div>
              </>
            )}
            {validationState === 'error' && (
              <>
                <XCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium">Validation failed</p>
                  <p className="text-sm opacity-80">{validationMessage}</p>
                </div>
              </>
            )}
          </div>
        )}
      </CardContent>

      <CardFooter className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <div className="flex gap-2">
          {!isValid && (
            <Button
              variant="outline"
              onClick={handleValidate}
              disabled={
                validationState === 'validating' ||
                (requiresApiKey && !credentials.apiKey)
              }
            >
              {validationState === 'validating' ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Validating...
                </>
              ) : (
                'Validate'
              )}
            </Button>
          )}
          <Button
            onClick={handleNext}
            disabled={
              validationState === 'validating' ||
              (requiresApiKey && !credentials.apiKey)
            }
          >
            {isValid ? 'Continue' : 'Validate & Continue'}
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
