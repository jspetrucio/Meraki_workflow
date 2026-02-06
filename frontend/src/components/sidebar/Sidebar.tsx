import { useState, useEffect } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Plus, Menu, X } from 'lucide-react';
import { SessionItem } from './SessionItem';
import { AgentList } from './AgentList';
import { SettingsPanel } from '@/components/settings';

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { sessions, activeSessionId, createSession } = useChatStore();

  const handleNewChat = () => {
    createSession('New Chat');
    setMobileOpen(false);
  };

  // Close mobile sidebar when clicking outside
  useEffect(() => {
    if (!mobileOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      const sidebar = document.getElementById('mobile-sidebar');
      if (sidebar && !sidebar.contains(e.target as Node)) {
        setMobileOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [mobileOpen]);

  // Desktop collapsed state
  if (collapsed) {
    return (
      <aside className="hidden md:flex w-16 flex-col border-r border-border bg-muted/30">
        <div className="flex items-center justify-center p-4 border-b border-border">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed(false)}
            aria-label="Expand sidebar"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </div>
      </aside>
    );
  }

  const sidebarContent = (
    <>
      {/* Header with branding */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-sm">C</span>
          </div>
          <div>
            <h1 className="text-sm font-semibold">CNL</h1>
            <p className="text-xs text-muted-foreground">Cisco Neural Language</p>
          </div>
        </div>
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed(true)}
            aria-label="Collapse sidebar"
            className="hidden md:flex"
          >
            <X className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileOpen(false)}
            aria-label="Close sidebar"
            className="md:hidden"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-2">
        <Button
          onClick={handleNewChat}
          className="w-full justify-start gap-2"
          variant="outline"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      <Separator />

      {/* Session List */}
      <ScrollArea className="flex-1 px-2">
        <div className="space-y-1 py-2">
          {sessions.length === 0 ? (
            <div className="text-center text-sm text-muted-foreground py-8">
              No chats yet
            </div>
          ) : (
            sessions.map((session) => (
              <SessionItem
                key={session.id}
                session={session}
                isActive={session.id === activeSessionId}
                onSelect={() => setMobileOpen(false)}
              />
            ))
          )}
        </div>
      </ScrollArea>

      <Separator />

      {/* Agent List */}
      <AgentList />

      <Separator />

      {/* Footer: Settings + Connection Status */}
      <div className="p-2 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">Settings</span>
          <SettingsPanel />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">Status:</span>
          <span className="flex items-center gap-1 text-xs">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            Connected
          </span>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile hamburger button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setMobileOpen(true)}
        className="md:hidden fixed top-4 left-4 z-40"
        aria-label="Open sidebar"
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 bg-black/50 z-40" aria-hidden="true" />
      )}

      {/* Mobile sidebar */}
      <aside
        id="mobile-sidebar"
        className={`
          md:hidden fixed left-0 top-0 bottom-0 w-64 z-50
          flex flex-col border-r border-border bg-background
          transform transition-transform duration-200
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {sidebarContent}
      </aside>

      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-64 flex-col border-r border-border bg-muted/30">
        {sidebarContent}
      </aside>
    </>
  );
}
