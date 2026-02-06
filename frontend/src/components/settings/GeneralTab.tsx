import { useEffect, useState } from 'react';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ThemeToggle } from '@/components/common/ThemeToggle';
import { useSettingsStore } from '@/stores/settingsStore';
import { api } from '@/lib/api';
import type { Settings } from '@/lib/types';

export function GeneralTab() {
  const { settings, updateSettings } = useSettingsStore();
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    // Load settings from backend
    api
      .get<Settings>('/api/v1/settings')
      .then((data) => {
        updateSettings(data);
      })
      .catch((err) => {
        console.error('Failed to load settings:', err);
      });
  }, [updateSettings]);

  const handleLanguageChange = async (language: string) => {
    setIsSaving(true);
    const previous = settings.language;

    // Optimistic update
    updateSettings({ language });

    try {
      await api.patch<Settings>('/api/v1/settings', { language });
    } catch (err) {
      // Rollback on error
      updateSettings({ language: previous });
      console.error('Failed to save language:', err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-4 py-4">
      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Customize the look and feel of the application</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Theme</Label>
              <p className="text-sm text-muted-foreground">
                Switch between light and dark mode
              </p>
            </div>
            <ThemeToggle />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Localization</CardTitle>
          <CardDescription>Set your preferred language</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="language">Language</Label>
            <Select
              value={settings.language}
              onValueChange={handleLanguageChange}
              disabled={isSaving}
            >
              <SelectTrigger id="language">
                <SelectValue placeholder="Select language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="pt">Português</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Server Information</CardTitle>
          <CardDescription>Current server configuration</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label>Server Port</Label>
            <p className="text-sm font-mono bg-muted px-2 py-1 rounded">
              {settings.port || 3141}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
