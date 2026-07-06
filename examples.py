#!/usr/bin/env python3
"""
Example script demonstrating how to use the RAG Intent Gateway API.
"""
import asyncio
import httpx


async def main():
    """Run example queries against the intent processing API."""
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/api/v1/intent/process"

    async with httpx.AsyncClient() as client:
        # Example 1: RAG query with history
        print("=" * 60)
        print("Example 1: RAG Query with History")
        print("=" * 60)

        rag_request = {
            "query": "把它和 B 公司的净利润对比一下，另外告诉我它们的负债情况",
            "history": [
                {
                    "role": "user",
                    "content": "我想了解一下 A 公司的年报"
                },
                {
                    "role": "assistant",
                    "content": "好的，我已经为您准备好了 A 公司 2025 年的财务报告。请问您想了解具体哪方面的内容？"
                }
            ]
        }

        response = await client.post(endpoint, json=rag_request)
        result = response.json()

        print(f"\n意图类型: {result['data']['intent_type']}")
        print(f"分类理由: {result['data']['reason']}")
        print(f"独立查询: {result['data']['standalone_query']}")
        print(f"子问题: {result['data']['sub_queries']}")
        print(f"扩展查询: {result['data']['expanded_queries']}")
        print(f"检索结果数: {len(result['retrieval_results'])}")

        # Example 2: Chitchat query
        print("\n" + "=" * 60)
        print("Example 2: CHITCHAT Query")
        print("=" * 60)

        chitchat_request = {
            "query": "哈喽，你今天心情怎么样？",
            "history": []
        }

        response = await client.post(endpoint, json=chitchat_request)
        result = response.json()

        print(f"\n意图类型: {result['data']['intent_type']}")
        print(f"分类理由: {result['data']['reason']}")
        print(f"回复文本: {result['data']['reply_text']}")

        # Example 3: Simple RAG query
        print("\n" + "=" * 60)
        print("Example 3: Simple RAG Query")
        print("=" * 60)

        simple_request = {
            "query": "什么是机器学习？",
            "history": []
        }

        response = await client.post(endpoint, json=simple_request)
        result = response.json()

        print(f"\n意图类型: {result['data']['intent_type']}")
        print(f"分类理由: {result['data']['reason']}")
        print(f"独立查询: {result['data']['standalone_query']}")
        print(f"扩展查询: {result['data']['expanded_queries']}")


if __name__ == "__main__":
    print("\n🤖 RAG Intent Gateway - Example Usage\n")
    print("⚠️  Make sure the server is running on http://localhost:8000")
    print("   Run: uvicorn app.main:app --reload\n")

    try:
        asyncio.run(main())
    except httpx.ConnectError:
        print("\n❌ Error: Cannot connect to the server.")
        print("   Please start the server first:")
        print("   uvicorn app.main:app --reload")