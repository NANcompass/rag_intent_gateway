# 🤖 RAG Intent Gateway

一个基于 FastAPI 和大语言模型的 RAG（检索增强生成）前置意图处理流水线。

## 📋 项目简介

本项目是一个智能的 RAG 前置处理系统，能够在不查阅知识库的前提下，分析用户输入的 Query 并结合历史对话，将其精细化分类为 **RAG（检索）** 或 **CHITCHAT（闲聊）**，并对检索类问题进行多路重写与扩展，以最大化后端向量库的召回率。

### 核心功能

- **意图分类**: 判断查询是否需要检索知识库（RAG）或为日常寒暄（CHITCHAT）
- **上下文消解**: 结合历史对话补全指代词和省略成分
- **子问题拆分**: 将复杂问题拆分为多个独立的子查询
- **同义扩展**: 生成多种语义等价的检索词变体

### 技术栈

- **Python 3.10+**
- **FastAPI** - 高性能 Web 框架
- **Pydantic v2** - 严格的数据验证
- **OpenAI AsyncOpenAI** - 异步 LLM 客户端
- **Uvicorn** - ASGI 服务器

## 🏗️ 项目结构

```
rag_intent_gateway/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── intent.py       # 意图处理路由
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # 配置管理
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic 数据模型
│   └── services/
│       ├── __init__.py
│       └── llm_service.py      # LLM 调用服务
├── tests/                      # 测试文件
├── main.py                     # FastAPI 启动入口
├── main_mcp.py                 # MCP 服务启动入口
├── .env.example                # 环境变量示例
├── requirements.txt            # Python 依赖
└── README.md                   # 本文档
```

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.10 或更高版本：

```bash
python --version
```

### 2. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

复制环境变量模板并填入配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 OpenAI API 密钥：

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

### 4. 运行应用

#### 方式 A: 运行 FastAPI 服务

```bash
# 方式一：使用 Python 直接运行（推荐）
python main.py

# 方式二：使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

应用将在 `http://localhost:8000` 启动。

#### 方式 B: 运行 MCP 服务

MCP (Model Context Protocol) 服务提供标准的工具接口，可用于 Dify 等平台集成：

```bash
# 方式一：直接运行
python main_mcp.py

# 方式二：自定义主机和端口
MCP_HOST=0.0.0.0 MCP_PORT=8022 python main_mcp.py
```

MCP 服务将在 `http://localhost:8022/mcp` 启动。

**MCP 配置：**

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `MCP_HOST` | `0.0.0.0` | MCP 服务主机 |
| `MCP_PORT` | `8022` | MCP 服务端口 |

**MCP 工具：**

1. **analyze_intent**: 分析用户查询意图并执行查询重写
   - 参数: `query` (查询文本), `history` (对话历史，可选)
   - 返回: 意图类型、独立查询、子查询、扩展查询

2. **health_check**: 检查服务健康状态

### 5. 访问文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health
- **MCP 端点**: http://localhost:8022/mcp

## 📖 API 使用指南

### 核心接口：意图处理

**端点**: `POST /api/v1/intent/process`

**请求体**:

```json
{
  "query": "把它和 B 公司的净利润对比一下",
  "history": [
    {
      "role": "user",
      "content": "我想了解一下 A 公司的年报"
    },
    {
      "role": "assistant", 
      "content": "好的，我已经为您准备好了 A 公司 2025 年的财务报告。"
    }
  ]
}
```

**参数说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | ✅ | 当前用户查询 |
| history | array | ❌ | 历史对话列表，包含 role 和 content |

**响应示例（RAG 意图 - 中等复杂度）**:

```json
{
  "success": true,
  "data": {
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
  },
  "message": "RAG intent detected - retrieval queries generated"
}
```

**响应示例（RAG 意图 - 简单查询）**:

```json
{
  "success": true,
  "data": {
    "intent_type": "RAG",
    "reason": "用户询问机器学习的定义，属于知识库检索范畴",
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

**响应示例（RAG 意图 - 复杂查询）**:

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

**响应示例（CHITCHAT 意图）**:

```json
{
  "success": true,
  "data": {
    "intent_type": "CHITCHAT",
    "reason": "日常打招呼与寒暄，无需检索知识库",
    "reply_text": "嗨！我是一个 AI 助手，随时准备好为您提供帮助了！今天有什么我可以帮您的吗？",
    "standalone_query": "哈喽，你今天心情怎么样？",
    "sub_queries": [],
    "expanded_queries": []
  },
  "message": "Chitchat intent detected - direct reply provided"
}
```

### 使用 curl 测试

```bash
# RAG 意图测试
curl -X POST "http://localhost:8000/api/v1/intent/process" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "把它和 B 公司的净利润对比一下",
    "history": [
      {"role": "user", "content": "我想了解一下 A 公司的年报"},
      {"role": "assistant", "content": "好的，我已经为您准备好了 A 公司 2025 年的财务报告。"}
    ]
  }'

# CHITCHAT 意图测试
curl -X POST "http://localhost:8000/api/v1/intent/process" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "哈喽，你今天心情怎么样？",
    "history": []
  }'
```

## 🔧 配置说明

### 环境变量

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| OPENAI_API_KEY | ✅ | - | OpenAI API 密钥 |
| OPENAI_BASE_URL | ❌ | `https://api.openai.com/v1` | API 基础 URL（支持自定义端点） |
| OPENAI_MODEL | ❌ | `gpt-4o` | 使用的模型 |
| OPENAI_TEMPERATURE | ❌ | `0.3` | 生成温度（0.0-2.0） |
| OPENAI_MAX_TOKENS | ❌ | `2000` | 最大生成令牌数 |
| APP_NAME | ❌ | `RAG Intent Gateway` | 应用名称 |
| APP_VERSION | ❌ | `1.0.0` | 应用版本 |
| DEBUG | ❌ | `false` | 调试模式 |
| API_PREFIX | ❌ | `/api/v1` | API 路由前缀 |

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_api.py

# 运行并显示覆盖率
pytest --cov=app tests/

# 详细输出
pytest -v tests/
```

### 测试覆盖

- **test_models.py**: Pydantic 数据模型验证测试
- **test_llm_service.py**: LLM 服务调用和解析测试
- **test_api.py**: API 端点集成测试

## 🔍 核心组件说明

### 1. Pydantic 数据模型 (`app/models/schemas.py`)

定义了严格的数据结构：

- `IntentType`: 意图类型枚举（RAG/CHITCHAT）
- `HistoryMessage`: 历史消息模型
- `IntentRequest`: API 请求模型
- `IntentResponse`: LLM 返回的结构化响应
- `APIResponse`: API 响应包装器

### 2. LLM 服务 (`app/services/llm_service.py`)

核心功能：

- 使用 `AsyncOpenAI` 异步客户端
- 强制 JSON 格式输出（`response_format={"type": "json_object"}`）
- 自动解析为 Pydantic 模型
- 完整的错误处理

### 3. 意图处理路由 (`app/api/v1/intent.py`)

业务逻辑：

- 接收查询和历史对话
- 调用 LLM 进行意图分析
- 根据意图类型分支处理：
  - **CHITCHAT**: 直接返回回复文本
  - **RAG**: 生成多路检索词供后续检索使用

## 🎯 使用场景

### 场景 1: 复杂查询的多路检索

**用户输入**: "把它和 B 公司的净利润对比一下，另外告诉我它们的负债情况"

**系统处理**:
1. 识别为 RAG 意图
2. 上下文消解："它" → "A 公司"
3. 拆分子问题：
   - "A 公司 2025 年净利润及负债情况"
   - "B 公司最新净利润及负债情况"
4. 生成扩展查询：
   - "A公司 B公司 财务报表 净利润 对比"
   - "A公司 B公司 资产负债率 盈利能力分析"

### 场景 2: 日常寒暄的智能回复

**用户输入**: "哈喽，你今天心情怎么样？"

**系统处理**:
1. 识别为 CHITCHAT 意图
2. 直接生成回复："嗨！我是一个 AI 助手，随时准备好为您提供帮助了！"
3. 不触发知识库检索

## 📊 架构流程图

```
┌────────────────────────┐
│   User Query (原始输入)  │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│   History Context      │
│   (多轮对话历史，可选)   │
└───────────┬────────────┘
            │
            ▼
┌──────────────────────────────────────┐
│        Intent Analyzer LLM           │
│     (执行: 路由/指代消解/多路扩展)    │
└──────────────────┬───────────────────┘
                   │
                   ▼
          ┌────────────────┐
          │ Structured JSON│
          └───────┬────────┘
                  │
       ┌──────────┴──────────┐
       ▼                     ▼
【意图 A: CHITCHAT】   【意图 B: RAG】
直接回复文本           多路并发检索
不触发知识库           极大提升召回率
```

## 🛠️ 开发指南

### 代码风格

项目使用以下工具保证代码质量：

- **Black**: 代码格式化
- **isort**: 导入排序
- **flake8**: 代码检查
- **mypy**: 类型检查

```bash
# 格式化代码
black app/ tests/

# 排序导入
isort app/ tests/

# 类型检查
mypy app/

# 代码检查
flake8 app/ tests/
```

### 扩展开发

#### 添加新的意图类型

1. 在 `IntentType` 枚举中添加新类型
2. 更新 `INTENT_SYSTEM_PROMPT` 中的提示词
3. 在路由中添加对应的处理逻辑

#### 集成真实检索系统

在 `app/api/v1/intent.py` 中，使用返回的检索词进行真实检索：

```python
# 获取响应中的检索词
response = await llm_service.analyze_intent(query, history)

if response.intent_type == IntentType.RAG:
    # 收集所有检索词
    all_queries = [response.standalone_query] + response.sub_queries + response.expanded_queries
    
    # 调用你的向量数据库客户端
    results = await vector_db.search(all_queries)
    return results
```

## 📝 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请提交 Issue。