"""Tests for Pydantic models."""
import pytest
from pydantic import ValidationError

from app.models import (
    IntentType,
    HistoryMessage,
    IntentRequest,
    IntentResponse,
    APIResponse,
)


def test_intent_type_enum():
    """Test IntentType enum."""
    assert IntentType.RAG == "RAG"
    assert IntentType.CHITCHAT == "CHITCHAT"


def test_history_message_model():
    """Test HistoryMessage model."""
    msg = HistoryMessage(role="user", content="你好")
    assert msg.role == "user"
    assert msg.content == "你好"


def test_intent_request_model():
    """Test IntentRequest model."""
    # Valid request
    req = IntentRequest(query="测试查询")
    assert req.query == "测试查询"
    assert req.history == []

    # With history
    req_with_history = IntentRequest(
        query="它怎么样？",
        history=[
            HistoryMessage(role="user", content="A公司"),
            HistoryMessage(role="assistant", content="好的")
        ]
    )
    assert len(req_with_history.history) == 2


def test_intent_request_validation():
    """Test IntentRequest validation."""
    # Empty query should fail
    with pytest.raises(ValidationError):
        IntentRequest(query="")

    # Missing query should fail
    with pytest.raises(ValidationError):
        IntentRequest()


def test_intent_response_model():
    """Test IntentResponse model."""
    # RAG response
    rag_response = IntentResponse(
        intent_type=IntentType.RAG,
        reason="需要检索知识库",
        reply_text="",
        standalone_query="A公司的财务情况",
        sub_queries=["A公司净利润", "A公司负债"],
        expanded_queries=["A公司财务报表", "A公司盈利能力"]
    )
    assert rag_response.intent_type == IntentType.RAG
    assert rag_response.reply_text == ""
    assert len(rag_response.sub_queries) == 2

    # CHITCHAT response
    chitchat_response = IntentResponse(
        intent_type=IntentType.CHITCHAT,
        reason="日常寒暄",
        reply_text="你好！有什么可以帮助你的吗？",
        standalone_query="你好",
        sub_queries=[],
        expanded_queries=[]
    )
    assert chitchat_response.intent_type == IntentType.CHITCHAT
    assert chitchat_response.reply_text != ""


def test_intent_response_defaults():
    """Test IntentResponse default values."""
    response = IntentResponse(
        intent_type=IntentType.RAG,
        reason="测试",
        standalone_query="测试查询"
    )
    assert response.reply_text == ""
    assert response.sub_queries == []
    assert response.expanded_queries == []


def test_api_response_model():
    """Test APIResponse model."""
    # Success response with RAG data
    intent_data = IntentResponse(
        intent_type=IntentType.RAG,
        reason="需要检索",
        reply_text="",
        standalone_query="测试查询",
        sub_queries=["子查询1"],
        expanded_queries=["扩展查询1"]
    )

    api_response = APIResponse(
        success=True,
        data=intent_data,
        message="处理成功"
    )

    assert api_response.success is True
    assert api_response.data.intent_type == IntentType.RAG
    assert api_response.message == "处理成功"
    assert not hasattr(api_response, 'retrieval_results')

    # Minimal response
    minimal_response = APIResponse(success=False, message="处理失败")
    assert minimal_response.data is None