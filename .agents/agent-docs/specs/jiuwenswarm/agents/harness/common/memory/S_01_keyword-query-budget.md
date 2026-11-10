---
author: Arshia Zakeri Rad
author_email: zrr.arshia@gmail.com
modules:
- jiuwenswarm/agents/harness/common/memory
files:
- jiuwenswarm/agents/harness/common/memory/internal.py
- jiuwenswarm/agents/harness/common/memory/config.py
- jiuwenswarm/agents/harness/common/memory/manager.py
- tests/unit_tests/agentserver/memory/test_memory_search_scoring.py
updated: '2026-11-06'
id: S_01_keyword-query-budget
title: 本地关键词查询预算契约
type: S
status: active
---

# 本地关键词查询预算契约

- 配置路径为 `memory.query.keywordMaxTerms`，默认值 64；允许 1–256 的整数。
- `10` 提供旧预算兼容行为。禁止布尔、浮点、字符串、null、零及负数的静默转换。
- 默认/程序化 `MemorySettings`、YAML 读取及显式 query 覆盖均在设置生效前校验。
- 预算仅限制本地 FTS 词项数；不截断传给 embedding 的完整问题，也不影响外接
  agent-memory provider 的独立检索参数。
- 原正则词项按输入顺序逐项引用并以 OR 连接；否定词、数值和标识符组成词不被
  自动删除。并不实现布尔否定语义、实体识别、普通词过滤或关键词重要性选择。
- 超长问题仍按相同有限词项预算构造 SQL；预算并非任意单个词的字符长度上限。
- 来源隔离、limit 前过滤、BM25 原生次序、相对分数归一及失败路降级保持原契约。
