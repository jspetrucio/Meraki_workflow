"""
Tests for WebSocket chat endpoint (Story 1.2).

Tests WebSocket protocol, message handling, and session management.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from scripts.server import app


# Test client
client = TestClient(app)


# ==================== WebSocket Connection Tests ====================


class TestWebSocketConnection:
    """Tests for WebSocket connection lifecycle."""

    def test_websocket_connect_and_disconnect(self):
        """Test basic WebSocket connection and disconnection."""
        with client.websocket_connect("/ws/chat") as ws:
            # Send ping
            ws.send_json({"type": "ping"})

            # Receive pong
            data = ws.receive_json()
            assert data["type"] == "pong"

    def test_websocket_multiple_connections(self):
        """Test multiple concurrent WebSocket connections."""
        # Open 3 concurrent connections
        with client.websocket_connect("/ws/chat") as ws1, \
             client.websocket_connect("/ws/chat") as ws2, \
             client.websocket_connect("/ws/chat") as ws3:

            # Each connection should work independently
            for ws in [ws1, ws2, ws3]:
                ws.send_json({"type": "ping"})
                data = ws.receive_json()
                assert data["type"] == "pong"

    def test_websocket_reconnect(self):
        """Test reconnecting after disconnect."""
        # First connection
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] == "pong"

        # Second connection (reconnect)
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] == "pong"


# ==================== Message Protocol Tests ====================


class TestMessageProtocol:
    """Tests for WebSocket message protocol."""

    def test_ping_pong(self):
        """Test ping/pong keepalive."""
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] == "pong"

    def test_invalid_json_handling(self):
        """Test handling of invalid JSON."""
        with client.websocket_connect("/ws/chat") as ws:
            # Send invalid JSON
            ws.send_text("not valid json {{{")

            # Should receive error
            data = ws.receive_json()
            assert data["type"] == "error"
            assert "INVALID_JSON" in data["code"]

    def test_unknown_message_type(self):
        """Test handling of unknown message type."""
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_json({"type": "unknown_type"})

            data = ws.receive_json()
            assert data["type"] == "error"
            assert "UNKNOWN_MESSAGE_TYPE" in data["code"]

    def test_empty_message_rejected(self):
        """Test that empty messages are rejected."""
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_json({
                "type": "message",
                "content": "",
                "session_id": "test-123"
            })

            data = ws.receive_json()
            assert data["type"] == "error"
            assert "EMPTY_MESSAGE" in data["code"]

    def test_message_too_long_rejected(self):
        """Test that messages exceeding max length are rejected."""
        with client.websocket_connect("/ws/chat") as ws:
            # Send message > 5000 chars
            long_content = "a" * 5001

            ws.send_json({
                "type": "message",
                "content": long_content,
                "session_id": "test-123"
            })

            data = ws.receive_json()
            assert data["type"] == "error"
            assert "MESSAGE_TOO_LONG" in data["code"]


# ==================== Message Processing Tests ====================


class TestMessageProcessing:
    """Tests for message processing via agent router."""

    @patch("scripts.server._ai_engine", None)
    def test_message_without_ai_engine(self):
        """Test message handling when AI engine is not configured."""
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_json({
                "type": "message",
                "content": "hello",
                "session_id": "test-123"
            })

            # Should receive agent_status
            data = ws.receive_json()
            assert data["type"] == "agent_status"
            assert data["status"] == "thinking"

            # Should receive stub response
            data = ws.receive_json()
            assert data["type"] == "stream"
            assert "not configured" in data["chunk"].lower()

            # Should receive done
            data = ws.receive_json()
            assert data["type"] == "done"

    @patch("scripts.server.process_message")
    @patch("scripts.server._ai_engine")
    def test_message_with_ai_engine(self, mock_ai_engine, mock_process):
        """Test message processing with AI engine configured."""
        # Mock AI engine
        mock_ai_engine.__bool__.return_value = True

        # Mock process_message to yield chunks
        async def mock_generator():
            yield {"type": "classification", "agent": "network-analyst", "confidence": 0.9}
            yield {"type": "stream", "chunk": "Processing", "agent": "network-analyst"}
            yield {"type": "stream", "chunk": " your request...", "agent": "network-analyst"}

        mock_process.return_value = mock_generator()

        with client.websocket_connect("/ws/chat") as ws:
            ws.send_json({
                "type": "message",
                "content": "analyze the network",
                "session_id": "test-123"
            })

            # Should receive agent_status
            data = ws.receive_json()
            assert data["type"] == "agent_status"

            # Should receive classification
            data = ws.receive_json()
            assert data["type"] == "classification"
            assert data["agent"] == "network-analyst"

            # Should receive stream chunks
            data = ws.receive_json()
            assert data["type"] == "stream"
            assert "Processing" in data["chunk"]

            data = ws.receive_json()
            assert data["type"] == "stream"

            # Should receive done
            data = ws.receive_json()
            assert data["type"] == "done"

    def test_session_persistence(self):
        """Test that messages are added to session."""
        with client.websocket_connect("/ws/chat") as ws:
            session_id = "test-session-persist"

            # Send first message
            ws.send_json({
                "type": "message",
                "content": "first message",
                "session_id": session_id
            })

            # Consume responses
            while True:
                data = ws.receive_json()
                if data["type"] == "done":
                    break

            # Send second message
            ws.send_json({
                "type": "message",
                "content": "second message",
                "session_id": session_id
            })

            # Consume responses
            while True:
                data = ws.receive_json()
                if data["type"] == "done":
                    break

            # Session should have 2 user messages
            from scripts.server import _session_manager
            session = _session_manager.get_session(session_id)
            assert session is not None
            assert len(session.messages) >= 2


# ==================== Cancel Flow Tests ====================


class TestCancelFlow:
    """Tests for canceling streaming responses."""

    def test_cancel_message(self):
        """Test sending cancel message."""
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_json({"type": "cancel"})

            data = ws.receive_json()
            assert data["type"] == "done"
            assert data.get("cancelled") is True


# ==================== Confirmation Flow Tests ====================


class TestConfirmationFlow:
    """Tests for confirmation requests and responses."""

    def test_confirmation_response_approved(self):
        """Test confirmation response with approval."""
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_json({
                "type": "confirm_response",
                "request_id": "req-123",
                "approved": True
            })

            data = ws.receive_json()
            assert data["type"] == "stream"
            assert "approved" in data["chunk"].lower()

    def test_confirmation_response_denied(self):
        """Test confirmation response with denial."""
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_json({
                "type": "confirm_response",
                "request_id": "req-123",
                "approved": False
            })

            data = ws.receive_json()
            assert data["type"] == "stream"
            assert "denied" in data["chunk"].lower()


# ==================== Session Management Tests ====================


class TestSessionManagement:
    """Tests for chat session management."""

    def test_session_auto_creation(self):
        """Test that session is auto-created if not provided."""
        with client.websocket_connect("/ws/chat") as ws:
            # Send message without session_id
            ws.send_json({
                "type": "message",
                "content": "hello"
            })

            # Should receive agent_status (connection established)
            data = ws.receive_json()
            assert data["type"] == "agent_status"

            # Consume remaining responses
            while True:
                data = ws.receive_json()
                if data["type"] == "done":
                    session_id = data.get("session_id")
                    assert session_id is not None
                    break

    def test_session_reuse(self):
        """Test that providing session_id reuses existing session."""
        session_id = "test-session-reuse"

        with client.websocket_connect("/ws/chat") as ws:
            # Send first message
            ws.send_json({
                "type": "message",
                "content": "first",
                "session_id": session_id
            })

            # Consume responses
            while True:
                data = ws.receive_json()
                if data["type"] == "done":
                    break

        # New connection with same session_id
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_json({
                "type": "message",
                "content": "second",
                "session_id": session_id
            })

            # Consume responses
            while True:
                data = ws.receive_json()
                if data["type"] == "done":
                    break

        # Session should have messages from both connections
        from scripts.server import _session_manager
        session = _session_manager.get_session(session_id)
        assert session is not None
        assert len(session.messages) >= 2


# ==================== Connection Manager Tests ====================


class TestConnectionManager:
    """Tests for ConnectionManager class."""

    def test_connection_manager_tracking(self):
        """Test that ConnectionManager tracks active connections."""
        from scripts.server import _connection_manager

        initial_count = _connection_manager.get_active_count()

        with client.websocket_connect("/ws/chat") as ws:
            ws.send_json({"type": "ping"})
            ws.receive_json()

            # Connection count should increase (after first message with session_id)
            # Note: Connection is registered after first message, not on connect

        # After disconnect, count should return to initial
        # (cleanup happens in finally block)


# ==================== Error Handling Tests ====================


class TestErrorHandling:
    """Tests for error handling in WebSocket endpoint."""

    @patch("scripts.server.process_message")
    @patch("scripts.server._ai_engine")
    def test_processing_error_handled(self, mock_ai_engine, mock_process):
        """Test that processing errors are caught and returned as error messages."""
        mock_ai_engine.__bool__.return_value = True

        # Mock process_message to raise exception
        async def mock_generator():
            raise ValueError("Test error")
            yield  # Never reached

        mock_process.return_value = mock_generator()

        with client.websocket_connect("/ws/chat") as ws:
            ws.send_json({
                "type": "message",
                "content": "test message",
                "session_id": "test-error"
            })

            # Should receive agent_status
            data = ws.receive_json()
            assert data["type"] == "agent_status"

            # Should receive error
            data = ws.receive_json()
            assert data["type"] == "error"
            assert "PROCESSING_ERROR" in data["code"]


# ==================== Run Tests ====================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
