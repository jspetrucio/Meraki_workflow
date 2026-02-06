"""
Chat session management for CNL WebSocket chat.

Manages:
- Session lifecycle (creation, cleanup)
- Message history (last 20 messages for context)
- Session persistence (in-memory for now)
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Individual chat message."""

    id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    agent: Optional[str] = None
    data: Optional[dict] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "agent": self.agent,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ChatSession:
    """Chat session with message history."""

    id: str
    profile: str = "default"
    messages: list[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_message(
        self,
        role: str,
        content: str,
        agent: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> ChatMessage:
        """
        Add a message to the session.

        Args:
            role: Message role (user/assistant/system)
            content: Message content
            agent: Optional agent name
            data: Optional structured data

        Returns:
            Created ChatMessage
        """
        message = ChatMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            agent=agent,
            data=data,
            timestamp=datetime.now(),
        )

        self.messages.append(message)
        self.updated_at = datetime.now()

        logger.debug(
            f"Added message to session {self.id}: role={role}, content_len={len(content)}"
        )

        return message

    def get_context(self, max_messages: int = 20) -> list[dict]:
        """
        Get recent messages as context for AI.

        Args:
            max_messages: Maximum number of messages to return

        Returns:
            List of message dicts with role and content
        """
        recent = self.messages[-max_messages:]
        return [
            {"role": msg.role, "content": msg.content}
            for msg in recent
            if msg.role != "system"  # Exclude system messages from context
        ]

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "id": self.id,
            "profile": self.profile,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class SessionManager:
    """Manages active chat sessions."""

    def __init__(self):
        self._sessions: dict[str, ChatSession] = {}
        logger.info("SessionManager initialized")

    def create_session(
        self, session_id: Optional[str] = None, profile: str = "default"
    ) -> ChatSession:
        """
        Create a new chat session.

        Args:
            session_id: Optional session ID (generated if not provided)
            profile: Meraki profile to use

        Returns:
            Created ChatSession
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        # Check if session already exists
        if session_id in self._sessions:
            logger.debug(f"Session {session_id} already exists, returning existing")
            return self._sessions[session_id]

        session = ChatSession(id=session_id, profile=profile)
        self._sessions[session_id] = session

        logger.info(f"Created session {session_id} with profile {profile}")

        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Get existing session by ID.

        Args:
            session_id: Session identifier

        Returns:
            ChatSession if found, None otherwise
        """
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Deleted session {session_id}")
            return True

        logger.warning(f"Attempted to delete non-existent session {session_id}")
        return False

    def cleanup_old_sessions(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up sessions older than max_age_seconds.

        Args:
            max_age_seconds: Maximum age in seconds (default: 1 hour)

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        to_delete = []

        for session_id, session in self._sessions.items():
            age = (now - session.updated_at).total_seconds()
            if age > max_age_seconds:
                to_delete.append(session_id)

        for session_id in to_delete:
            del self._sessions[session_id]

        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} old sessions")

        return len(to_delete)

    def get_active_count(self) -> int:
        """Get number of active sessions."""
        return len(self._sessions)

    def list_sessions(self) -> list[dict]:
        """
        List all active sessions.

        Returns:
            List of session summaries
        """
        return [
            {
                "id": session.id,
                "profile": session.profile,
                "message_count": len(session.messages),
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
            }
            for session in self._sessions.values()
        ]
