import { renderMarkdown } from '@/lib/markdown';

interface StreamingTextProps {
  content: string;
  isStreaming?: boolean;
}

export function StreamingText({ content, isStreaming = false }: StreamingTextProps) {
  return (
    <div className="relative">
      <div
        className="prose prose-sm dark:prose-invert max-w-none"
        dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
      />
      {isStreaming && (
        <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
      )}
    </div>
  );
}
