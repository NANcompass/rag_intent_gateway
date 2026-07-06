# RAG Intent Gateway 架构设计文档

## 1. 系统架构概览

### 1.1 整体架构

RAG Intent Gateway 采用分层架构设计，从上到下分为：

```
┌─────────────────────────────────────────────┐
│           Presentation Layer                │
│         (FastAPI Routes & API)              │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────┴───────────────────────┐
│          Business Logic Layer               │
│      (Intent Processing & Routing)          │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────┴───────────────────────┐
│           Service Layer                     │
│      (LLM Service & Retrieval)              │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────┴───────────────────────┐
│            Data Layer                       │
│    (Pydantic Models & Config)               │
└─────────────────────────────────────────────┘
```

---

### 1.2 核心流程图

```
用户请求 (Query + History)
        ↓
    ┌──────────────┐
    │ FastAPI 路由 │
    │  接收请求     │
    └───────┬──────┘
            ↓
    ┌──────────────┐
    │  参数验证     │
    │ (Pydantic)   │
    └───────┬──────┘
            ↓
    ┌──────────────┐
    │ LLM 服务调用  │
    │ (AsyncOpenAI)│
    └───────┬──────┘
            ↓
    ┌──────────────┐
    │ JSON 解析     │
    │  + 验证      │
    └───────┬──────┘
            ↓
    ┌──────────────────────┐
    │   意图分支判断         │
    └─────────┬────────────┘
              │
    ┌─────────┴─────────┐
    ↓                   ↓
┌──────────┐      ┌──────────┐
│CHITCHAT  │      │   RAG    │
│直接回复   │      │多路检索   │
└────┬─────┘      └─────┬────┘
     ↓                  ↓
 ┌─────────┐      ┌──────────┐
 │返回回复 │      │生成检索词 │
 │  文本   │      │+模拟结果  │
 └────┬────┘      └─────┬────┘
     ↓                  ↓
     └────────┬─────────┘
              ↓
      ┌──────────────┐
      │  API 响应     │
      └──────────────┘
```

---

## 2. 模块设计

### 2.1 目录结构

```
rag_intent_gateway/
├── main.py                    # 应用入口（启动点）
├── app/                       # 应用核心代码
│   ├── main.py               # FastAPI 应用定义
│   ├── api/                  # API 路由层
│   │   └── v1/
│   │       └── intent.py     # 意图处理路由
│   ├── core/                 # 核心配置
│   │   └── config.py         # 配置管理
│   ├── models/               # 数据模型
│   │   └── schemas.py        # Pydantic 模型定义
│   └── services/             # 服务层
│       └── llm_service.py    # LLM 调用服务
├── tests/                    # 测试套件
│   ├── test_api.py           # API 测试
│   ├── test_llm_service.py   # LLM 服务测试
│   └── test_models.py        # 模型测试
├── docs/                     # 文档目录
│   ├── API.md               # API 文档
│   └── ARCHITECTURE.md      # 架构设计文档
├── .env                      # 环境配置
├── requirements.txt          # 依赖列表
└── README.md                 # 项目文档
```

---

### 2.2 模块职责

#### Presentation Layer (API 路由层)

**文件**: `app/api/v1/intent.py`

**职责**:
- 接收 HTTP 请求
- 参数验证和解析
- 业务逻辑编排
- 响应格式化

**核心函数**:
```python
@router.post("/process")
async def process_intent(request: IntentRequest) -> APIResponse:
    """处理意图分析请求"""
    # 1. 调用 LLM 服务
    intent_response = await llm_service.analyze_intent(...)
    
    # 2. 根据意图类型分支处理
    if intent_response.intent_type == IntentType.CHITCHAT:
        # 直接返回回复文本
        return APIResponse(...)
    else:
        # 生成多路检索词 + 模拟检索结果
        retrieval_results = simulate_retrieval(...)
        return APIResponse(...)
```

---

#### Service Layer (服务层)

**文件**: `app/services/llm_service.py`

**职责**:
- 管理 AsyncOpenAI 客户端
- 构建 System Prompt
- 调用 LLM API
- JSON 解析和验证

**核心类**:
```python
class LLMService:
    def __init__(self):
        """初始化 AsyncOpenAI 客户端"""
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=120.0
        )
    
    async def analyze_intent(self, query, history) -> IntentResponse:
        """分析意图并返回结构化结果"""
        # 1. 构建 System Prompt
        system_prompt = INTENT_SYSTEM_PROMPT
        user_prompt = self._build_user_prompt(query, history)
        
        # 2. 调用 LLM
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # 3. 解析和验证 JSON
        data = json.loads(response.choices[0].message.content)
        return IntentResponse(**data)
```

---

#### Data Layer (数据模型层)

**文件**: `app/models/schemas.py`

**职责**:
- 定义严格的数据结构
- 参数验证规则
- 类型约束

**核心模型**:
```python
class IntentType(str, Enum):
    """意图类型枚举"""
    RAG = "RAG"
    CHITCHAT = "CHITCHAT"

class IntentResponse(BaseModel):
    """LLM 结构化响应"""
    intent_type: IntentType
    reason: str
    reply_text: str = ""
    standalone_query: str
    sub_queries: List[str] = []
    expanded_queries: List[str] = []
```

---

## 3. 核心算法设计

### 3.1 System Prompt 设计策略

#### 设计原则

1. **强约束输出**: 强制 JSON 格式，无 Markdown 标记
2. **单次推理**: 一次完成 4 项任务（路由、消解、拆分、扩展）
3. **示例驱动**: 提供高质量示例引导模型
4. **明确任务**: 清晰定义每个步骤的职责

#### Prompt 结构

```
# Role
定义系统角色和职责

# Constraints
强制约束（JSON 格式、无标记）

# Tasks
四个核心任务的详细说明

# Output Format
JSON 输出模板

# Examples
高质量示例（RAG 和 CHITCHAT）

# 实际输入
History + Query
```

#### 关键特性

**上下文消解**:
```
【上下文消解 (standalone_query)】
结合 history 补全当前 Query 中含糊不清的指代
（如他、她、它、那个、上一个）或省略成分。
如果没有历史，保持原样。
```

**子问题拆分**:
```
【子问题拆分 (sub_queries)】
如果问题包含多重对比或复杂逻辑，
将其拆分为 2-3 个独立的、单一维度的具体子检索词。
如果是简单问题，放空数组。
```

**同义扩展**:
```
【同义变体扩展 (expanded_queries)】
针对核心检索目标，换 2 种更符合专业文档
或知识库术语的表达方式。
如果是闲聊，放空数组。
```

---

### 3.2 多路检索词生成算法

#### 输入
- `standalone_query`: 上下文消解后的查询
- `sub_queries`: 拆分的子问题
- `expanded_queries`: 同义扩展变体

#### 处理流程

```python
def generate_retrieval_queries(intent_response):
    """生成多路检索词"""
    all_queries = []
    
    # 1. 添加独立查询（核心）
    all_queries.append(intent_response.standalone_query)
    
    # 2. 添加子问题（精细化）
    all_queries.extend(intent_response.sub_queries)
    
    # 3. 添加扩展查询（广度）
    all_queries.extend(intent_response.expanded_queries)
    
    return all_queries
```

#### 检索策略

| 查询类型 | 作用 | 示例 |
|---------|------|------|
| 独立查询 | 核心意图覆盖 | "对比 A 公司和 B 公司的净利润" |
| 子问题 | 精细化检索 | "A 公司净利润", "B 公司净利润" |
| 扩展查询 | 语义扩展 | "盈利能力对比分析", "财务数据对比" |

**优势**:
- ✅ 提升向量库召回率（多角度）
- ✅ 支持复杂查询的精细化处理
- ✅ 兼顾专业术语和通俗表达

---

### 3.3 分支处理逻辑

#### CHITCHAT 分支

```python
if intent_response.intent_type == IntentType.CHITCHAT:
    # 直接返回友好回复
    return APIResponse(
        success=True,
        data=intent_response,
        message="Chitchat intent detected - direct reply provided",
        retrieval_results=None  # 不触发检索
    )
```

**特点**:
- 无检索开销
- 直接 LLM 生成的友好文本
- 适合日常交互场景

---

#### RAG 分支

```python
else:  # IntentType.RAG
    # 生成多路检索词
    all_queries = [
        intent_response.standalone_query,
        *intent_response.sub_queries,
        *intent_response.expanded_queries
    ]
    
    # 模拟检索（可替换为真实向量库）
    retrieval_results = simulate_retrieval(all_queries)
    
    return APIResponse(
        success=True,
        data=intent_response,
        message="RAG intent detected - retrieval queries generated",
        retrieval_results=retrieval_results
    )
```

**特点**:
- 多路检索词生成
- 模拟检索结果
- 可集成真实向量数据库

---

## 4. 技术选型

### 4.1 核心技术栈

| 技术 | 版本 | 选择理由 |
|------|------|---------|
| Python | 3.10+ | 异步支持、类型提示 |
| FastAPI | 0.109+ | 高性能、原生异步、自动文档 |
| Pydantic | v2 | 严格验证、性能提升 |
| AsyncOpenAI | 1.12+ | 异步调用、流式支持 |
| Uvicorn | 0.27+ | ASGI 服务器、生产级 |

---

### 4.2 Pydantic v2 选择理由

**性能优势**:
- 比 v1 快 5-10 倍
- 基于 Rust 的 pydantic-core

**严格验证**:
```python
class IntentRequest(BaseModel):
    query: str = Field(..., min_length=1)  # 强制非空
    history: List[HistoryMessage] = Field(default_factory=list)
```

**类型安全**:
- 完整的类型提示
- IDE 自动补全支持
- 防止运行时错误

---

### 4.3 AsyncOpenAI 选择理由

**异步架构**:
```python
# 异步调用，支持高并发
response = await client.chat.completions.create(...)
```

**兼容性**:
- 支持 vLLM
- 支持 OpenAI API
- 支持其他兼容服务

**强制 JSON**:
```python
response_format={"type": "json_object"}  # 强制 JSON 输出
```

---

## 5. 性能优化

### 5.1 异步架构

**全链路异步**:

```
FastAPI (异步端点)
    ↓
AsyncOpenAI (异步调用)
    ↓
异步响应处理
```

**代码实现**:
```python
@router.post("/process")
async def process_intent(request: IntentRequest):  # 异步端点
    intent_response = await llm_service.analyze_intent(...)  # 异步调用
    return APIResponse(...)
```

**优势**:
- ✅ 高并发支持
- ✅ 非阻塞 I/O
- ✅ 资源利用率高

---

### 5.2 单次 LLM 调用策略

**传统方案** (多次调用):
```
意图分类 (1次) → 上下文消解 (1次) → 查询扩展 (1次) = 3次调用
```

**当前方案** (单次调用):
```
System Prompt 强约束 → 一次性输出结构化 JSON = 1次调用
```

**优势**:
- ✅ 降低延迟（节省 2/3 时间）
- ✅ 降低成本（节省 2/3 token）
- ✅ 上下文一致性更好

---

### 5.3 超时优化

**问题**: LLM 推理可能较慢

**解决**:
```python
self.client = AsyncOpenAI(
    timeout=120.0  # 增加超时到 120 秒
)
```

**建议**:
- vLLM 本地模型：120 秒
- OpenAI API：60 秒
- 其他服务：根据实际调整

---

## 6. 扩展性设计

### 6.1 集成真实向量数据库

**当前**: 模拟检索

**扩展**: 替换函数

```python
# app/api/v1/intent.py

async def real_retrieval(queries: List[str]) -> List[dict]:
    """真实向量数据库检索"""
    # 集成 Milvus / Elasticsearch / Pinecone
    client = VectorDBClient()
    results = await client.search(queries)
    return results

# 在路由中使用
retrieval_results = await real_retrieval(all_queries)
```

---

### 6.2 添加新意图类型

**步骤**:

1. **定义枚举**:
```python
# app/models/schemas.py
class IntentType(str, Enum):
    RAG = "RAG"
    CHITCHAT = "CHITCHAT"
    FAQ = "FAQ"  # 新增类型
```

2. **更新 Prompt**:
```python
# app/services/llm_service.py
INTENT_SYSTEM_PROMPT = """
...
1. 【意图路由】: 判断属于 RAG、CHITCHAT 或 FAQ
...
"""
```

3. **添加处理逻辑**:
```python
# app/api/v1/intent.py
if intent_response.intent_type == IntentType.FAQ:
    # FAQ 专用处理逻辑
    ...
```

---

### 6.3 多语言支持

**扩展**: 添加多语言 Prompt

```python
# app/services/llm_service.py

INTENT_SYSTEM_PROMPT_EN = """
# Role
You are a RAG intent analyzer...

# Tasks
1. Intent Routing: Determine RAG or CHITCHAT...
"""

# 根据用户语言选择 Prompt
if user_language == "en":
    system_prompt = INTENT_SYSTEM_PROMPT_EN
else:
    system_prompt = INTENT_SYSTEM_PROMPT
```

---

## 7. 安全性设计

### 7.1 参数验证

**Pydantic 严格验证**:
```python
class IntentRequest(BaseModel):
    query: str = Field(
        ..., 
        min_length=1,  # 防止空查询
        max_length=1000  # 防止过长查询
    )
```

**效果**:
- ✅ 防止恶意输入
- ✅ 自动返回 422 错误
- ✅ 清晰的错误提示

---

### 7.2 错误处理

**分层捕获**:

```python
try:
    intent_response = await llm_service.analyze_intent(...)
except json.JSONDecodeError:
    raise HTTPException(422, "JSON 解析失败")
except ValidationError:
    raise HTTPException(422, "数据验证失败")
except Exception:
    raise HTTPException(500, "服务器内部错误")
```

---

### 7.3 CORS 配置

**允许跨域**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 8. 测试策略

### 8.1 单元测试

**模型测试** (`test_models.py`):
- Pydantic 验证规则
- 默认值测试
- 边界条件测试

**服务测试** (`test_llm_service.py`):
- Mock LLM API
- JSON 解析测试
- Prompt 构建测试

**API 测试** (`test_api.py`):
- 端点调用测试
- 参数验证测试
- 响应格式测试

---

### 8.2 集成测试

**端到端测试**:
```python
# 启动真实服务
client = TestClient(app)

# 测试 CHITCHAT
response = client.post("/api/v1/intent/process", json={"query": "你好"})
assert response.json()["data"]["intent_type"] == "CHITCHAT"

# 测试 RAG
response = client.post("/api/v1/intent/process", json={"query": "什么是机器学习？"})
assert response.json()["data"]["intent_type"] == "RAG"
```

---

## 9. 部署建议

### 9.1 生产部署

**使用 Uvicorn**:
```bash
# 多 worker 进程
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

**使用 Gunicorn**:
```bash
gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000
```

---

### 9.2 Docker 部署

**Dockerfile**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

**运行**:
```bash
docker build -t rag-intent-gateway .
docker run -p 8000:8000 --env-file .env rag-intent-gateway
```

---

### 9.3 监控指标

**关键指标**:
- API 响应时间（P50, P95, P99）
- LLM 调用成功率
- 意图分类准确率
- 错误率统计

**工具**:
- Prometheus + Grafana
- ELK Stack
- Sentry

---

## 10. 未来优化方向

### 10.1 缓存机制

**意图缓存**:
```python
# 对相似查询缓存意图结果
cache_key = hash(query + str(history))
if cache.has(cache_key):
    return cache.get(cache_key)
```

**优势**:
- 降低 LLM 调用频率
- 提升响应速度
- 降低成本

---

### 10.2 批量处理

**批量请求**:
```python
@router.post("/batch")
async def process_batch(requests: List[IntentRequest]):
    # 并发处理多个请求
    results = await asyncio.gather(
        *[llm_service.analyze_intent(r.query, r.history) for r in requests]
    )
    return results
```

---

### 10.3 流式响应

**流式输出**:
```python
async def stream_intent(query: str):
    # 流式生成意图分析结果
    async for chunk in llm_service.stream_analyze(query):
        yield chunk
```

---

## 总结

RAG Intent Gateway 采用现代异步架构，通过精心设计的 System Prompt 和分层模块化设计，实现了高效、可扩展、易维护的意图处理系统。

**核心优势**:
1. ✅ 单次 LLM 调用，高效低成本
2. ✅ 严格的数据验证，类型安全
3. ✅ 异步架构，高并发支持
4. ✅ 模块化设计，易于扩展
5. ✅ 完整的测试覆盖，质量保证

---

**文档版本**: 1.0.0  
**最后更新**: 2026-07-02