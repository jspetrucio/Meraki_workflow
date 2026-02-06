import { Settings } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { GeneralTab } from './GeneralTab';
import { AIProviderTab } from './AIProviderTab';
import { ProfilesTab } from './ProfilesTab';
import { N8NTab } from './N8NTab';
import { AboutSection } from './AboutSection';

export function SettingsPanel() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Open settings"
          className="h-9 w-9"
        >
          <Settings className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
        </DialogHeader>
        <Tabs defaultValue="general" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="general">General</TabsTrigger>
            <TabsTrigger value="ai">AI Provider</TabsTrigger>
            <TabsTrigger value="profiles">Meraki Profiles</TabsTrigger>
            <TabsTrigger value="n8n">N8N</TabsTrigger>
            <TabsTrigger value="about">About</TabsTrigger>
          </TabsList>
          <TabsContent value="general" className="space-y-4">
            <GeneralTab />
          </TabsContent>
          <TabsContent value="ai" className="space-y-4">
            <AIProviderTab />
          </TabsContent>
          <TabsContent value="profiles" className="space-y-4">
            <ProfilesTab />
          </TabsContent>
          <TabsContent value="n8n" className="space-y-4">
            <N8NTab />
          </TabsContent>
          <TabsContent value="about" className="space-y-4">
            <AboutSection />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
