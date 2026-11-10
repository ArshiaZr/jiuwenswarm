---
title: 实施与决策 F索引
author: Arshia Zakeri Rad
author_email: zrr.arshia@gmail.com
generated: true
---

# 实施与决策 F索引

由 sync_documents.py 从文档 frontmatter 自动生成；请修改源文档后重新生成，不手工维护。

共 2 篇文档，按模块分组；跨模块文档在各相关分组展示，总数按文档去重。

## 模块导航

| 模块 | 文档数 |
|---|---|
| [jiuwenswarm/agents/harness/common/memory](#module-1) | 1 |
| [scripts](#module-2) | 1 |

<a id="module-1"></a>

## jiuwenswarm/agents/harness/common/memory

| ID / 文档 | 类型 | 标题 | 作者 | 模块 | 代码文件 | 关联 D |
|---|---|---|---|---|---|---|
| [F_20261106_0553_memory-keyword-budget](F_20261106_0553_memory-keyword-budget.md) | F | 可配置的本地记忆关键词预算 | Arshia Zakeri Rad | jiuwenswarm/agents/harness/common/memory | jiuwenswarm/agents/harness/common/memory/internal.py, jiuwenswarm/agents/harness/common/memory/config.py, jiuwenswarm/agents/harness/common/memory/manager.py, tests/unit_tests/agentserver/memory/test_memory_search_scoring.py | 无独立 D：用户已明确授权关键词修复；常规有界预算修复，不补造独立设计或批准记录。 |

<a id="module-2"></a>

## scripts

| ID / 文档 | 类型 | 标题 | 作者 | 模块 | 代码文件 | 关联 D |
|---|---|---|---|---|---|---|
| [F_20261111_0005_native-benchmark-ingestion](F_20261111_0005_native-benchmark-ingestion.md) | F | Native benchmark ingestion launcher | Arshia Zakeri Rad | scripts | scripts/ingest_memory_benchmark.py, docs/en/Memory.md, docs/zh/记忆.md | 无独立 D：用户明确要求仅在 fork 的 exp 分支增加评测前原生数据摄入；复用跨仓 API，不另造抽取器。 |
