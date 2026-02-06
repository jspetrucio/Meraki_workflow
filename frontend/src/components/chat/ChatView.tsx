import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ChevronDown } from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { useChat } from '@/hooks/useChat';
import { MessageBubble } from './MessageBubble';
import { StreamingText } from './StreamingText';
import { DataRenderer } from './DataRenderer';
import { ConfirmDialog } from './ConfirmDialog';
import { ChatInput } from './ChatInput';
import type { Message } from '@/lib/types';

export function ChatView() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [userScrolled, setUserScrolled] = useState(false);

  const { activeMessages, isStreaming } = useChatStore();
  const { sendMessage, sendConfirmResponse, connectionStatus } = useChat();
  const messages = activeMessages();

  // Auto-scroll to bottom on new messages (unless user scrolled up)
  useEffect(() => {
    if (!userScrolled && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, userScrolled]);

  const handleScroll = () => {
    if (!scrollRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;

    setShowScrollButton(!isAtBottom);
    setUserScrolled(!isAtBottom);
  };

  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      setUserScrolled(false);
    }
  };

  const handleStop = () => {
    // TODO: Implement stop streaming
    console.log('Stop streaming requested');
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b p-4 bg-background">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <h1 className="text-xl font-semibold">Chat</h1>
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                connectionStatus === 'connected'
                  ? 'bg-green-500'
                  : connectionStatus === 'connecting'
                  ? 'bg-yellow-500 animate-pulse'
                  : 'bg-red-500'
              }`}
            />
            <span className="text-sm text-muted-foreground capitalize">
              {connectionStatus}
            </span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1">
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="max-w-4xl mx-auto p-4 space-y-4"
        >
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-12">
              <div className="text-6xl mb-4">💬</div>
              <h2 className="text-xl font-semibold mb-2">Start a conversation</h2>
              <p className="text-muted-foreground max-w-md">
                Ask me to analyze your Meraki network, configure devices, or create automation workflows.
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <MessageItem
                key={message.id}
                message={message}
                onConfirm={sendConfirmResponse}
              />
            ))
          )}
        </div>
      </ScrollArea>

      {/* Scroll to bottom button */}
      {showScrollButton && (
        <div className="absolute bottom-24 right-8">
          <Button
            size="icon"
            variant="secondary"
            onClick={scrollToBottom}
            className="rounded-full shadow-lg"
          >
            <ChevronDown className="h-5 w-5" />
          </Button>
        </div>
      )}

      {/* Input */}
      <ChatInput
        onSend={sendMessage}
        disabled={connectionStatus !== 'connected'}
        isStreaming={isStreaming}
        onStop={handleStop}
      />
    </div>
  );
}

interface MessageItemProps {
  message: Message;
  onConfirm: (requestId: string, approved: boolean) => void;
}

function MessageItem({ message, onConfirm }: MessageItemProps) {
  // Regular message bubble
  if (!message.data && !message.confirmRequest) {
    if (message.streaming) {
      return (
        <div className="flex gap-3 mb-4">
          {message.agent && (
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <span className="text-sm">{message.agent.icon}</span>
            </div>
          )}
          <div className="flex flex-col max-w-[70%]">
            {message.agent && (
              <div className="text-xs text-muted-foreground mb-1 px-2">
                {message.agent.name}
              </div>
            )}
            <div className="rounded-lg px-4 py-2 bg-muted">
              <StreamingText content={message.content} isStreaming={true} />
            </div>
          </div>
        </div>
      );
    }
    return <MessageBubble message={message} />;
  }

  // Data message
  if (message.data) {
    return (
      <div className="mb-4">
        {message.agent && (
          <div className="text-xs text-muted-foreground mb-2 flex items-center gap-2">
            <span>{message.agent.icon}</span>
            <span>{message.agent.name}</span>
          </div>
        )}
        <DataRenderer data={message.data} />
      </div>
    );
  }

  // Confirm request
  if (message.confirmRequest) {
    return (
      <div className="mb-4">
        {message.agent && (
          <div className="text-xs text-muted-foreground mb-2 flex items-center gap-2">
            <span>{message.agent.icon}</span>
            <span>{message.agent.name}</span>
          </div>
        )}
        <ConfirmDialog
          confirmRequest={message.confirmRequest}
          onConfirm={onConfirm}
        />
      </div>
    );
  }

  return null;
}
