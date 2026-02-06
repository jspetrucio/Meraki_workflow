import { Network, Workflow, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

interface WelcomeStepProps {
  onNext: () => void;
}

export function WelcomeStep({ onNext }: WelcomeStepProps) {
  return (
    <Card className="w-full max-w-2xl">
      <CardHeader className="text-center">
        <div className="mx-auto mb-4 h-20 w-20 rounded-2xl bg-primary flex items-center justify-center">
          <span className="text-primary-foreground font-bold text-4xl">C</span>
        </div>
        <CardTitle className="text-3xl">Welcome to CNL</CardTitle>
        <CardDescription className="text-base">
          Cisco Neural Language — Manage your Meraki infrastructure with natural language
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="grid gap-4">
          <div className="flex gap-4 items-start">
            <div className="rounded-lg bg-primary/10 p-3">
              <Network className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Network Discovery</h3>
              <p className="text-sm text-muted-foreground">
                Automatically analyze your Meraki network infrastructure, devices, and configurations
              </p>
            </div>
          </div>

          <div className="flex gap-4 items-start">
            <div className="rounded-lg bg-primary/10 p-3">
              <Zap className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Natural Language Configuration</h3>
              <p className="text-sm text-muted-foreground">
                Configure ACLs, firewall rules, SSIDs, and more using simple conversational commands
              </p>
            </div>
          </div>

          <div className="flex gap-4 items-start">
            <div className="rounded-lg bg-primary/10 p-3">
              <Workflow className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Workflow Automation</h3>
              <p className="text-sm text-muted-foreground">
                Create and manage automated workflows for compliance, remediation, and monitoring
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-lg bg-muted p-4">
          <p className="text-sm">
            <strong>Getting started takes just 2 minutes.</strong> We'll help you connect your Meraki
            organization and configure your AI provider.
          </p>
        </div>
      </CardContent>

      <CardFooter className="flex justify-center">
        <Button onClick={onNext} size="lg">
          Get Started
        </Button>
      </CardFooter>
    </Card>
  );
}
