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
updated: '2026-11-10'
id: F_20261106_0553_memory-keyword-budget
title: 可配置的本地记忆关键词预算
type: F
status: implemented
designs: []
design_note: 用户已明确授权关键词修复；常规有界预算修复，不补造独立设计或批准记录。
---

# 可配置的本地记忆关键词预算

## 问题与最终行为

旧 FTS 构造器只取查询的前十个词；自然语言开头可能先耗尽预算，书名、实体或
日期根本没有进入 BM25。例如 Nightingale 问题的书名在第十词之后。
现在原生本地文件记忆默认取 64 个词项，并通过 `memory.query.keywordMaxTerms`
配置。设为 10 可恢复旧预算；合法值是 1–256 的整数，布尔、字符串、浮点、null
及越界值直接拒绝，不默认为零或静默强转。

该预算仅作用于 `_search_keyword` 的 FTS 表达式。语义向量仍使用完整原始问题；
不加入普通词删除、去重、同义词或意图推断。原正则分词和逐项引号保持，否定词
仍是字面词项而非布尔 NOT。迭代式分词在达到预算后停止。

## 决策及依据

工作区研究中，163 个此前未评分的偏好/多会话问题上，十词与 64 词控制的
nDCG@10 为 0.5372 与 0.6642；64 词并非每题都更好（70 胜 / 19 负）。
因此保留配置和兼容值，不把 64 声称为普适最优值。普通词过滤的收益较小且偏好
任务退步，继续只放在研究控制中。该结果是检索分数，不是最终回答准确率。

## 实现与验证

`internal.py` 负责预算常量、校验及有限 FTS 词项；`config.py` 在 dataclass、
YAML 和显式覆盖路径校验；manager 从设置取预算，仅传给关键词构造器。
模板与中英文记忆文档同步。先前 `chunks.source` SQL 修复及评分/降级修复一并
作为已有基线带入本隔离分支，并未改写研究原始分支。

定向真实模块/FTS 表结构回归 27 例通过，包括第十词后的实体、可恢复十词、
长问题硬词项预算、配置非法值、标识符/否定词、多来源过滤和语义问题完整传递。
2026-11-10 在独立 fork 的 exp 分支，以 Python 3.14 / pytest 8.4.2 重验 27 例通过。
本次直接导入真实模块和运行目录函数，仅用 confcutdir 跳过无关的全局 SDK fixtures；
向量 UDF 由测试提供，不代表真实向量扩展、完整部署或端到端准确率验证。

研究结果入口：工作区 `research/2026-11-05-memory-combinations/iteration-02-findings.md`。
当前契约见 `S_01_keyword-query-budget`。实现、回归与文档一并提交至本地 exp；未合并、未部署。
