import { formatDistanceToNow } from '@/lib/date-utils';
import { renderMarkdown } from '@/lib/markdown';
import type { Message } from '@/lib/types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && message.agent && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
          <span className="text-sm">{message.agent.icon}</span>
        </div>
      )}

      <div className={`flex flex-col max-w-[70%] ${isUser ? 'items-end' : 'items-start'}`}>
        {!isUser && message.agent && (
          <div className="text-xs text-muted-foreground mb-1 px-2">
            {message.agent.name}
          </div>
        )}

        <div
          className={`rounded-lg px-4 py-2 ${
            isUser
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-foreground'
          }`}
        >
          {message.content && (
            <div
              className="prose prose-sm dark:prose-invert max-w-none"
              dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }}
            />
          )}
        </div>

        <div className="text-xs text-muted-foreground mt-1 px-2">
          {formatDistanceToNow(message.timestamp)}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
          <span className="text-sm text-primary-foreground">👤</span>
        </div>
      )}
    </div>
  );
}
