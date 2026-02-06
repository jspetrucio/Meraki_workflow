"""
Unit tests for AI Engine (LiteLLM wrapper).

Tests:
- Initialization and configuration
- Model string mapping
- Streaming and non-streaming completions
- Classification routing
- Retry logic
- Error handling
- Token usage tracking
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scripts.ai_engine import (
    AIAuthError,
    AIConnectionError,
    AIEngine,
    AIEngineError,
    AIRateLimitError,
    SessionTokenUsage,
)
from scripts.settings import Settings


# Fixtures


@pytest.fixture
def settings_anthropic():
    return Settings(
        ai_provider="anthropic", ai_model="claude-sonnet", ai_api_key="sk-ant-test-key"
    )


@pytest.fixture
def settings_openai():
    return Settings(ai_provider="openai", ai_model="gpt-4o", ai_api_key="sk-openai-test-key")


@pytest.fixture
def settings_google():
    return Settings(ai_provider="google", ai_model="gemini-pro", ai_api_key="google-test-key")


@pytest.fixture
def settings_ollama():
    return Settings(ai_provider="ollama", ai_model="llama3", ai_api_key=None)


@pytest.fixture
def engine_anthropic(settings_anthropic):
    return AIEngine(settings_anthropic)


# Test: Initialization


class TestAIEngineInit:
    def test_init_anthropic(self, engine_anthropic, settings_anthropic):
        assert engine_anthropic.provider == "anthropic"
        assert engine_anthropic.model == "claude-sonnet"
        assert engine_anthropic.api_key == "sk-ant-test-key"
        assert engine_anthropic._token_usage == {}

    def test_init_openai(self, settings_openai):
        engine = AIEngine(settings_openai)
        assert engine.provider == "openai"
        assert engine.model == "gpt-4o"
        assert engine.api_key == "sk-openai-test-key"

    def test_update_settings(self, engine_anthropic, settings_openai):
        engine_anthropic.update_settings(settings_openai)
        assert engine_anthropic.provider == "openai"
        assert engine_anthropic.model == "gpt-4o"
        assert engine_anthropic.api_key == "sk-openai-test-key"


# Test: Model String Mapping


class TestModelString:
    def test_model_string_anthropic_sonnet(self, engine_anthropic):
        assert engine_anthropic._get_model_string() == "anthropic/claude-sonnet-4-5-20250929"

    def test_model_string_anthropic_haiku(self):
        settings = Settings(
            ai_provider="anthropic", ai_model="claude-haiku", ai_api_key="sk-test"
        )
        engine = AIEngine(settings)
        assert engine._get_model_string() == "anthropic/claude-haiku-4-5-20251001"

    def test_model_string_openai_gpt4o(self, settings_openai):
        engine = AIEngine(settings_openai)
        assert engine._get_model_string() == "openai/gpt-4o"

    def test_model_string_openai_gpt4o_mini(self):
        settings = Settings(ai_provider="openai", ai_model="gpt-4o-mini", ai_api_key="sk-test")
        engine = AIEngine(settings)
        assert engine._get_model_string() == "openai/gpt-4o-mini"

    def test_model_string_google(self, settings_google):
        engine = AIEngine(settings_google)
        assert engine._get_model_string() == "gemini/gemini-2.0-flash"

    def test_model_string_ollama(self, settings_ollama):
        engine = AIEngine(settings_ollama)
        assert engine._get_model_string() == "ollama/llama3.2"

    def test_model_string_unknown_fallback(self):
        settings = Settings(
            ai_provider="unknown-provider", ai_model="unknown-model", ai_api_key="test"
        )
        engine = AIEngine(settings)
        assert engine._get_model_string() == "unknown-provider/unknown-model"


# Test: Chat Completion (Non-Streaming)


class TestChatCompletionNonStreaming:
    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_non_streaming_success(self, mock_completion, engine_anthropic):
        # Mock response
        mock_response = MagicMock()
        mock_response.usage = MagicMock(
            prompt_tokens=10, completion_tokens=20, total_tokens=30
        )
        mock_completion.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        result = await engine_anthropic.chat_completion(messages, stream=False)

        assert result == mock_response
        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args.kwargs
        assert call_kwargs["model"] == "anthropic/claude-sonnet-4-5-20250929"
        assert call_kwargs["messages"] == messages
        assert call_kwargs["stream"] is False
        assert call_kwargs["api_key"] == "sk-ant-test-key"

    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_non_streaming_with_tools(self, mock_completion, engine_anthropic):
        mock_response = MagicMock()
        mock_response.usage = MagicMock(
            prompt_tokens=10, completion_tokens=20, total_tokens=30
        )
        mock_completion.return_value = mock_response

        messages = [{"role": "user", "content": "Test"}]
        tools = [{"type": "function", "function": {"name": "test_tool"}}]

        result = await engine_anthropic.chat_completion(messages, tools=tools, stream=False)

        assert result == mock_response
        call_kwargs = mock_completion.call_args.kwargs
        assert call_kwargs["tools"] == tools


# Test: Chat Completion (Streaming)


class TestChatCompletionStreaming:
    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_streaming_success(self, mock_completion, engine_anthropic):
        # Mock streaming response
        async def mock_stream():
            chunks = [
                MagicMock(
                    choices=[MagicMock(delta=MagicMock(content="Hello"))],
                    usage=None,
                ),
                MagicMock(
                    choices=[MagicMock(delta=MagicMock(content=" world"))],
                    usage=None,
                ),
                MagicMock(
                    choices=[MagicMock(delta=MagicMock(content="!"))],
                    usage=MagicMock(prompt_tokens=5, completion_tokens=3, total_tokens=8),
                ),
            ]
            for chunk in chunks:
                yield chunk

        mock_completion.return_value = mock_stream()

        messages = [{"role": "user", "content": "Test"}]
        generator = await engine_anthropic.chat_completion(messages, stream=True)

        chunks = []
        async for chunk in generator:
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].choices[0].delta.content == "Hello"
        assert chunks[1].choices[0].delta.content == " world"
        assert chunks[2].choices[0].delta.content == "!"

    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_streaming_handles_connection_drop(self, mock_completion, engine_anthropic):
        async def mock_stream():
            yield MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))], usage=None)
            # Simulate connection drop
            raise ConnectionError("Connection lost")

        mock_completion.return_value = mock_stream()

        messages = [{"role": "user", "content": "Test"}]
        generator = await engine_anthropic.chat_completion(messages, stream=True)

        chunks = []
        with pytest.raises(ConnectionError):
            async for chunk in generator:
                chunks.append(chunk)

        assert len(chunks) == 1


# Test: Classification


class TestClassify:
    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_classify_success(self, mock_completion, engine_anthropic):
        # Mock tool call response
        mock_tool_call = MagicMock()
        mock_tool_call.function.arguments = json.dumps(
            {"agent": "meraki-specialist", "confidence": 0.95, "reasoning": "Configure ACL"}
        )

        mock_message = MagicMock()
        mock_message.tool_calls = [mock_tool_call]

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = MagicMock(
            prompt_tokens=50, completion_tokens=10, total_tokens=60
        )

        mock_completion.return_value = mock_response

        agents = [
            {"name": "meraki-specialist", "description": "Configure Meraki devices"},
            {"name": "network-analyst", "description": "Analyze network"},
        ]

        result = await engine_anthropic.classify("Configure ACL", agents)

        assert result["agent"] == "meraki-specialist"
        assert result["confidence"] == 0.95
        assert result["reasoning"] == "Configure ACL"

    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_classify_no_tool_call(self, mock_completion, engine_anthropic):
        mock_response = MagicMock()
        mock_response.choices = []
        mock_response.usage = None
        mock_completion.return_value = mock_response

        agents = [{"name": "test-agent", "description": "Test"}]

        with pytest.raises(AIEngineError, match="No valid tool call"):
            await engine_anthropic.classify("Test message", agents)


# Test: Retry Logic


class TestRetry:
    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_retry_on_rate_limit(self, mock_completion, engine_anthropic):
        from litellm.exceptions import RateLimitError

        # First two calls fail, third succeeds
        mock_response = MagicMock()
        mock_response.usage = MagicMock(
            prompt_tokens=10, completion_tokens=20, total_tokens=30
        )

        mock_completion.side_effect = [
            RateLimitError("Rate limit", "test", "anthropic"),
            RateLimitError("Rate limit", "test", "anthropic"),
            mock_response,
        ]

        messages = [{"role": "user", "content": "Test"}]
        result = await engine_anthropic.chat_completion(messages, stream=False)

        assert result == mock_response
        assert mock_completion.call_count == 3

    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_retry_on_connection_error(self, mock_completion, engine_anthropic):
        from litellm.exceptions import APIConnectionError

        mock_response = MagicMock()
        mock_response.usage = MagicMock(
            prompt_tokens=10, completion_tokens=20, total_tokens=30
        )

        mock_completion.side_effect = [
            APIConnectionError("Connection failed", "test", "anthropic"),
            mock_response,
        ]

        messages = [{"role": "user", "content": "Test"}]
        result = await engine_anthropic.chat_completion(messages, stream=False)

        assert result == mock_response
        assert mock_completion.call_count == 2

    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_no_retry_on_auth_error(self, mock_completion, engine_anthropic):
        from litellm.exceptions import AuthenticationError

        mock_completion.side_effect = AuthenticationError("Invalid key", "test", "anthropic")

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(AIAuthError, match="Invalid API key"):
            await engine_anthropic.chat_completion(messages, stream=False)

        assert mock_completion.call_count == 1

    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_max_retries_exceeded(self, mock_completion, engine_anthropic):
        from litellm.exceptions import RateLimitError

        mock_completion.side_effect = RateLimitError("Rate limit", "test", "anthropic")

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(AIRateLimitError, match="Rate limit exceeded"):
            await engine_anthropic.chat_completion(messages, stream=False)

        assert mock_completion.call_count == 3


# Test: Error Handling


class TestErrorHandling:
    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_auth_error_handling(self, mock_completion, engine_anthropic):
        from litellm.exceptions import AuthenticationError

        mock_completion.side_effect = AuthenticationError("Invalid", "test", "anthropic")

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(AIAuthError) as exc_info:
            await engine_anthropic.chat_completion(messages, stream=False)

        assert "Invalid API key for anthropic" in str(exc_info.value)
        # Ensure API key not in error message
        assert "sk-ant-test-key" not in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_rate_limit_error_handling(self, mock_completion, engine_anthropic):
        from litellm.exceptions import RateLimitError

        mock_completion.side_effect = RateLimitError("Rate limit", "test", "anthropic")

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(AIRateLimitError) as exc_info:
            await engine_anthropic.chat_completion(messages, stream=False)

        assert "Rate limit exceeded" in str(exc_info.value)
        # Ensure API key not in error message
        assert "sk-ant-test-key" not in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_connection_error_handling(self, mock_completion, engine_anthropic):
        from litellm.exceptions import APIConnectionError

        mock_completion.side_effect = APIConnectionError("Failed", "test", "anthropic")

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(AIConnectionError) as exc_info:
            await engine_anthropic.chat_completion(messages, stream=False)

        assert "Cannot reach anthropic" in str(exc_info.value)
        # Ensure API key not in error message
        assert "sk-ant-test-key" not in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_unknown_error_handling(self, mock_completion, engine_anthropic):
        mock_completion.side_effect = ValueError("Unknown error")

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(AIEngineError) as exc_info:
            await engine_anthropic.chat_completion(messages, stream=False)

        assert "Completion failed" in str(exc_info.value)


# Test: Token Tracking


class TestTokenTracking:
    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_token_tracking_non_streaming(self, mock_completion, engine_anthropic):
        mock_response = MagicMock()
        mock_response.usage = MagicMock(
            prompt_tokens=10, completion_tokens=20, total_tokens=30
        )
        mock_completion.return_value = mock_response

        messages = [{"role": "user", "content": "Test"}]
        await engine_anthropic.chat_completion(messages, stream=False, session_id="test-session")

        usage = engine_anthropic.get_session_usage("test-session")
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30
        assert usage.call_count == 1

    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_token_tracking_accumulation(self, mock_completion, engine_anthropic):
        mock_response = MagicMock()
        mock_response.usage = MagicMock(
            prompt_tokens=10, completion_tokens=20, total_tokens=30
        )
        mock_completion.return_value = mock_response

        messages = [{"role": "user", "content": "Test"}]

        # First call
        await engine_anthropic.chat_completion(messages, stream=False, session_id="session1")

        # Second call
        await engine_anthropic.chat_completion(messages, stream=False, session_id="session1")

        usage = engine_anthropic.get_session_usage("session1")
        assert usage.prompt_tokens == 20
        assert usage.completion_tokens == 40
        assert usage.total_tokens == 60
        assert usage.call_count == 2

    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_token_tracking_streaming(self, mock_completion, engine_anthropic):
        async def mock_stream():
            chunks = [
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Hi"))], usage=None),
                MagicMock(
                    choices=[MagicMock(delta=MagicMock(content="!"))],
                    usage=MagicMock(prompt_tokens=5, completion_tokens=2, total_tokens=7),
                ),
            ]
            for chunk in chunks:
                yield chunk

        mock_completion.return_value = mock_stream()

        messages = [{"role": "user", "content": "Test"}]
        generator = await engine_anthropic.chat_completion(
            messages, stream=True, session_id="stream-session"
        )

        async for _ in generator:
            pass

        usage = engine_anthropic.get_session_usage("stream-session")
        assert usage.prompt_tokens == 5
        assert usage.completion_tokens == 2
        assert usage.total_tokens == 7
        assert usage.call_count == 1

    def test_get_session_usage_nonexistent(self, engine_anthropic):
        usage = engine_anthropic.get_session_usage("nonexistent")
        assert usage.session_id == "nonexistent"
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0
        assert usage.call_count == 0

    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_reset_session_usage(self, mock_completion, engine_anthropic):
        mock_response = MagicMock()
        mock_response.usage = MagicMock(
            prompt_tokens=10, completion_tokens=20, total_tokens=30
        )
        mock_completion.return_value = mock_response

        messages = [{"role": "user", "content": "Test"}]
        await engine_anthropic.chat_completion(messages, stream=False, session_id="reset-test")

        usage_before = engine_anthropic.get_session_usage("reset-test")
        assert usage_before.total_tokens == 30

        engine_anthropic.reset_session_usage("reset-test")

        usage_after = engine_anthropic.get_session_usage("reset-test")
        assert usage_after.total_tokens == 0
        assert usage_after.call_count == 0

    @pytest.mark.asyncio
    @patch("scripts.ai_engine.litellm.acompletion")
    async def test_session_isolation(self, mock_completion, engine_anthropic):
        mock_response = MagicMock()
        mock_response.usage = MagicMock(
            prompt_tokens=10, completion_tokens=20, total_tokens=30
        )
        mock_completion.return_value = mock_response

        messages = [{"role": "user", "content": "Test"}]

        # Different sessions
        await engine_anthropic.chat_completion(messages, stream=False, session_id="session-a")
        await engine_anthropic.chat_completion(messages, stream=False, session_id="session-b")

        usage_a = engine_anthropic.get_session_usage("session-a")
        usage_b = engine_anthropic.get_session_usage("session-b")

        assert usage_a.total_tokens == 30
        assert usage_b.total_tokens == 30
        assert usage_a.session_id != usage_b.session_id
