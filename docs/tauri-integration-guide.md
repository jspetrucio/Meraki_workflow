# Tauri Native Features Integration Guide

This guide shows how to integrate with the native features implemented in Story 4.2.

---

## Available Tauri Commands

### 1. Backend Health Check

```typescript
import { invoke } from '@tauri-apps/api/core';

// Check if backend is healthy
const health = await invoke<string>('check_backend_health');
console.log(health); // "Backend is healthy"

// Check if backend is running
const isRunning = await invoke<boolean>('is_backend_running');
```

---

## 2. Autostart Management

### Check Autostart Status

```typescript
import { invoke } from '@tauri-apps/api/core';

const enabled = await invoke<boolean>('is_autostart_enabled');
if (enabled) {
  console.log('Launch on startup is enabled');
}
```

### Enable/Disable Autostart

```typescript
// Enable launch on startup
try {
  await invoke('enable_autostart');
  console.log('Autostart enabled');
} catch (error) {
  console.error('Failed to enable autostart:', error);
}

// Disable launch on startup
try {
  await invoke('disable_autostart');
  console.log('Autostart disabled');
} catch (error) {
  console.error('Failed to disable autostart:', error);
}
```

### Settings Panel Toggle Component

```typescript
import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

export function AutostartToggle() {
  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    invoke<boolean>('is_autostart_enabled')
      .then(setEnabled)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleToggle = async (checked: boolean) => {
    setLoading(true);
    try {
      if (checked) {
        await invoke('enable_autostart');
      } else {
        await invoke('disable_autostart');
      }
      setEnabled(checked);
    } catch (error) {
      console.error('Failed to toggle autostart:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <Switch
        id="autostart"
        checked={enabled}
        onCheckedChange={handleToggle}
        disabled={loading}
      />
      <Label htmlFor="autostart">
        Launch CNL on system startup
      </Label>
    </div>
  );
}
```

---

## 3. Native Notifications

### Show Notification

```typescript
import { invoke } from '@tauri-apps/api/core';

// Show a notification
await invoke('show_notification', {
  title: 'Discovery Complete',
  body: 'Found 5 networks and 23 devices',
});

// Show error notification
await invoke('show_notification', {
  title: 'Configuration Failed',
  body: 'Failed to apply ACL: Network not found',
});
```

### Check Notification Permission (macOS)

```typescript
const permission = await invoke<string>('check_notification_permission');
if (permission === 'granted') {
  // Can show notifications
} else {
  // Need to request permission
}
```

### Notification Helper Hook

```typescript
import { invoke } from '@tauri-apps/api/core';
import { useCallback } from 'react';

export function useNotification() {
  const showNotification = useCallback(
    async (title: string, body: string) => {
      try {
        await invoke('show_notification', { title, body });
      } catch (error) {
        console.error('Failed to show notification:', error);
      }
    },
    []
  );

  const showSuccess = useCallback(
    (message: string) => showNotification('Success', message),
    [showNotification]
  );

  const showError = useCallback(
    (message: string) => showNotification('Error', message),
    [showNotification]
  );

  return { showNotification, showSuccess, showError };
}
```

### Usage Example

```typescript
import { useNotification } from '@/hooks/useNotification';

function DiscoveryPanel() {
  const { showSuccess, showError } = useNotification();

  const runDiscovery = async () => {
    try {
      const result = await fetch('http://localhost:3141/api/v1/discovery/full', {
        method: 'POST',
      });
      const data = await result.json();
      showSuccess(`Discovery complete: ${data.networks.length} networks found`);
    } catch (error) {
      showError('Discovery failed: ' + error.message);
    }
  };

  return <button onClick={runDiscovery}>Run Discovery</button>;
}
```

---

## 4. Global Keyboard Shortcut

### Update Shortcut

```typescript
import { invoke } from '@tauri-apps/api/core';

// Change global shortcut
try {
  await invoke('update_global_shortcut', {
    newShortcut: 'Cmd+Shift+N',
  });
  console.log('Shortcut updated');
} catch (error) {
  console.error('Invalid shortcut format:', error);
}
```

### Shortcut Input Component

```typescript
import { useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';

export function ShortcutInput() {
  const [shortcut, setShortcut] = useState('Cmd+Shift+M');
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    setError(null);
    try {
      await invoke('update_global_shortcut', {
        newShortcut: shortcut,
      });
      console.log('Shortcut saved:', shortcut);
    } catch (err) {
      setError(String(err));
    }
  };

  return (
    <div className="space-y-2">
      <Label htmlFor="shortcut">Global Keyboard Shortcut</Label>
      <div className="flex space-x-2">
        <Input
          id="shortcut"
          value={shortcut}
          onChange={(e) => setShortcut(e.target.value)}
          placeholder="Cmd+Shift+M"
        />
        <Button onClick={handleSave}>Save</Button>
      </div>
      {error && <p className="text-sm text-red-500">{error}</p>}
      <p className="text-xs text-muted-foreground">
        Examples: Cmd+Shift+M, Ctrl+Alt+N, Alt+Space
      </p>
    </div>
  );
}
```

---

## 5. System Tray Events

### Listen for Tray Events

```typescript
import { listen } from '@tauri-apps/api/event';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export function TrayEventListener() {
  const navigate = useNavigate();

  useEffect(() => {
    // Listen for "Settings" click from tray
    const unlisten = listen('navigate-to-settings', () => {
      console.log('Settings requested from tray');
      navigate('/settings');
    });

    return () => {
      unlisten.then((fn) => fn());
    };
  }, [navigate]);

  return null;
}
```

### Register in App Root

```typescript
// In App.tsx or main layout component
import { TrayEventListener } from '@/components/TrayEventListener';

function App() {
  return (
    <>
      <TrayEventListener />
      {/* Rest of your app */}
    </>
  );
}
```

---

## 6. Complete Settings Panel Example

```typescript
import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';

export function DesktopSettingsPanel() {
  const [autostart, setAutostart] = useState(false);
  const [shortcut, setShortcut] = useState('Cmd+Shift+M');
  const [loading, setLoading] = useState(true);

  // Load current settings
  useEffect(() => {
    Promise.all([
      invoke<boolean>('is_autostart_enabled'),
      // You'd fetch the current shortcut from your settings API
    ])
      .then(([autostartEnabled]) => {
        setAutostart(autostartEnabled);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleAutostartToggle = async (checked: boolean) => {
    try {
      if (checked) {
        await invoke('enable_autostart');
      } else {
        await invoke('disable_autostart');
      }
      setAutostart(checked);
    } catch (error) {
      console.error('Failed to toggle autostart:', error);
    }
  };

  const handleShortcutSave = async () => {
    try {
      await invoke('update_global_shortcut', { newShortcut: shortcut });
      await invoke('show_notification', {
        title: 'Settings Saved',
        body: `Shortcut updated to ${shortcut}`,
      });
    } catch (error) {
      console.error('Failed to update shortcut:', error);
      await invoke('show_notification', {
        title: 'Error',
        body: 'Invalid shortcut format',
      });
    }
  };

  if (loading) {
    return <div>Loading settings...</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Desktop Integration</CardTitle>
        <CardDescription>
          Configure how CNL integrates with your operating system
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Autostart Toggle */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="autostart">Launch on Startup</Label>
            <p className="text-sm text-muted-foreground">
              Automatically start CNL when you log in
            </p>
          </div>
          <Switch
            id="autostart"
            checked={autostart}
            onCheckedChange={handleAutostartToggle}
          />
        </div>

        {/* Global Shortcut */}
        <div className="space-y-2">
          <Label htmlFor="shortcut">Global Keyboard Shortcut</Label>
          <p className="text-sm text-muted-foreground">
            Press this shortcut from anywhere to show/focus CNL
          </p>
          <div className="flex space-x-2">
            <Input
              id="shortcut"
              value={shortcut}
              onChange={(e) => setShortcut(e.target.value)}
              placeholder="Cmd+Shift+M"
            />
            <Button onClick={handleShortcutSave}>Save</Button>
          </div>
        </div>

        {/* System Tray Info */}
        <div className="space-y-2">
          <Label>System Tray</Label>
          <p className="text-sm text-muted-foreground">
            CNL minimizes to the system tray when you close the window.
            Right-click the tray icon for quick actions.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## 7. Error Handling Best Practices

### Always Wrap Tauri Invokes

```typescript
import { invoke } from '@tauri-apps/api/core';

async function safeInvoke<T>(
  command: string,
  args?: Record<string, unknown>
): Promise<T | null> {
  try {
    return await invoke<T>(command, args);
  } catch (error) {
    console.error(`Tauri command '${command}' failed:`, error);
    // Optionally show a notification
    await invoke('show_notification', {
      title: 'Error',
      body: `Command ${command} failed: ${error}`,
    }).catch(() => {
      // Ignore notification errors
    });
    return null;
  }
}

// Usage
const result = await safeInvoke<boolean>('is_autostart_enabled');
if (result !== null) {
  console.log('Autostart is enabled:', result);
}
```

---

## 8. Type Definitions

Create `src/types/tauri.ts`:

```typescript
// Tauri command types
export interface TauriCommands {
  check_backend_health(): Promise<string>;
  is_backend_running(): Promise<boolean>;
  is_autostart_enabled(): Promise<boolean>;
  enable_autostart(): Promise<void>;
  disable_autostart(): Promise<void>;
  show_notification(args: { title: string; body: string }): Promise<void>;
  check_notification_permission(): Promise<string>;
  update_global_shortcut(args: { newShortcut: string }): Promise<void>;
}

// Tray event types
export interface TrayEvents {
  'navigate-to-settings': void;
  'show-notification': {
    title: string;
    body: string;
  };
}
```

### Typed Invoke Helper

```typescript
import { invoke as tauriInvoke } from '@tauri-apps/api/core';
import { TauriCommands } from '@/types/tauri';

export async function invoke<K extends keyof TauriCommands>(
  command: K,
  ...args: Parameters<TauriCommands[K]> extends [infer P] ? [P] : []
): Promise<ReturnType<TauriCommands[K]>> {
  return tauriInvoke(command as string, ...args) as ReturnType<TauriCommands[K]>;
}

// Usage with full type safety
const health = await invoke('check_backend_health'); // string
const enabled = await invoke('is_autostart_enabled'); // boolean
await invoke('show_notification', { title: 'Test', body: 'Message' }); // void
```

---

## Summary

The Tauri native features integration provides:

1. **Autostart Management** - Enable/disable launch on startup
2. **Native Notifications** - Cross-platform OS notifications
3. **Global Shortcuts** - System-wide keyboard shortcuts
4. **System Tray** - Background operation with tray menu
5. **Event System** - React to tray actions from frontend

All features are accessible via simple `invoke()` calls from the frontend.
