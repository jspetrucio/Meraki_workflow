import { useState } from 'react';
import { CheckCircle2, XCircle, Loader2, ExternalLink } from 'lucide-react';
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
import type { MerakiCredentials, ValidationResult } from './types';

interface MerakiKeyStepProps {
  credentials: MerakiCredentials;
  onUpdate: (credentials: MerakiCredentials) => void;
  onValidate: (apiKey: string, orgId: string) => Promise<ValidationResult>;
  onNext: () => void;
  onBack: () => void;
}

export function MerakiKeyStep({
  credentials,
  onUpdate,
  onValidate,
  onNext,
  onBack,
}: MerakiKeyStepProps) {
  const [validationState, setValidationState] = useState<
    'idle' | 'validating' | 'success' | 'error'
  >('idle');
  const [validationMessage, setValidationMessage] = useState('');
  const [orgName, setOrgName] = useState<string | undefined>();

  const handleValidate = async () => {
    if (!credentials.apiKey || !credentials.orgId) {
      setValidationState('error');
      setValidationMessage('Please enter both API Key and Organization ID');
      return;
    }

    setValidationState('validating');
    setValidationMessage('');

    const result = await onValidate(credentials.apiKey, credentials.orgId);

    if (result.valid) {
      setValidationState('success');
      setValidationMessage(result.message);
      setOrgName(result.orgName);
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
        <CardTitle>Connect Your Meraki Organization</CardTitle>
        <CardDescription>
          Enter your Meraki Dashboard API credentials to enable network management
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="api-key" className="text-sm font-medium">
            API Key
          </label>
          <Input
            id="api-key"
            type="password"
            placeholder="Enter your Meraki API key"
            value={credentials.apiKey}
            onChange={(e) =>
              onUpdate({ ...credentials, apiKey: e.target.value })
            }
            disabled={validationState === 'validating'}
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="org-id" className="text-sm font-medium">
            Organization ID
          </label>
          <Input
            id="org-id"
            type="text"
            placeholder="Enter your Organization ID"
            value={credentials.orgId}
            onChange={(e) =>
              onUpdate({ ...credentials, orgId: e.target.value })
            }
            disabled={validationState === 'validating'}
          />
        </div>

        <div className="rounded-lg bg-muted p-4 space-y-2">
          <p className="text-sm font-medium">How to get your credentials:</p>
          <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
            <li>
              Log in to{' '}
              <a
                href="https://dashboard.meraki.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline inline-flex items-center gap-1"
              >
                Meraki Dashboard
                <ExternalLink className="h-3 w-3" />
              </a>
            </li>
            <li>Navigate to Organization → Settings → Dashboard API access</li>
            <li>Click "Generate new API key" and copy it</li>
            <li>
              Your Organization ID is in the URL: dashboard.meraki.com/o/
              <strong>XXXXXX</strong>/...
            </li>
          </ol>
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
                  <p className="font-medium">Validating credentials...</p>
                  <p className="text-sm opacity-80">Connecting to Meraki Dashboard</p>
                </div>
              </>
            )}
            {validationState === 'success' && (
              <>
                <CheckCircle2 className="h-5 w-5 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium">Credentials validated successfully!</p>
                  {orgName && (
                    <p className="text-sm opacity-80">Connected to: {orgName}</p>
                  )}
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
                !credentials.apiKey ||
                !credentials.orgId
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
              !credentials.apiKey ||
              !credentials.orgId
            }
          >
            {isValid ? 'Continue' : 'Validate & Continue'}
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
