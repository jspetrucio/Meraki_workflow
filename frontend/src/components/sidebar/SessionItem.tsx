import { useState } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { MessageSquare, Trash2 } from 'lucide-react';
import type { ChatSession } from '@/lib/types';

interface SessionItemProps {
  session: ChatSession;
  isActive: boolean;
  onSelect?: () => void;
}

export function SessionItem({ session, isActive, onSelect }: SessionItemProps) {
  const { setActiveSession, deleteSession } = useChatStore();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const handleClick = () => {
    setActiveSession(session.id);
    onSelect?.();
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowDeleteDialog(true);
  };

  const confirmDelete = () => {
    deleteSession(session.id);
    setShowDeleteDialog(false);
  };

  // Get last message preview
  const lastMessage = session.messages[session.messages.length - 1];
  const preview = lastMessage
    ? lastMessage.content.slice(0, 50) + (lastMessage.content.length > 50 ? '...' : '')
    : 'No messages yet';

  // Format timestamp
  const timestamp = new Date(session.updatedAt).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });

  return (
    <>
      <TooltipProvider>
        <div
          onClick={handleClick}
          className={`
            group relative flex items-start gap-2 p-2 rounded-md cursor-pointer
            transition-colors hover:bg-muted
            ${isActive ? 'bg-muted border-l-2 border-primary' : ''}
          `}
          role="button"
          tabIndex={0}
          aria-label={`Chat: ${session.title}`}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              handleClick();
            }
          }}
        >
          <MessageSquare className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground" />

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-1">
              <h3 className="text-sm font-medium truncate">{session.title}</h3>
              <span className="text-xs text-muted-foreground flex-shrink-0">
                {timestamp}
              </span>
            </div>
            <p className="text-xs text-muted-foreground truncate mt-0.5">
              {preview}
            </p>
          </div>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={handleDelete}
                aria-label="Delete chat"
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Delete chat</p>
            </TooltipContent>
          </Tooltip>
        </div>
      </TooltipProvider>

      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Chat</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{session.title}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={confirmDelete}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
