import { CheckCircle2, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

interface SuccessStepProps {
  onStartDiscovery: () => void;
  onGoToSettings: () => void;
}

export function SuccessStep({ onStartDiscovery, onGoToSettings }: SuccessStepProps) {
  return (
    <Card className="w-full max-w-2xl">
      <CardHeader className="text-center">
        <div className="mx-auto mb-4 h-20 w-20 rounded-full bg-green-100 dark:bg-green-950 flex items-center justify-center">
          <CheckCircle2 className="h-10 w-10 text-green-600 dark:text-green-400" />
        </div>
        <CardTitle className="text-3xl">All Set!</CardTitle>
        <CardDescription className="text-base">
          Your CNL environment is configured and ready to use
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="rounded-lg bg-muted p-4 space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium">Meraki Dashboard Connected</p>
              <p className="text-sm text-muted-foreground">
                Your organization credentials have been validated and saved securely
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium">AI Provider Configured</p>
              <p className="text-sm text-muted-foreground">
                Natural language processing is ready for your commands
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border-2 border-primary/20 bg-primary/5 p-4">
          <h3 className="font-semibold mb-2">What's next?</h3>
          <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
            <li>Run a full network discovery to analyze your infrastructure</li>
            <li>Chat with CNL to configure devices using natural language</li>
            <li>Create automated workflows for compliance and monitoring</li>
            <li>Generate reports and insights about your network</li>
          </ul>
        </div>
      </CardContent>

      <CardFooter className="flex flex-col sm:flex-row gap-3">
        <Button onClick={onGoToSettings} variant="outline" className="flex-1">
          <Settings className="h-4 w-4 mr-2" />
          Go to Settings
        </Button>
        <Button onClick={onStartDiscovery} size="lg" className="flex-1">
          Start Discovery
        </Button>
      </CardFooter>
    </Card>
  );
}
