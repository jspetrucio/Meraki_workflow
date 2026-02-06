"""
Multi-provider AI engine using LiteLLM.

Wraps LiteLLM for provider-agnostic completions with:
- Streaming support
- Function/tool calling
- Retry with exponential backoff
- Token usage tracking
- Custom error handling
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

import litellm
from litellm.exceptions import (
    APIConnectionError,
    AuthenticationError,
    RateLimitError,
)

from scripts.settings import Settings

logger = logging.getLogger(__name__)

# Custom exceptions


class AIEngineError(Exception):
    """Base exception for AI engine errors."""


class AIAuthError(AIEngineError):
    """Invalid API key or authentication failed."""


class AIRateLimitError(AIEngineError):
    """Rate limit exceeded."""


class AIConnectionError(AIEngineError):
    """Cannot reach provider."""


@dataclass
class SessionTokenUsage:
    """Token usage tracking per session."""

    session_id: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    call_count: int = 0


class AIEngine:
    """Multi-provider AI engine using LiteLLM."""

    def __init__(self, settings: Settings):
        """
        Initialize AI engine with settings.

        Args:
            settings: Settings object containing provider, model, and API key
        """
        self.provider = settings.ai_provider
        self.model = settings.ai_model
        self.api_key = settings.ai_api_key
        self._token_usage: dict[str, SessionTokenUsage] = {}

    def _get_model_string(self) -> str:
        """
        Map (provider, model) to LiteLLM format.

        Returns:
            LiteLLM model string (e.g. "anthropic/claude-sonnet-4-5-20250929")
        """
        model_map = {
            ("anthropic", "claude-sonnet"): "anthropic/claude-sonnet-4-5-20250929",
            ("anthropic", "claude-haiku"): "anthropic/claude-haiku-4-5-20251001",
            ("openai", "gpt-4o"): "openai/gpt-4o",
            ("openai", "gpt-4o-mini"): "openai/gpt-4o-mini",
            ("google", "gemini-pro"): "gemini/gemini-2.0-flash",
            ("ollama", "llama3"): "ollama/llama3.2",
        }
        return model_map.get((self.provider, self.model), f"{self.provider}/{self.model}")

    def update_settings(self, settings: Settings) -> None:
        """
        Update engine settings (for per-session provider switching).

        Args:
            settings: New settings to apply
        """
        self.provider = settings.ai_provider
        self.model = settings.ai_model
        self.api_key = settings.ai_api_key

    async def chat_completion(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        stream: bool = True,
        temperature: float = 0.1,
        session_id: str = "default",
    ) -> AsyncGenerator[dict, None] | dict:
        """
        Generate chat completion with retry logic.

        Args:
            messages: List of message dicts with role and content
            tools: Optional list of tool definitions
            stream: Whether to stream response chunks
            temperature: Sampling temperature (0.0-1.0)
            session_id: Session identifier for token tracking

        Returns:
            AsyncGenerator yielding chunks if stream=True, else full response dict

        Raises:
            AIAuthError: Invalid API key
            AIRateLimitError: Rate limit exceeded
            AIConnectionError: Cannot reach provider
        """
        model_string = self._get_model_string()

        # Retry configuration
        max_retries = 3
        retry_delays = [1, 2, 4]

        for attempt in range(max_retries):
            try:
                response = await litellm.acompletion(
                    model=model_string,
                    messages=messages,
                    tools=tools,
                    stream=stream,
                    temperature=temperature,
                    api_key=self.api_key,
                )

                if stream:
                    # Return async generator for streaming
                    return self._stream_with_tracking(response, session_id)
                else:
                    # Non-streaming: track usage and return response
                    self._track_usage(response, session_id)
                    return response

            except AuthenticationError as exc:
                # Don't retry auth errors
                logger.error("Authentication failed for provider %s", self.provider)
                raise AIAuthError(f"Invalid API key for {self.provider}") from exc

            except RateLimitError as exc:
                # Retry on rate limit
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.warning(
                        "Rate limit exceeded for %s, retrying in %ds (attempt %d/%d)",
                        self.provider,
                        delay,
                        attempt + 1,
                        max_retries,
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error("Rate limit exceeded after %d retries", max_retries)
                    raise AIRateLimitError("Rate limit exceeded") from exc

            except APIConnectionError as exc:
                # Retry on connection error
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.warning(
                        "Connection error to %s, retrying in %ds (attempt %d/%d)",
                        self.provider,
                        delay,
                        attempt + 1,
                        max_retries,
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error("Connection failed after %d retries", max_retries)
                    raise AIConnectionError(f"Cannot reach {self.provider}") from exc

            except Exception as exc:
                # Unknown error - don't retry
                logger.exception("Unexpected error during completion")
                raise AIEngineError(f"Completion failed: {type(exc).__name__}") from exc

        # Should never reach here
        raise AIEngineError("Maximum retries exceeded")

    async def _stream_with_tracking(
        self, response: AsyncGenerator, session_id: str
    ) -> AsyncGenerator[dict, None]:
        """
        Wrap streaming response to track token usage.

        Args:
            response: LiteLLM async generator
            session_id: Session identifier for token tracking

        Yields:
            Response chunks
        """
        accumulated_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        async for chunk in response:
            # Track usage if present in chunk
            if hasattr(chunk, "usage") and chunk.usage:
                usage = chunk.usage
                if hasattr(usage, "prompt_tokens") and usage.prompt_tokens:
                    accumulated_usage["prompt_tokens"] = usage.prompt_tokens
                if hasattr(usage, "completion_tokens") and usage.completion_tokens:
                    accumulated_usage["completion_tokens"] = usage.completion_tokens
                if hasattr(usage, "total_tokens") and usage.total_tokens:
                    accumulated_usage["total_tokens"] = usage.total_tokens

            yield chunk

        # Update session usage after stream completes
        if accumulated_usage["total_tokens"] > 0:
            self._update_session_usage(session_id, accumulated_usage)

    def _track_usage(self, response: dict, session_id: str) -> None:
        """
        Track token usage from non-streaming response.

        Args:
            response: LiteLLM response object
            session_id: Session identifier
        """
        if hasattr(response, "usage") and response.usage:
            usage = response.usage
            usage_dict = {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0),
            }
            self._update_session_usage(session_id, usage_dict)

    def _update_session_usage(self, session_id: str, usage: dict) -> None:
        """
        Update session token usage.

        Args:
            session_id: Session identifier
            usage: Dict with prompt_tokens, completion_tokens, total_tokens
        """
        if session_id not in self._token_usage:
            self._token_usage[session_id] = SessionTokenUsage(session_id=session_id)

        session = self._token_usage[session_id]
        session.prompt_tokens += usage.get("prompt_tokens", 0)
        session.completion_tokens += usage.get("completion_tokens", 0)
        session.total_tokens += usage.get("total_tokens", 0)
        session.call_count += 1

    async def classify(
        self, message: str, agents: list[dict], session_id: str = "default"
    ) -> dict:
        """
        Classify message to route to appropriate agent.

        Args:
            message: User message to classify
            agents: List of agent dicts with name and description
            session_id: Session identifier for token tracking

        Returns:
            Dict with agent, confidence, and reasoning

        Raises:
            AIEngineError: Classification failed
        """
        # Build route_to_agent tool definition
        tool_def = {
            "type": "function",
            "function": {
                "name": "route_to_agent",
                "description": "Route user message to the most appropriate agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent": {
                            "type": "string",
                            "enum": [agent["name"] for agent in agents],
                            "description": "Name of the agent to route to",
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Confidence score (0.0-1.0)",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Brief explanation of routing decision",
                        },
                    },
                    "required": ["agent", "confidence", "reasoning"],
                },
            },
        }

        # Build classification prompt
        agent_list = "\n".join([f"- {a['name']}: {a['description']}" for a in agents])
        messages = [
            {
                "role": "system",
                "content": f"You are a message classifier. Route user messages to the appropriate agent.\n\nAvailable agents:\n{agent_list}",
            },
            {"role": "user", "content": message},
        ]

        try:
            # Call with tool_choice="required" to force tool use
            response = await self.chat_completion(
                messages=messages,
                tools=[tool_def],
                stream=False,
                session_id=session_id,
            )

            # Parse tool call response
            if hasattr(response, "choices") and len(response.choices) > 0:
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "tool_calls"):
                    tool_calls = choice.message.tool_calls
                    if tool_calls and len(tool_calls) > 0:
                        tool_call = tool_calls[0]
                        if hasattr(tool_call, "function") and hasattr(
                            tool_call.function, "arguments"
                        ):
                            import json

                            args = json.loads(tool_call.function.arguments)
                            return {
                                "agent": args.get("agent"),
                                "confidence": args.get("confidence", 0.0),
                                "reasoning": args.get("reasoning", ""),
                            }

            raise AIEngineError("No valid tool call in classification response")

        except (AIEngineError, AIAuthError, AIRateLimitError, AIConnectionError):
            # Re-raise known errors
            raise
        except Exception as exc:
            logger.exception("Classification failed")
            raise AIEngineError(f"Classification failed: {type(exc).__name__}") from exc

    def get_session_usage(self, session_id: str = "default") -> SessionTokenUsage:
        """
        Get token usage for a session.

        Args:
            session_id: Session identifier

        Returns:
            SessionTokenUsage object
        """
        return self._token_usage.get(session_id, SessionTokenUsage(session_id=session_id))

    def reset_session_usage(self, session_id: str = "default") -> None:
        """
        Reset token usage for a session.

        Args:
            session_id: Session identifier
        """
        if session_id in self._token_usage:
            del self._token_usage[session_id]
