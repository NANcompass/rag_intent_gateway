#!/usr/bin/env python3
"""
RAG Intent Gateway MCP Server - FastMCP with Streamable HTTP Transport
Exposes RAG intent processing functionality as MCP tools via HTTP

Run: python main_mcp.py
Endpoint: http://localhost:8022/mcp
"""
import asyncio
import sys
import os
import logging
from typing import Optional, List

from mcp.server.fastmcp import FastMCP

from app.core.config import settings
from app.services.llm_service import llm_service
from app.models import HistoryMessage, IntentType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# MCP configuration from environment
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8022"))

# Create FastMCP instance
mcp = FastMCP(
    "rag-intent-gateway-mcp",
    json_response=True  # Recommended for Dify compatibility
)

# Configure server
mcp.settings.host = MCP_HOST
mcp.settings.port = MCP_PORT
mcp.settings.transport_security.enable_dns_rebinding_protection = False
mcp.settings.transport_security.allowed_hosts = ["*"]
mcp.settings.transport_security.allowed_origins = ["*"]


@mcp.tool()
async def analyze_intent(
    query: str,
    history: Optional[str] = None
) -> str:
    """Analyze user query intent and perform intelligent query rewriting.

    This tool processes user queries through the RAG Intent Gateway pipeline:
    1. Intent Classification: Determines if query needs knowledge base retrieval (RAG)
       or is casual conversation (CHITCHAT)
    2. Context Resolution: Resolves ambiguous references using conversation history
    3. Query Rewriting: Splits complex queries into sub-queries
    4. Query Expansion: Generates synonym variants for better retrieval

    Args:
        query: User query text in natural language
        history: Optional conversation history in JSON format.
                 Format: '[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]'

    Returns:
        Structured analysis result including:
        - intent_type: RAG or CHITCHAT
        - reason: Classification reason
        - reply_text: Direct reply for CHITCHAT intent
        - standalone_query: Context-resolved query
        - sub_queries: Sub-queries for complex questions
        - expanded_queries: Synonym-expanded queries for retrieval
    """
    logger.info(f"MCP Tool called: analyze_intent(query='{query[:50]}...')")

    try:
        # Parse history if provided
        history_messages: List[HistoryMessage] = []
        if history:
            import json
            try:
                history_data = json.loads(history)
                history_messages = [HistoryMessage(**msg) for msg in history_data]
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to parse history, using empty: {e}")

        # Call the LLM service
        result = await llm_service.analyze_intent(query=query, history=history_messages)

        # Format response
        response_parts = [
            f"## Intent Analysis Result\n",
            f"**Intent Type**: {result.intent_type.value}",
            f"**Reason**: {result.reason}",
        ]

        if result.intent_type == IntentType.CHITCHAT:
            response_parts.append(f"\n**Direct Reply**:\n{result.reply_text}")
        else:
            response_parts.append(f"\n**Standalone Query**: {result.standalone_query}")

            if result.sub_queries:
                response_parts.append("\n**Sub-Queries**:")
                for i, sq in enumerate(result.sub_queries, 1):
                    response_parts.append(f"  {i}. {sq}")

            if result.expanded_queries:
                response_parts.append("\n**Expanded Queries**:")
                for i, eq in enumerate(result.expanded_queries, 1):
                    response_parts.append(f"  {i}. {eq}")

        return "\n".join(response_parts)

    except Exception as e:
        logger.error(f"MCP tool error: {str(e)}", exc_info=True)
        return f"Error processing query: {str(e)}"


@mcp.tool()
async def health_check() -> str:
    """Check the health status of the MCP server.

    Returns:
        Server health status and configuration info
    """
    logger.info("MCP Tool called: health_check")

    return f"""## RAG Intent Gateway MCP Server Health Check

**Status**: ✅ Healthy
**Version**: {settings.app_version}
**Model**: {settings.openai_model}
**Temperature**: {settings.openai_temperature}

The MCP server is running normally and ready to process requests.
"""


def main():
    """Main entry point - run MCP HTTP server"""
    logger.info(f"Starting RAG Intent Gateway MCP Server v{settings.app_version}")
    logger.info(f"MCP HTTP server listening on {MCP_HOST}:{MCP_PORT}")
    logger.info(f"MCP endpoint: http://{MCP_HOST}:{MCP_PORT}/mcp")

    try:
        import uvicorn

        # Get the Starlette app from FastMCP
        app = mcp.streamable_http_app()

        # Run with uvicorn
        config = uvicorn.Config(app, host=MCP_HOST, port=MCP_PORT, log_level="info")
        server = uvicorn.Server(config)
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error(f"MCP server error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()