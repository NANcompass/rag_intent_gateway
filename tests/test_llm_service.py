"""
Tests for LLM Service.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from openai import AsyncOpenAI

from app.services.llm_service import LLMService, INTENT_SYSTEM_PROMPT
from app.models import IntentResponse, IntentType, HistoryMessage


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """{
        "intent_type": "RAG",
        "reason": "用户需要查询公司财务信息",
        "reply_text": "",
        "standalone_query": "对比 A 公司和 B 公司的净利润以及资产负债情况",
        "sub_queries": ["A 公司 2025 年净利润及负债情况", "B 公司最新净利润及负债情况"],
        "expanded_queries": ["A公司 B公司 财务报表 净利润 对比", "A公司 B公司 资产负债率 盈利能力分析"]
    }"""
    return mock_response


@pytest.fixture
def mock_chitchat_response():
    """Mock OpenAI API response for chitchat."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """{
        "intent_type": "CHITCHAT",
        "reason": "日常打招呼与寒暄，无需检索知识库",
        "reply_text": "嗨！我是一个 AI 助手，随时准备好为您提供帮助了！",
        "standalone_query": "哈喽，你今天心情怎么样？",
        "sub_queries": [],
        "expanded_queries": []
    }"""
    return mock_response


@pytest.mark.asyncio
async def test_analyze_intent_rag(mock_openai_response):
    """Test intent analysis for RAG query."""
    with patch.object(AsyncOpenAI, 'chat') as mock_chat:
        mock_completions = AsyncMock()
        mock_completions.completions = AsyncMock()
        mock_completions.completions.create = AsyncMock(return_value=mock_openai_response)
        mock_chat.completions = mock_completions.completions

        service = LLMService()
        result = await service.analyze_intent("对比一下两家公司的财务情况")

        assert isinstance(result, IntentResponse)
        assert result.intent_type == IntentType.RAG
        assert result.reason == "用户需要查询公司财务信息"
        assert result.reply_text == ""
        assert len(result.sub_queries) == 2
        assert len(result.expanded_queries) == 2


@pytest.mark.asyncio
async def test_analyze_intent_chitchat(mock_chitchat_response):
    """Test intent analysis for chitchat query."""
    with patch.object(AsyncOpenAI, 'chat') as mock_chat:
        mock_completions = AsyncMock()
        mock_completions.completions = AsyncMock()
        mock_completions.completions.create = AsyncMock(return_value=mock_chitchat_response)
        mock_completions.completions.create = AsyncMock(return_value=mock_chitchat_response)
        mock_chat.completions = mock_completions.completions

        service = LLMService()
        result = await service.analyze_intent("哈喽，你今天心情怎么样？")

        assert isinstance(result, IntentResponse)
        assert result.intent_type == IntentType.CHITCHAT
        assert result.reply_text != ""
        assert len(result.sub_queries) == 0
        assert len(result.expanded_queries) == 0


@pytest.mark.asyncio
async def test_analyze_intent_with_history():
    """Test intent analysis with conversation history."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """{
        "intent_type": "RAG",
        "reason": "用户想了解净利润对比",
        "reply_text": "",
        "standalone_query": "对比 A 公司和 B 公司的净利润情况",
        "sub_queries": [],
        "expanded_queries": []
    }"""

    with patch.object(AsyncOpenAI, 'chat') as mock_chat:
        mock_completions = AsyncMock()
        mock_completions.completions = AsyncMock()
        mock_completions.completions.create = AsyncMock(return_value=mock_response)
        mock_chat.completions = mock_completions.completions

        service = LLMService()
        history = [
            HistoryMessage(role="user", content="我想了解一下 A 公司的年报"),
            HistoryMessage(role="assistant", content="好的，我已经为您准备好了 A 公司的财务报告。")
        ]

        result = await service.analyze_intent("把它和 B 公司对比一下", history)

        assert isinstance(result, IntentResponse)
        assert result.intent_type == IntentType.RAG
        assert "对比" in result.standalone_query


def test_format_history():
    """Test history formatting."""
    service = LLMService()
    history = [
        HistoryMessage(role="user", content="你好"),
        HistoryMessage(role="assistant", content="你好！有什么可以帮助你的？")
    ]

    formatted = service._format_history(history)
    assert "你好" in formatted
    assert "user" in formatted
    assert "assistant" in formatted

    # Test empty history
    empty_formatted = service._format_history([])
    assert empty_formatted == "[]"


def test_build_user_prompt():
    """Test user prompt building."""
    service = LLMService()
    query = "这家公司怎么样？"
    history = [
        HistoryMessage(role="user", content="我想了解 A 公司"),
        HistoryMessage(role="assistant", content="好的，请问您想了解哪方面？")
    ]

    prompt = service._build_user_prompt(query, history)

    assert query in prompt
    assert "History" in prompt
    assert "Query" in prompt
    assert "Output" in prompt