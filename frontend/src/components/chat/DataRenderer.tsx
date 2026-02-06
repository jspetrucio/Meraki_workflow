import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import type { MessageData } from '@/lib/types';

interface DataRendererProps {
  data: MessageData;
}

export function DataRenderer({ data }: DataRendererProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  switch (data.format) {
    case 'code':
      return <CodeBlock content={data.content} language={data.language} />;

    case 'table':
      return <TableView content={data.content} />;

    case 'html':
      return <HtmlReportViewer content={data.content} />;

    case 'diff':
      return <DiffView content={data.content} />;

    case 'json':
      return (
        <Card className="p-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">Data</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? 'Collapse' : 'Expand'}
            </Button>
          </div>
          {isExpanded && (
            <pre className="text-xs overflow-auto max-h-96 bg-muted p-3 rounded">
              {JSON.stringify(data.content, null, 2)}
            </pre>
          )}
        </Card>
      );

    default:
      return <pre className="text-xs">{String(data.content)}</pre>;
  }
}

function CodeBlock({ content, language }: { content: unknown; language?: string }) {
  const code = typeof content === 'string' ? content : JSON.stringify(content, null, 2);

  return (
    <Card className="p-4">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium">
          {language ? `Code (${language})` : 'Code'}
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigator.clipboard.writeText(code)}
        >
          Copy
        </Button>
      </div>
      <pre className="text-xs overflow-auto max-h-96 bg-muted p-3 rounded">
        <code>{code}</code>
      </pre>
    </Card>
  );
}

function TableView({ content }: { content: unknown }) {
  if (!Array.isArray(content)) {
    return <pre className="text-xs">{JSON.stringify(content)}</pre>;
  }

  if (content.length === 0) {
    return <p className="text-sm text-muted-foreground">No data</p>;
  }

  const headers = Object.keys(content[0] as Record<string, unknown>);

  return (
    <Card className="p-4 overflow-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            {headers.map((header) => (
              <th key={header} className="text-left py-2 px-3 font-medium">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {content.map((row, idx) => (
            <tr key={idx} className="border-b">
              {headers.map((header) => (
                <td key={header} className="py-2 px-3">
                  {String((row as Record<string, unknown>)[header])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function HtmlReportViewer({ content }: { content: unknown }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const htmlContent = typeof content === 'string' ? content : JSON.stringify(content);

  return (
    <Card className="p-4">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium">HTML Report</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? 'Collapse' : 'View Report'}
        </Button>
      </div>
      {isExpanded && (
        <iframe
          srcDoc={htmlContent}
          sandbox="allow-same-origin"
          className="w-full h-96 border rounded"
          title="HTML Report"
        />
      )}
    </Card>
  );
}

function DiffView({ content }: { content: unknown }) {
  const diffText = typeof content === 'string' ? content : JSON.stringify(content, null, 2);
  const lines = diffText.split('\n');

  return (
    <Card className="p-4">
      <div className="text-sm font-medium mb-2">Configuration Changes</div>
      <pre className="text-xs overflow-auto max-h-96 bg-muted p-3 rounded">
        {lines.map((line, idx) => {
          let className = '';
          if (line.startsWith('+')) className = 'text-green-600 dark:text-green-400';
          if (line.startsWith('-')) className = 'text-red-600 dark:text-red-400';
          if (line.startsWith('@@')) className = 'text-blue-600 dark:text-blue-400';

          return (
            <div key={idx} className={className}>
              {line}
            </div>
          );
        })}
      </pre>
    </Card>
  );
}
