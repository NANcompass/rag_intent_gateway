# 📚 RAG Intent Gateway 文档中心

欢迎访问 RAG Intent Gateway 文档中心。这里提供了完整的项目文档，帮助你快速了解和使用本系统。

---

## 📖 文档索引

### 1. 快速开始

- **[README.md](../README.md)** - 项目完整文档
  - 项目介绍和功能特性
  - 安装和配置指南
  - 详细的使用说明
  - 开发和测试指南

- **[QUICK_START.md](../QUICK_START.md)** - 快速启动指南
  - 环境准备
  - 一键启动步骤
  - 快速测试方法
  - 常见问题解答

---

### 2. API 文档

- **[API.md](API.md)** - 完整的 API 文档
  - API 端点详细说明
  - 请求/响应格式
  - 使用示例和最佳实践
  - 错误处理指南

**在线文档**:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

### 3. 架构设计

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - 系统架构文档
  - 整体架构设计
  - 模块划分和职责
  - 核心算法实现
  - 技术选型说明
  - 性能优化策略
  - 扩展性设计

---

### 4. 测试报告

- **[TEST_REPORT.md](../TEST_REPORT.md)** - 功能测试报告
  - 测试环境和配置
  - 单元测试结果
  - API 功能测试
  - 性能指标分析

---

### 5. 实施方案

- **[plan.md](../plan.md)** - 原始实施方案
  - 方案目标
  - 核心架构设计
  - System Prompt 模板
  - 技术要求说明

---

### 6. 项目总结

- **[FINAL_SUMMARY.md](../FINAL_SUMMARY.md)** - 项目完成总结
  - 测试结果汇总
  - 功能验证清单
  - 核心能力总结
  - 使用指南

---

## 🚀 快速导航

### 我想快速启动服务

→ 阅读 [QUICK_START.md](../QUICK_START.md)

### 我想了解 API 接口

→ 阅读 [API.md](API.md) 或访问 http://localhost:8000/docs

### 我想了解系统架构

→ 阅读 [ARCHITECTURE.md](ARCHITECTURE.md)

### 我想查看测试结果

→ 阅读 [TEST_REPORT.md](../TEST_REPORT.md)

### 我想查看项目文档

→ 阅读 [README.md](../README.md)

---

## 📂 文档结构

```
docs/
├── README.md           # 文档索引（本文件）
├── API.md             # API 接口文档
└── ARCHITECTURE.md    # 架构设计文档

项目根目录/
├── README.md          # 完整项目文档
├── QUICK_START.md     # 快速启动指南
├── TEST_REPORT.md     # 测试报告
├── FINAL_SUMMARY.md   # 项目总结
└── plan.md            # 实施方案
```

---

## 🔧 开发者文档

### 代码结构

```
app/
├── main.py              # FastAPI 应用入口
├── api/v1/intent.py     # 意图处理路由
├── services/
│   └── llm_service.py   # LLM 服务
├── models/
│   └── schemas.py       # 数据模型
└── core/
    └── config.py        # 配置管理
```

### 测试套件

```
tests/
├── test_api.py          # API 测试
├── test_llm_service.py  # LLM 服务测试
└── test_models.py       # 数据模型测试
```

---

## 📊 核心功能

### 意图分类

- **CHITCHAT**: 日常闲聊，直接生成友好回复
- **RAG**: 知识库检索，生成多路检索词

### 查询处理

- **上下文消解**: 解析指代词，补全省略信息
- **子问题拆分**: 复杂问题拆分为独立子查询
- **同义扩展**: 生成专业术语和双语变体

---

## 🎯 使用场景

### 1. 知识库问答系统

```
用户查询 → 意图分析 → 多路检索 → 答案生成
```

### 2. 智能客服机器人

```
用户提问 → 意图识别 → 直接回复或知识检索
```

### 3. RAG 系统前置处理

```
原始查询 → 意图分析 → 检索词优化 → 向量检索
```

---

## 🔗 相关链接

- **FastAPI 官方文档**: https://fastapi.tiangolo.com/
- **Pydantic 文档**: https://docs.pydantic.dev/
- **OpenAI API 文档**: https://platform.openai.com/docs/
- **vLLM 项目**: https://github.com/vllm-project/vllm

---

## 💡 提示

### 推荐阅读顺序

**新手**:
1. [QUICK_START.md](../QUICK_START.md) - 快速上手
2. [API.md](API.md) - 了解接口
3. [README.md](../README.md) - 深入了解

**开发者**:
1. [ARCHITECTURE.md](ARCHITECTURE.md) - 架构设计
2. [API.md](API.md) - API 详细说明
3. [TEST_REPORT.md](../TEST_REPORT.md) - 测试验证

**运维人员**:
1. [QUICK_START.md](../QUICK_START.md) - 部署启动
2. [ARCHITECTURE.md](ARCHITECTURE.md) - 性能优化
3. [API.md](API.md) - 监控指标

---

## ❓ 常见问题

### Q: 如何启动服务？

```bash
python main.py
```

### Q: 如何配置 LLM？

编辑 `.env` 文件，配置 `OPENAI_BASE_URL` 和 `OPENAI_MODEL`

### Q: 如何集成真实向量库？

修改 `app/api/v1/intent.py` 中的 `simulate_retrieval` 函数

### Q: API 文档在哪里？

访问 http://localhost:8000/docs

---

## 📝 文档更新

- **README.md**: 2026-07-02
- **API.md**: 2026-07-02
- **ARCHITECTURE.md**: 2026-07-02
- **QUICK_START.md**: 2026-07-02
- **TEST_REPORT.md**: 2026-07-01

---

## 📞 技术支持

如有问题或建议，请查阅相关文档或提交 Issue。

---

**文档版本**: 1.0.0  
**最后更新**: 2026-07-02  
**维护者**: RAG Intent Gateway Team