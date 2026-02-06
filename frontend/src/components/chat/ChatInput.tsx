import { useState, useRef, type KeyboardEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Send, Square } from 'lucide-react';

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  isStreaming?: boolean;
  onStop?: () => void;
}

export function ChatInput({ onSend, disabled = false, isStreaming = false, onStop }: ChatInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!value.trim() || disabled || isStreaming) return;
    onSend(value);
    setValue('');

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  return (
    <div className="border-t bg-background p-4">
      <div className="flex gap-2 items-end max-w-4xl mx-auto">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          disabled={disabled}
          placeholder={
            isStreaming
              ? 'Waiting for response...'
              : 'Type your message... (Shift+Enter for newline)'
          }
          className="flex-1 min-h-[48px] max-h-[200px] px-4 py-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
          rows={1}
        />

        {isStreaming ? (
          <Button
            type="button"
            size="icon"
            variant="destructive"
            onClick={onStop}
            className="h-12 w-12"
          >
            <Square className="h-5 w-5" />
          </Button>
        ) : (
          <Button
            type="button"
            size="icon"
            onClick={handleSend}
            disabled={!value.trim() || disabled}
            className="h-12 w-12"
          >
            <Send className="h-5 w-5" />
          </Button>
        )}
      </div>

      <div className="text-xs text-muted-foreground text-center mt-2">
        Press Enter to send, Shift+Enter for newline
      </div>
    </div>
  );
}
