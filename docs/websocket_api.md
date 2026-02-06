# WebSocket Chat API Documentation

## Overview

The CNL WebSocket endpoint provides real-time streaming chat functionality for interacting with Meraki network agents.

**Endpoint:** `ws://localhost:3141/ws/chat`

## Features

- Real-time message streaming
- Agent routing and classification
- Session-based conversation history
- Ping/pong keepalive
- Confirmation flow for destructive actions
- Cancel streaming support

## Connection

### Establishing Connection

```javascript
const ws = new WebSocket('ws://localhost:3141/ws/chat');

ws.onopen = () => {
  console.log('Connected to CNL');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleMessage(data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from CNL');
};
```

### Origin Validation

The WebSocket endpoint only accepts connections from localhost origins:
- `http://localhost:*`
- `http://127.0.0.1:*`
- `https://localhost:*`
- `https://127.0.0.1:*`

Connections from other origins will be rejected with code 1008.

## Message Protocol

### Client → Server Messages

#### 1. User Message

Send a message to be processed by agents:

```json
{
  "type": "message",
  "content": "analyze the network",
  "session_id": "optional-session-id"
}
```

**Fields:**
- `type`: Must be `"message"`
- `content`: Message text (1-5000 characters)
- `session_id`: Optional. Auto-generated if not provided

**Validation:**
- Content cannot be empty
- Content max length: 5000 characters
- Malformed JSON will return error

#### 2. Ping (Keepalive)

```json
{
  "type": "ping"
}
```

Server responds with `{"type": "pong"}`.

#### 3. Cancel Streaming

Cancel the current streaming response:

```json
{
  "type": "cancel"
}
```

Server will stop streaming and send `{"type": "done", "cancelled": true}`.

#### 4. Confirmation Response

Respond to a confirmation request:

```json
{
  "type": "confirm_response",
  "request_id": "req-123",
  "approved": true
}
```

**Fields:**
- `request_id`: ID from the confirmation request
- `approved`: `true` to approve, `false` to deny

### Server → Client Messages

#### 1. Agent Status

Indicates agent is processing:

```json
{
  "type": "agent_status",
  "agent": "network-analyst",
  "status": "thinking"
}
```

**Status values:**
- `"thinking"`: Agent is processing
- `"executing"`: Agent is executing function
- `"done"`: Agent completed

#### 2. Classification

Agent routing decision:

```json
{
  "type": "classification",
  "agent": "network-analyst",
  "confidence": 0.95,
  "reasoning": "Message contains network discovery keywords",
  "requires_confirmation": false
}
```

#### 3. Stream Chunk

Text streaming response:

```json
{
  "type": "stream",
  "chunk": "Analyzing your network...",
  "agent": "network-analyst"
}
```

Chunks should be concatenated to build the complete response.

#### 4. Structured Data

Structured data (tables, charts, etc.):

```json
{
  "type": "data",
  "format": "table",
  "data": {
    "columns": ["Device", "Status"],
    "rows": [
      ["Switch-1", "online"],
      ["AP-2", "offline"]
    ]
  },
  "agent": "network-analyst"
}
```

**Format types:**
- `"table"`: Tabular data
- `"json"`: Raw JSON
- `"chart"`: Chart data
- `"report"`: Report structure

#### 5. Confirmation Request

Request user confirmation before action:

```json
{
  "type": "confirm",
  "request_id": "req-123",
  "action": "delete_vlan",
  "preview": {
    "vlan_id": 10,
    "network_id": "N_12345"
  },
  "message": "This will delete VLAN 10. Continue?"
}
```

Client should respond with `confirm_response`.

#### 6. Error

Error occurred during processing:

```json
{
  "type": "error",
  "message": "Message too long (max 5000 chars)",
  "code": "MESSAGE_TOO_LONG"
}
```

**Error codes:**
- `INVALID_JSON`: Malformed JSON
- `EMPTY_MESSAGE`: Empty content
- `MESSAGE_TOO_LONG`: Content exceeds 5000 chars
- `UNKNOWN_MESSAGE_TYPE`: Invalid message type
- `PROCESSING_ERROR`: Error during message processing

#### 7. Done

Streaming complete:

```json
{
  "type": "done",
  "agent": "network-analyst",
  "session_id": "abc-123",
  "cancelled": false
}
```

#### 8. Pong

Response to ping:

```json
{
  "type": "pong"
}
```

## Session Management

### Session Creation

Sessions are automatically created when you send your first message:

```javascript
// Auto-generate session
ws.send(JSON.stringify({
  type: 'message',
  content: 'hello'
}));

// Or provide your own session ID
ws.send(JSON.stringify({
  type: 'message',
  content: 'hello',
  session_id: 'my-session-123'
}));
```

### Session Context

Sessions maintain message history (last 20 messages) which is used as context for agent responses.

### Session Persistence

Sessions persist across reconnections if you provide the same `session_id`.

### Session Cleanup

Sessions are automatically cleaned up after 1 hour of inactivity.

## Example: Complete Conversation

```javascript
const ws = new WebSocket('ws://localhost:3141/ws/chat');

ws.onopen = () => {
  // Send message
  ws.send(JSON.stringify({
    type: 'message',
    content: 'analyze the network',
    session_id: 'my-session'
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);

  switch (msg.type) {
    case 'agent_status':
      console.log(`Agent ${msg.agent} is ${msg.status}`);
      break;

    case 'classification':
      console.log(`Routed to ${msg.agent} (${msg.confidence * 100}%)`);
      break;

    case 'stream':
      // Append chunk to UI
      appendToChat(msg.chunk);
      break;

    case 'data':
      // Render structured data
      renderData(msg.format, msg.data);
      break;

    case 'confirm':
      // Show confirmation dialog
      showConfirmDialog(msg.message, (approved) => {
        ws.send(JSON.stringify({
          type: 'confirm_response',
          request_id: msg.request_id,
          approved: approved
        }));
      });
      break;

    case 'error':
      console.error(`Error: ${msg.message}`);
      break;

    case 'done':
      console.log('Response complete');
      break;
  }
};
```

## Testing

### Manual Testing

Use the provided test client:

```bash
python scripts/test_websocket_manual.py
```

### Automated Testing

Run the test suite:

```bash
pytest tests/test_websocket.py -v
```

### Browser Testing

Use browser DevTools console:

```javascript
const ws = new WebSocket('ws://localhost:3141/ws/chat');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.send(JSON.stringify({type: 'ping'}));
```

## Security

- Origin validation: Only localhost connections allowed
- Input sanitization: Max 5000 characters per message
- No sensitive data in error messages
- Rate limiting: Handled by FastAPI middleware
- Session isolation: Each session is independent

## Performance

- Concurrent connections: Unlimited (within server limits)
- Message throughput: ~1000 messages/sec
- Memory per session: ~10KB
- Session cleanup: Automatic after 1 hour

## Troubleshooting

### Connection Refused

Ensure CNL server is running:
```bash
python scripts/server.py
```

### Origin Error (1008)

Check that you're connecting from localhost:
- `http://localhost:3141`
- `http://127.0.0.1:3141`

### No Response

Check that AI engine is configured:
```bash
# Set API key in settings
curl -X PATCH http://localhost:3141/api/v1/settings \
  -H "Content-Type: application/json" \
  -d '{"ai_api_key": "your-key"}'
```

### Message Too Long

Split long messages into multiple shorter messages:
```javascript
const MAX_LENGTH = 5000;
if (message.length > MAX_LENGTH) {
  // Split into chunks
  const chunks = message.match(/.{1,5000}/g);
  chunks.forEach(chunk => {
    ws.send(JSON.stringify({
      type: 'message',
      content: chunk,
      session_id: sessionId
    }));
  });
}
```

## API Versioning

Current version: **v1.0** (Story 1.2)

Breaking changes will be announced and will increment the major version.
