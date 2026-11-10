---
id: F_20261111_0005_native-benchmark-ingestion
title: Native benchmark ingestion launcher
type: F
author: Arshia Zakeri Rad
author_email: zrr.arshia@gmail.com
updated: '2026-11-10'
modules:
  - scripts
files:
  - scripts/ingest_memory_benchmark.py
  - docs/en/Memory.md
  - docs/zh/记忆.md
designs: []
design_note: 用户明确要求仅在 fork 的 exp 分支增加评测前原生数据摄入；复用跨仓 API，不另造抽取器。
status: implemented
---

# Native benchmark ingestion launcher

## 行为与决策

提供独立实验 CLI 启动器，选择 agent-memory fork 路径和 Python 环境，将参数、
环境与退出状态转发给 evaluation.ingestion。它不复制摄入状态机、身份逻辑或抽取器，
不改变线上 memory manager、prefetch、tool schema 或本地文件索引行为。

完整历史源导入、按序 native add(infer=True)、持久检查点、故障阻断与 benchmark
门禁归 agent-memory 的 S11-evaluation-ingestion 契约维护，不在 Swarm 重复定义。
Python API / CLI 可用，不声称提供新的 HTTP 上传接口。

## 拒绝方案

不在两仓各实现一份 extractor，不把原始事实直接插入当提炼，不将本地文件记忆
与 agent-memory 原生生命周期混为同一存储；不从本启动器自动启动付费基准。

## 验证与限制

通过实际子进程进入 agent-memory CLI 的 help/status 入口，核对参数/路径转发。
核心 native 摄入/重启/门禁行为由 agent-memory 的单元与集成测试验证，只有模型
输出与 embedding 使用确定性替身；无付费模型质量结论或完整 Swarm 运行时结论。
此前评分修复另在第一提交，不混入本次功能的准确率声明。
