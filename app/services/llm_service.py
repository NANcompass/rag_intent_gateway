"""
LLM service for intent analysis using AsyncOpenAI with structured output.
"""
import json
from typing import List

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.models import HistoryMessage, IntentResponse, IntentType


# System prompt template for intent analysis
INTENT_SYSTEM_PROMPT = """# Role
你是一个专业的 RAG（检索增强生成）系统前置"意图识别与 Query 重写"引擎。你的职责是分析用户输入的 Query，结合多轮对话历史（Context），将其转化为结构化的检索任务。

# Constraints
1. 必须严格输出 JSON 格式，不要包含任何 Markdown 标记（如 ```json）或前后解释文本。
2. 当前年份为 2026 年。
3. 根据问题的实际复杂度和需求，灵活决定返回的子问题和扩展查询数量，不要机械地返回固定数量。

# Tasks
你需要在单次推理中完成以下四个步骤：
1. 【意图路由 (intent_type)】: 判断属于 RAG（需要查知识库回答的具体问题）或 CHITCHAT（打招呼、日常寒暄、纯打字机测试，无需查库）。
2. 【上下文消解 (standalone_query)】: 结合 history 补全当前 Query 中含糊不清的指代（如他、她、它、那个、上一个）或省略成分。如果没有历史，保持原样。
3. 【子问题拆分 (sub_queries)】: 根据问题的实际复杂度灵活处理：
   - 简单问题（单一事实查询）：返回空数组 []
   - 中等问题（2-3个维度）：拆分为 2-3 个独立子问题
   - 复杂问题（多维度对比/分析）：拆分为 3-5 个独立子问题
   每个子问题应该是单一维度、可独立检索的具体查询。
4. 【同义变体扩展 (expanded_queries)】: 根据核心检索概念的重要性和多样性灵活扩展：
   - 简单常见词：返回 1-2 个扩展变体（或不扩展）
   - 专业术语/多义词：返回 2-3 个扩展变体
   - 跨领域/多概念：返回 3-4 个扩展变体
   扩展应该使用专业术语、同义词、上下位词或英文翻译，提升召回率。

# Output Format (JSON)
{
  "intent_type": "RAG" | "CHITCHAT",
  "reason": "简短的一句话意图分类理由",
  "reply_text": "如果是 CHITCHAT，在此处直接给出日常寒暄的回复文本；如果是 RAG，此处为空字符串",
  "standalone_query": "补全了上下文、纠错后的独立查询词",
  "sub_queries": ["子问题1", "子问题2", ...],  // 根据复杂度返回 0-5 个
  "expanded_queries": ["扩展变体1", "扩展变体2", ...]  // 根据需求返回 0-4 个
}

# Examples

## Example 1 (简单查询 - 无需拆分，少量扩展)
[History]: []
[Query]: "什么是机器学习？"
[Output]:
{
  "intent_type": "RAG",
  "reason": "用户询问机器学习的定义，属于知识库检索范畴",
  "reply_text": "",
  "standalone_query": "什么是机器学习？",
  "sub_queries": [],
  "expanded_queries": [
    "机器学习的概念与定义",
    "Machine Learning 定义与原理"
  ]
}

## Example 2 (中等复杂度 - 需要拆分和扩展)
[History]: [
  {"role": "user", "content": "我想了解一下 A 公司的年报"},
  {"role": "assistant", "content": "好的，我已经为您准备好了 A 公司 2025 年的财务报告。请问您想了解具体哪方面的内容？"}
]
[Query]: "把它和 B 公司的净利润对比一下，另外告诉我它们的负债情况"
[Output]:
{
  "intent_type": "RAG",
  "reason": "用户要求对比两家公司的净利润与负债情况，需要检索财务知识库",
  "reply_text": "",
  "standalone_query": "对比 A 公司和 B 公司的净利润以及资产负债情况",
  "sub_queries": [
    "A 公司 2025 年净利润及负债情况",
    "B 公司最新净利润及负债情况"
  ],
  "expanded_queries": [
    "A公司 B公司 财务报表 净利润 对比",
    "A公司 B公司 资产负债率 盈利能力分析"
  ]
}

## Example 3 (复杂查询 - 多维度拆分和充分扩展)
[History]: []
[Query]: "对比一下 Python、Java 和 Go 三种语言在并发编程、内存管理和学习曲线方面的差异"
[Output]:
{
  "intent_type": "RAG",
  "reason": "用户要求对比三种编程语言在三个维度上的差异，需要检索技术知识库",
  "reply_text": "",
  "standalone_query": "对比 Python、Java 和 Go 三种语言在并发编程、内存管理和学习曲线方面的差异",
  "sub_queries": [
    "Python 并发编程特性与内存管理机制",
    "Java 并发编程特性与内存管理机制",
    "Go 并发编程特性与内存管理机制",
    "Python Java Go 学习曲线对比"
  ],
  "expanded_queries": [
    "Python Java Go 并发模型对比 goroutine thread",
    "Python Java Go 内存管理 GC 机制对比",
    "编程语言学习曲线难度对比 Python Java Go",
    "Python Java Go 语言特性优缺点分析"
  ]
}

## Example 4 (闲聊意图 - 空数组)
[History]: []
[Query]: "哈喽，你今天心情怎么样？"
[Output]:
{
  "intent_type": "CHITCHAT",
  "reason": "日常打招呼与寒暄，无需检索知识库",
  "reply_text": "嗨！我是一个 AI 助手，随时准备好为您提供帮助了！今天有什么我可以帮您的吗？",
  "standalone_query": "哈喽，你今天心情怎么样？",
  "sub_queries": [],
  "expanded_queries": []
}
"""


class LLMService:
    """Service for interacting with LLM using AsyncOpenAI."""

    def __init__(self):
        """Initialize the LLM service with AsyncOpenAI client."""
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=120.0  # Increased timeout for vLLM
        )
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature
        self.max_tokens = settings.openai_max_tokens

    def _format_history(self, history: List[HistoryMessage]) -> str:
        """
        Format history messages for the prompt.

        Args:
            history: List of historical messages

        Returns:
            Formatted history string
        """
        if not history:
            return "[]"

        history_list = [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]
        return json.dumps(history_list, ensure_ascii=False, indent=2)

    def _build_user_prompt(
        self,
        query: str,
        history: List[HistoryMessage]
    ) -> str:
        """
        Build the user prompt with query and history.

        Args:
            query: User's current query
            history: List of historical messages

        Returns:
            Formatted user prompt
        """
        history_str = self._format_history(history)
        return f"""---
现在请处理以下实际输入：
[History]: {history_str}
[Query]: "{query}"
[Output]:
"""

    async def analyze_intent(
        self,
        query: str,
        history: List[HistoryMessage] = None
    ) -> IntentResponse:
        """
        Analyze the user query and return structured intent response.

        This method uses AsyncOpenAI to call the LLM and forces the response
        to be parsed into the IntentResponse Pydantic model.

        Args:
            query: User's current query
            history: Optional list of historical messages

        Returns:
            IntentResponse: Structured intent analysis result

        Raises:
            ValueError: If the LLM response cannot be parsed
        """
        if history is None:
            history = []

        user_prompt = self._build_user_prompt(query, history)

        try:
            # Call OpenAI API with structured output
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )

            # Extract content
            content = response.choices[0].message.content

            # Parse JSON
            data = json.loads(content)

            # Validate with Pydantic model
            intent_response = IntentResponse(**data)

            return intent_response

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
        except ValidationError as e:
            raise ValueError(f"LLM response validation failed: {e}")
        except Exception as e:
            raise ValueError(f"LLM API call failed: {e}")


# Global service instance
llm_service = LLMService()
