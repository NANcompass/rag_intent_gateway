"""
Tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app
from app.models import IntentResponse, IntentType


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app=app)


@pytest.fixture
def mock_rag_response():
    """Mock RAG intent response."""
    return IntentResponse(
        intent_type=IntentType.RAG,
        reason="用户需要查询财务信息",
        reply_text="",
        standalone_query="对比 A 公司和 B 公司的净利润",
        sub_queries=["A 公司净利润", "B 公司净利润"],
        expanded_queries=["A公司 B公司 财务对比", "A公司 B公司 盈利能力"]
    )


@pytest.fixture
def mock_chitchat_response():
    """Mock chitchat intent response."""
    return IntentResponse(
        intent_type=IntentType.CHITCHAT,
        reason="日常打招呼",
        reply_text="你好！我是 AI 助手，有什么可以帮助你的吗？",
        standalone_query="你好",
        sub_queries=[],
        expanded_queries=[]
    )


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "docs" in data


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@patch("app.api.v1.intent.llm_service")
def test_process_intent_rag(mock_service, client, mock_rag_response):
    """Test intent processing for RAG query."""
    mock_service.analyze_intent = AsyncMock(return_value=mock_rag_response)

    response = client.post(
        "/api/v1/intent/process",
        json={
            "query": "对比一下两家公司的净利润",
            "history": []
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["intent_type"] == "RAG"
    assert "retrieval_results" not in data


@patch("app.api.v1.intent.llm_service")
def test_process_intent_chitchat(mock_service, client, mock_chitchat_response):
    """Test intent processing for chitchat query."""
    mock_service.analyze_intent = AsyncMock(return_value=mock_chitchat_response)

    response = client.post(
        "/api/v1/intent/process",
        json={
            "query": "你好",
            "history": []
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["intent_type"] == "CHITCHAT"
    assert data["data"]["reply_text"] != ""
    assert "retrieval_results" not in data


@patch("app.api.v1.intent.llm_service")
def test_process_intent_with_history(mock_service, client, mock_rag_response):
    """Test intent processing with conversation history."""
    mock_service.analyze_intent = AsyncMock(return_value=mock_rag_response)

    response = client.post(
        "/api/v1/intent/process",
        json={
            "query": "它和 B 公司对比怎么样？",
            "history": [
                {"role": "user", "content": "我想了解 A 公司"},
                {"role": "assistant", "content": "好的，A 公司是一家..."}
            ]
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["intent_type"] == "RAG"


@patch("app.api.v1.intent.llm_service")
def test_process_intent_llm_error(mock_service, client):
    """Test intent processing when LLM fails."""
    mock_service.analyze_intent = AsyncMock(
        side_effect=ValueError("LLM API call failed")
    )

    response = client.post(
        "/api/v1/intent/process",
        json={
            "query": "测试查询",
            "history": []
        }
    )

    assert response.status_code == 422
    assert "Intent analysis failed" in response.json()["detail"]