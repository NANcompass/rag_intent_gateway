# RAG Intent Gateway API 文档

## 概述

RAG Intent Gateway 是一个基于大语言模型的 RAG（检索增强生成）前置意图处理系统。它能够智能分析用户查询，将其分类为 RAG（需要检索）或 CHITCHAT（闲聊）意图，并对检索类问题进行查询重写和扩展。

### 核心功能

- **意图分类**: 自动识别查询类型（RAG 或 CHITCHAT）
- **上下文消解**: 结合历史对话补全指代词和省略成分
- **子问题拆分**: 将复杂问题拆分为多个独立子查询
- **同义扩展**: 生成多种语义等价的检索词变体

### 基本信息

- **Base URL**: `http://localhost:8000`
- **API Version**: v1
- **API Prefix**: `/api/v1`
- **Content-Type**: `application/json`

---

## API 端点

### 1. 根路径信息

获取 API 基本信息。

**端点**: `GET /`

**请求示例**:
```bash
curl http://localhost:8000/
```

**响应示例**:
```json
{
  "name": "RAG Intent Gateway",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc",
  "api_prefix": "/api/v1"
}
```

**响应字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | API 名称 |
| version | string | API 版本 |
| docs | string | Swagger UI 文档路径 |
| redoc | string | ReDoc 文档路径 |
| api_prefix | string | API 路径前缀 |

---

### 2. 健康检查

检查服务健康状态。

**端点**: `GET /health`

**请求示例**:
```bash
curl http://localhost:8000/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

**响应字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 服务状态（"healthy" 或 "unhealthy"） |
| version | string | 当前版本 |

---

### 3. 意图处理（核心接口）

分析用户查询的意图并执行相应的处理。

**端点**: `POST /api/v1/intent/process`

**Content-Type**: `application/json`

---

#### 请求参数

**请求体结构**:

```json
{
  "query": string,           // 必填，用户查询
  "history": [               // 可选，历史对话列表
    {
      "role": string,        // "user" 或 "assistant"
      "content": string      // 消息内容
    }
  ]
}
```

**字段说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| query | string | ✅ | 当前用户查询，最少 1 个字符 |
| history | array | ❌ | 历史对话列表，用于上下文消解 |
| history[].role | string | - | 消息角色："user" 或 "assistant" |
| history[].content | string | - | 消息内容 |

---

#### 响应结构

**成功响应** (HTTP 200):

```json
{
  "success": boolean,                // 处理是否成功
  "data": {                          // 意图分析结果
    "intent_type": string,           // "RAG" 或 "CHITCHAT"
    "reason": string,                // 分类理由
    "reply_text": string,            // CHITCHAT 直接回复
    "standalone_query": string,      // 独立查询（上下文消解后）
    "sub_queries": [string],         // 子问题列表
    "expanded_queries": [string]     // 扩展查询列表
  },
  "message": string                  // 处理消息
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 处理是否成功 |
| data.intent_type | string | 意图类型："RAG" 或 "CHITCHAT" |
| data.reason | string | 意图分类的理由说明 |
| data.reply_text | string | CHITCHAT 意图时的直接回复文本 |
| data.standalone_query | string | 经过上下文消解后的独立查询 |
| data.sub_queries | array | 复杂问题拆分的子查询列表 |
| data.expanded_queries | array | 同义扩展的查询变体列表 |
| message | string | 处理结果说明 |

---

#### 错误响应

**参数验证失败** (HTTP 422):
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "query"],
      "msg": "String should have at least 1 character",
      "input": "",
      "url": "https://errors.pydantic.dev/..."
    }
  ]
}
```

**LLM 处理失败** (HTTP 422):
```json
{
  "detail": "Intent analysis failed: <错误信息>"
}
```

**服务器错误** (HTTP 500):
```json
{
  "detail": "Internal server error: <错误信息>"
}
```

---

## 使用示例

### 示例 1: CHITCHAT 意图（日常寒暄）

**请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/intent/process" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "你好，今天天气怎么样？",
    "history": []
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "intent_type": "CHITCHAT",
    "reason": "用户在进行日常寒暄，询问天气，属于非知识库检索类的闲聊范畴",
    "reply_text": "你好！作为一个人工智能，我无法直接感知实时的天气变化，不过你可以告诉我你所在的城市，我可以帮你查询一下最新的天气预报哦！",
    "standalone_query": "你好，今天天气怎么样？",
    "sub_queries": [],
    "expanded_queries": []
  },
  "message": "Chitchat intent detected - direct reply provided"
}
```

**特点**:
- ✅ 直接返回友好回复文本
- ✅ 不触发知识库检索

---

### 示例 2: RAG 意图（简单查询）

**请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/intent/process" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是机器学习？",
    "history": []
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "intent_type": "RAG",
    "reason": "用户询问关于机器学习的定义，属于需要检索专业知识库的范畴",
    "reply_text": "",
    "standalone_query": "什么是机器学习？",
    "sub_queries": [],
    "expanded_queries": [
      "机器学习的概念与定义",
      "Machine Learning 定义与原理"
    ]
  },
  "message": "RAG intent detected - retrieval queries generated"
}
```

**特点**:
- ✅ 识别为 RAG 意图，需要检索知识库
- ✅ 简单问题不拆分子问题（`sub_queries` 为空数组）
- ✅ 生成 1-2 个同义扩展查询
- ✅ 返回检索词供后续向量库检索使用

---

### 示例 3: RAG 意图（中等复杂度 + 上下文消解）

**请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/intent/process" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "intent_type": "RAG",
    "reason": "用户要求对比 A 公司与 B 公司的净利润及负债情况，涉及具体的财务数据检索",
    "reply_text": "",
    "standalone_query": "对比 A 公司 2025 年年报中的净利润与 B 公司的净利润，并查询两家公司的负债情况",
    "sub_queries": [
      "A 公司 2025 年净利润与负债情况",
      "B 公司 2025 年净利润与负债情况"
    ],
    "expanded_queries": [
      "A公司与B公司盈利能力及负债率对比分析",
      "A公司 B公司 净利润 资产负债表 数据对比"
    ]
  },
  "message": "RAG intent detected - retrieval queries generated"
}
```

**特点**:
- ✅ **上下文消解**: "它" 正确解析为 "A 公司 2025 年年报"
- ✅ **子问题拆分**: 复杂问题拆分为 2 个独立子查询
- ✅ **同义扩展**: 生成专业财务术语变体
- ✅ **多路检索**: 生成多条检索路径，提升召回率

---

### 示例 4: RAG 意图（复杂查询 - 多维度对比）

**请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/intent/process" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "对比一下 Python、Java 和 Go 三种语言在并发编程、内存管理和学习曲线方面的差异",
    "history": []
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
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
  },
  "message": "RAG intent detected - retrieval queries generated"
}
```

**特点**:
- ✅ **多维度拆分**: 三语言 × 三维度 → 4 个子问题
- ✅ **充分扩展**: 根据复杂度生成 4 个扩展查询
- ✅ **灵活数量**: 根据问题实际复杂度动态调整
- ✅ **专业术语**: 包含技术术语（goroutine、GC、thread）

---

### 示例 5: 参数验证失败

**请求** (空查询):
```bash
curl -X POST "http://localhost:8000/api/v1/intent/process" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "",
    "history": []
  }'
```

**响应** (HTTP 422):
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "query"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {
        "min_length": 1
      },
      "url": "https://errors.pydantic.dev/2.13/v/string_too_short"
    }
  ]
}
```

---

## 意图类型说明

### CHITCHAT 意图

**触发场景**:
- 日常问候和寒暄
- 简单的情感交流
- 不需要知识库支持的问答
- 打字机测试、功能测试类输入

**处理方式**:
- ✅ 直接生成友好回复文本
- ✅ 不触发知识库检索
- ✅ `reply_text` 包含回复内容
- ✅ `sub_queries` 和 `expanded_queries` 为空数组

---

### RAG 意图

**触发场景**:
- 需要专业知识库支持的问题
- 涉及具体数据和事实的查询
- 复杂的对比、分析类问题
- 需要文档检索的场景

**处理方式**:
- ✅ 进行上下文消解（结合历史对话）
- ✅ 根据复杂度灵活拆分问题（0-5 个子查询）
- ✅ 根据需求灵活生成扩展查询（0-4 个）
- ✅ 返回检索词供后续向量库检索使用
- ✅ `reply_text` 为空字符串

**智能拆分规则**:
- 简单问题（单一事实查询）：`sub_queries` 为空数组
- 中等问题（2-3个维度）：拆分为 2-3 个子问题
- 复杂问题（多维度对比/分析）：拆分为 3-5 个子问题

**智能扩展规则**:
- 简单常见词：1-2 个扩展变体
- 专业术语/多义词：2-3 个扩展变体
- 跨领域/多概念：3-4 个扩展变体

**多路检索词生成**:
1. **独立查询**: 上下文消解后的完整查询
2. **子问题**: 复杂问题的拆分（如对比类问题）
3. **扩展查询**: 同义词和专业术语变体

**优势**:
- 提升向量库召回率
- 多角度覆盖查询意图
- 支持复杂场景的精细化检索

---

## 数据模型

### IntentRequest (请求模型)

```python
{
  "query": str,           # 用户查询，最少 1 字符
  "history": [            # 历史对话列表
    {
      "role": str,        # "user" 或 "assistant"
      "content": str      # 消息内容
    }
  ]
}
```

### IntentResponse (意图响应模型)

```python
{
  "intent_type": "RAG" | "CHITCHAT,    # 意图类型
  "reason": str,                        # 分类理由
  "reply_text": str,                    # CHITCHAT 回复文本
  "standalone_query": str,              # 独立查询
  "sub_queries": [str],                 # 子问题列表（0-5个，根据复杂度）
  "expanded_queries": [str]             # 扩展查询列表（0-4个，根据需求）
}
```

### APIResponse (API 响应模型)

```python
{
  "success": bool,                      # 处理是否成功
  "data": IntentResponse | null,        # 意图分析结果
  "message": str                        # 处理消息
}
```

---

## 集成指南

### Python 示例

```python
import requests

# API 端点
url = "http://localhost:8000/api/v1/intent/process"

# 请求数据
data = {
    "query": "什么是机器学习？",
    "history": []
}

# 发送请求
response = requests.post(url, json=data)

# 解析响应
result = response.json()

if result["success"]:
    intent_type = result["data"]["intent_type"]
    
    if intent_type == "CHITCHAT":
        print("回复:", result["data"]["reply_text"])
    else:  # RAG
        print("检索词:", result["data"]["standalone_query"])
        print("子查询:", result["data"]["sub_queries"])
        print("扩展查询:", result["data"]["expanded_queries"])
        
        # 使用检索词进行向量库检索
        all_queries = [result["data"]["standalone_query"]] + \
                      result["data"]["sub_queries"] + \
                      result["data"]["expanded_queries"]
        
        # 调用你的向量数据库进行检索
        # retrieval_results = vector_db.search(all_queries)
```

### JavaScript 示例

```javascript
// API 端点
const url = "http://localhost:8000/api/v1/intent/process";

// 请求数据
const data = {
  query: "什么是机器学习？",
  history: []
};

// 发送请求
fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify(data)
})
.then(response => response.json())
.then(result => {
  if (result.success) {
    const intentType = result.data.intent_type;
    
    if (intentType === "CHITCHAT") {
      console.log("回复:", result.data.reply_text);
    } else {
      console.log("检索词:", result.data.standalone_query);
      console.log("子查询:", result.data.sub_queries);
      console.log("扩展查询:", result.data.expanded_queries);
      
      // 使用检索词进行向量库检索
      const allQueries = [
        result.data.standalone_query,
        ...result.data.sub_queries,
        ...result.data.expanded_queries
      ];
      
      // 调用你的向量数据库进行检索
      // const retrievalResults = vectorDb.search(allQueries);
    }
  }
});
```

---

## 最佳实践

### 1. 使用历史对话

对于包含指代词的查询，提供历史对话以提升消解准确率：

```json
{
  "query": "它的价格是多少？",
  "history": [
    {"role": "user", "content": "我想了解 iPhone 15"},
    {"role": "assistant", "content": "好的，iPhone 15 是苹果公司..."}
  ]
}
```

**效果**: "它" → "iPhone 15"

---

### 2. 控制历史长度

建议历史对话不超过 5-10轮，避免 token 过多：

```json
{
  "query": "...",
  "history": [
    // 最近 5轮对话即可
  ]
}
```

---

### 3. 错误处理

处理可能出现的错误：

```python
try:
    response = requests.post(url, json=data, timeout=120)
    result = response.json()
    
    if response.status_code == 422:
        # 参数验证错误
        print("验证失败:", result["detail"])
    elif response.status_code == 500:
        # 服务器错误
        print("服务器错误:", result["detail"])
    else:
        # 处理结果
        ...
        
except requests.Timeout:
    print("请求超时，LLM 处理耗时较长")
except requests.ConnectionError:
    print("连接失败，检查服务是否启动")
```

---

### 4. 超时设置

由于 LLM 处理可能耗时，建议设置较长超时：

```python
# 建议 120 秒超时
response = requests.post(url, json=data, timeout=120)
```

---

## 交互式文档

### Swagger UI

访问地址: `http://localhost:8000/docs`

**功能**:
- 交互式 API 测试
- 参数自动验证
- 实时查看响应
- 模型定义查看

---

### ReDoc

访问地址: `http://localhost:8000/redoc`

**功能**:
- 更友好的文档展示
- 三栏布局
- 详细的数据模型说明
- 搜索功能

---

## 性能指标

### 响应时间

| 查询类型 | 平均响应时间 | 说明 |
|---------|-------------|------|
| CHITCHAT | 2-4 秒 | 直接 LLM 生成回复 |
| RAG（简单） | 3-5 秒 | 查询扩展 + 模拟检索 |
| RAG（复杂） | 5-8 秒 | 上下文消解 + 子问题拆分 |

**影响因素**:
- LLM 模型推理速度
- 查询复杂度
- 历史对话长度
- vLLM/OpenAI API 响应速度

---

### 并发支持

- 异步架构（AsyncOpenAI）
- FastAPI 原生异步支持
- 建议并发数：10-20

---

## 常见问题

### Q1: 如何判断意图类型？

查看响应中的 `intent_type` 字段：
- `"CHITCHAT"`: 闲聊，直接使用 `reply_text`
- `"RAG"`: 需检索，使用 `standalone_query` 等检索词

---

### Q2: 如何获取检索词？

RAG 意图下，使用以下字段作为检索词：
- `standalone_query`: 上下文消解后的完整查询
- `sub_queries`: 子问题列表（如有）
- `expanded_queries`: 同义扩展列表

---

### Q3: 如何使用检索词进行向量库检索？

当前 API 返回意图分析结果和检索词，需自行调用向量数据库。RAG 意图下，使用以下字段作为检索词：

```python
# 收集所有检索词
all_queries = [
    result["data"]["standalone_query"],  # 上下文消解后的完整查询
    *result["data"]["sub_queries"],      # 子问题列表
    *result["data"]["expanded_queries"]  # 同义扩展列表
]

# 调用向量数据库
retrieval_results = await vector_db.search(all_queries)
```

---

### Q4: 支持哪些 LLM？

支持所有兼容 OpenAI API 的服务：
- vLLM 本地模型
- OpenAI GPT 系列
- 其他兼容 API（如 Azure OpenAI）

---

## 版本历史

### v1.0.0 (当前版本)

**功能**:
- ✅ 意图分类（CHITCHAT/RAG）
- ✅ 上下文消解
- ✅ 子问题拆分
- ✅ 同义扩展
- ✅ 多路检索词生成
- ✅ 完整的 API 文档

**技术栈**:
- FastAPI 0.109+
- Pydantic v2
- AsyncOpenAI
- Python 3.10+

---

## 技术支持

- **文档**: [README.md](../README.md)
- **快速启动**: [QUICK_START.md](../QUICK_START.md)
- **测试报告**: [TEST_REPORT.md](../TEST_REPORT.md)
- **实施方案**: [plan.md](../plan.md)

---

## 许可证

MIT License

---

**文档版本**: 1.0.0  
**最后更新**: 2026-07-06  
**API 版本**: v1