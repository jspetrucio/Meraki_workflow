import { Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useSettingsStore } from '@/stores/settingsStore';

export function ThemeToggle() {
  const { settings, toggleTheme } = useSettingsStore();
  const isDark = settings.theme === 'dark';

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </Button>
  );
}
