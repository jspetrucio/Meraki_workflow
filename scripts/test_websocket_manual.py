#!/usr/bin/env python3
"""
Manual WebSocket test client for CNL chat endpoint.

Usage:
    python scripts/test_websocket_manual.py

Connects to ws://localhost:3141/ws/chat and allows interactive testing.
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime

try:
    import websockets
except ImportError:
    print("ERROR: websockets library not installed")
    print("Install with: pip install websockets")
    sys.exit(1)


async def test_websocket_chat():
    """Test WebSocket chat endpoint with interactive session."""
    uri = "ws://localhost:3141/ws/chat"
    session_id = str(uuid.uuid4())

    print(f"CNL WebSocket Test Client")
    print(f"==========================")
    print(f"Connecting to: {uri}")
    print(f"Session ID: {session_id}")
    print()

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected successfully!")
            print()

            # Test 1: Ping/Pong
            print("[TEST 1] Ping/Pong keepalive")
            await websocket.send(json.dumps({"type": "ping"}))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"  → Sent: ping")
            print(f"  ← Received: {data['type']}")
            assert data["type"] == "pong", "Expected pong response"
            print("  ✓ Ping/pong working")
            print()

            # Test 2: Invalid JSON
            print("[TEST 2] Invalid JSON handling")
            await websocket.send("not valid json {{{")
            response = await websocket.recv()
            data = json.loads(response)
            print(f"  → Sent: invalid JSON")
            print(f"  ← Received: {data['type']} - {data.get('message', '')}")
            assert data["type"] == "error", "Expected error response"
            print("  ✓ Invalid JSON rejected")
            print()

            # Test 3: Empty message
            print("[TEST 3] Empty message rejection")
            await websocket.send(json.dumps({
                "type": "message",
                "content": "",
                "session_id": session_id
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"  → Sent: empty message")
            print(f"  ← Received: {data['type']} - {data.get('message', '')}")
            assert data["type"] == "error", "Expected error response"
            print("  ✓ Empty message rejected")
            print()

            # Test 4: Send actual message
            print("[TEST 4] Sending actual message")
            test_message = "analyze the network"
            await websocket.send(json.dumps({
                "type": "message",
                "content": test_message,
                "session_id": session_id
            }))
            print(f"  → Sent: '{test_message}'")
            print()

            # Receive and display all responses
            response_count = 0
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    response_count += 1

                    msg_type = data["type"]
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

                    if msg_type == "agent_status":
                        print(f"  [{timestamp}] Status: {data.get('agent')} - {data.get('status')}")
                    elif msg_type == "classification":
                        print(f"  [{timestamp}] Classification:")
                        print(f"    Agent: {data.get('agent')}")
                        print(f"    Confidence: {data.get('confidence', 0):.0%}")
                        print(f"    Reasoning: {data.get('reasoning', 'N/A')}")
                    elif msg_type == "stream":
                        chunk = data.get("chunk", "")
                        agent = data.get("agent", "system")
                        print(f"  [{timestamp}] Stream ({agent}): {chunk}")
                    elif msg_type == "data":
                        format_type = data.get("format", "unknown")
                        print(f"  [{timestamp}] Data ({format_type}): {data.get('data', {})}")
                    elif msg_type == "error":
                        print(f"  [{timestamp}] ERROR: {data.get('message', 'Unknown error')}")
                    elif msg_type == "done":
                        print(f"  [{timestamp}] Done")
                        cancelled = data.get("cancelled", False)
                        if cancelled:
                            print(f"    (Cancelled)")
                        break
                    else:
                        print(f"  [{timestamp}] {msg_type}: {data}")

                except asyncio.TimeoutError:
                    print(f"  [Timeout] No more messages received")
                    break

            print()
            print(f"  ✓ Received {response_count} responses")
            print()

            # Test 5: Cancel flow
            print("[TEST 5] Cancel flow")
            await websocket.send(json.dumps({"type": "cancel"}))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"  → Sent: cancel")
            print(f"  ← Received: {data['type']}")
            assert data["type"] == "done", "Expected done response"
            assert data.get("cancelled") is True, "Expected cancelled flag"
            print("  ✓ Cancel flow working")
            print()

            # Test 6: Confirmation flow
            print("[TEST 6] Confirmation response")
            await websocket.send(json.dumps({
                "type": "confirm_response",
                "request_id": "test-req-123",
                "approved": True
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"  → Sent: confirm_response (approved)")
            print(f"  ← Received: {data['type']}")
            print("  ✓ Confirmation flow working")
            print()

            print("="*50)
            print("All tests passed successfully! ✓")
            print("="*50)

    except websockets.exceptions.WebSocketException as exc:
        print(f"WebSocket error: {exc}")
        print()
        print("Make sure the CNL server is running:")
        print("  python scripts/server.py")
        sys.exit(1)

    except Exception as exc:
        print(f"Unexpected error: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print()
    asyncio.run(test_websocket_chat())
    print()
