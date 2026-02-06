import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import type { ConfirmRequest } from '@/lib/types';

interface ConfirmDialogProps {
  confirmRequest: ConfirmRequest;
  onConfirm: (requestId: string, approved: boolean) => void;
}

export function ConfirmDialog({ confirmRequest, onConfirm }: ConfirmDialogProps) {
  const [confirmText, setConfirmText] = useState('');
  const [responded, setResponded] = useState(false);

  const isDangerous = confirmRequest.danger_level === 'high';
  const canConfirm = !isDangerous || confirmText === 'CONFIRM';

  const handleConfirm = () => {
    onConfirm(confirmRequest.request_id, true);
    setResponded(true);
  };

  const handleCancel = () => {
    onConfirm(confirmRequest.request_id, false);
    setResponded(true);
  };

  if (responded) {
    return (
      <Card className="p-4 border-muted">
        <p className="text-sm text-muted-foreground">Response sent</p>
      </Card>
    );
  }

  return (
    <Card className={`p-4 ${getDangerBorderClass(confirmRequest.danger_level)}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">⚠️</span>
          <h3 className="font-medium">Confirmation Required</h3>
        </div>
        <Badge variant={getDangerVariant(confirmRequest.danger_level)}>
          {confirmRequest.danger_level}
        </Badge>
      </div>

      <div className="mb-3">
        <p className="text-sm mb-2">{confirmRequest.action}</p>
        {confirmRequest.preview !== undefined && (
          <PreviewBox preview={confirmRequest.preview} />
        )}
      </div>

      {isDangerous && (
        <div className="mb-3">
          <label className="text-sm text-muted-foreground block mb-1">
            Type <code className="bg-muted px-1 rounded">CONFIRM</code> to proceed:
          </label>
          <Input
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder="CONFIRM"
            className="font-mono"
          />
        </div>
      )}

      <div className="flex gap-2 justify-end">
        <Button variant="outline" onClick={handleCancel} size="sm">
          Cancel
        </Button>
        <Button
          variant={isDangerous ? 'destructive' : 'default'}
          onClick={handleConfirm}
          disabled={!canConfirm}
          size="sm"
        >
          {isDangerous ? 'Execute (Dangerous)' : 'Confirm'}
        </Button>
      </div>
    </Card>
  );
}

function getDangerBorderClass(level: string): string {
  switch (level) {
    case 'high':
      return 'border-red-500 border-2';
    case 'medium':
      return 'border-yellow-500';
    case 'low':
      return 'border-blue-500';
    default:
      return '';
  }
}

function getDangerVariant(level: string): 'default' | 'destructive' | 'secondary' {
  switch (level) {
    case 'high':
      return 'destructive';
    case 'medium':
      return 'default';
    case 'low':
      return 'secondary';
    default:
      return 'default';
  }
}

function PreviewBox({ preview }: { preview: unknown }) {
  const previewText = typeof preview === 'string'
    ? preview
    : JSON.stringify(preview, null, 2);

  return (
    <div className="bg-muted p-3 rounded text-xs overflow-auto max-h-48">
      <pre>{previewText}</pre>
    </div>
  );
}
