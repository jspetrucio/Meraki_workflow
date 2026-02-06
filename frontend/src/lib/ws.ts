import type { ConnectionStatus } from './types';

type MessageHandler = (data: unknown) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private statusListeners: Set<(status: ConnectionStatus) => void> = new Set();
  private _status: ConnectionStatus = 'disconnected';

  constructor(url: string = `ws://${window.location.host}/ws/chat`) {
    this.url = url;
  }

  get status(): ConnectionStatus {
    return this._status;
  }

  private setStatus(status: ConnectionStatus) {
    this._status = status;
    this.statusListeners.forEach((fn) => fn(status));
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    this.setStatus('connecting');

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.setStatus('connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as Record<string, unknown>;
          const type = (data.type as string) || 'message';
          this.handlers.get(type)?.forEach((fn) => fn(data));
          this.handlers.get('*')?.forEach((fn) => fn(data));
        } catch {
          // Non-JSON message
        }
      };

      this.ws.onclose = () => {
        this.setStatus('disconnected');
        this.tryReconnect();
      };

      this.ws.onerror = () => {
        this.setStatus('error');
      };
    } catch {
      this.setStatus('error');
    }
  }

  disconnect(): void {
    this.reconnectAttempts = this.maxReconnectAttempts;
    this.ws?.close();
    this.ws = null;
    this.setStatus('disconnected');
  }

  send(data: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  on(type: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);
    return () => this.handlers.get(type)?.delete(handler);
  }

  onStatusChange(handler: (status: ConnectionStatus) => void): () => void {
    this.statusListeners.add(handler);
    return () => this.statusListeners.delete(handler);
  }

  private tryReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    setTimeout(() => this.connect(), delay);
  }
}

export const wsClient = new WebSocketClient();
