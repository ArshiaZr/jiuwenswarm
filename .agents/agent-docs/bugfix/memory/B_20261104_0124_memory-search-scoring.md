---
id: B_20261104_0124_memory-search-scoring
title: Local memory keyword and semantic score corrections
type: B
author: Arshia Zakeri Rad
author_email: zrr.arshia@gmail.com
modules:
  - jiuwenswarm/agents/harness/common/memory
files:
  - jiuwenswarm/agents/harness/common/memory/internal.py
  - jiuwenswarm/agents/harness/common/memory/manager.py
  - tests/unit_tests/agentserver/memory/test_memory_search_scoring.py
designs: []
design_note: Repairs to existing search contracts; no separate design or approval record is invented.
---

# 本地记忆检索评分修复

## 现象、根因与修复

- FTS5 越负越强，原转换 `1/(1-rank)` 却把更强结果转成更低分。现在以
  `strength=max(-rank,0)`、`strength/(1+strength)` 保证同方向，再按合格列表最大值归一。
  不能只反号而不考虑混合阈值，归一后的 lexical score 仍不是绝对置信度。
- sqlite-vec 输出 `1-distance/2`，Python 回退输出 `max(cosine,0)`，同一向量改变阈值。
  两路共用 `(1+cosine)/2` 的有限值/范围转换，保持原扩展路的分数口径。
- embedding 失败仍把唯一关键词路乘 0.3，会触发默认过滤。失败/不可用路现在显式
  降级，健康路使用完整权重；健康但空结果不重分配权重，避免正常无命中语义漂移。
- FTS SQL 先 limit 后检查来源，禁用来源会占满候选池。现在 join chunks 并在 limit 前
  使用来源条件。词法后端异常向 search 编排传播，不再伪装为空命中。
- 混合器原地覆盖输入候选分数，复用缓存时可重复加权。现在合并副本，输入保持不变。

## 验证证据与限制

新回归文件 13 例通过：真实 SQLite FTS5 排序、禁用来源挤占、五组余弦正负边界、
非有限值、embedding 故障、健康空路、零权重路不激活、关键词后端故障和重复合并。
从真实 MemoryIndexManager.search / keyword / vector / merge 方法进入，不用复制评分公式
充当被测实现；只有可选 sqlite-vec 的距离 UDF 用确定性余弦实现替代。

环境仅有 Python 3.14。pytest 9.1.1 和可用依赖由本地 pip 缓存离线恢复。
定向运行跳过无关 SDK fixture 并用临时路径函数替代运行时 utils，实际加载本模块的
manager/config/internal/embeddings/types。没有完整 Swarm SDK 集成、真实扩展加载或在线模型验证。
正常依赖环境的入口是本文件记录的 pytest 测试路径；不能把本地边界测试解释为全仓通过。

GitHub 无法解析，因此基于用户选择的缓存 develop 工作树实施；未声称刷新远端。
原来源隔离条件不扩大，原“近期文件由系统提示加载”约定不变。

## 当前契约与资料同步

本模块 AGENTS 固定方向、范围、候选资格、失败/空命中区分和输入不可变约束。
`docs/en/Memory.md` 与 `docs/zh/记忆.md` 同步评分和降级语义。

## 仍需研究

对比当前加权融合与 RRF；固定候选池、embedding 模型和上下文预算测量覆盖率与排序，
另测分词、普通词和词形变化。归一后的 minScore 是查询相对阈值，需要代表性数据验证。
真实 sqlite-vec、完整运行时和锁定依赖 CI 仍需重验；不声明基准准确率提升。

## 2026-11-05 补充：真实 FTS 表结构暴露来源列歧义

先前为在 limit 前过滤来源而加入 `JOIN chunks`，但来源条件仍是未限定表名的
`source`。真实 `_ensure_schema()` 会同时在 `chunks` 和 `chunks_fts` 建立该列，
因此关键词 SQL 抛出 `sqlite3.OperationalError: ambiguous column name: source`。
较早的 13 例测试使用只有 `text` 列的简化 FTS 表，没有覆盖这个回归；历史通过
仅代表当时的夹具，不能证明真实表结构中的关键词查询可用。

本次将单来源及多来源条件统一限定为 `chunks.source`，兼容原先只查询 chunks 的
向量/候选映射路径，也兼容关键词 JOIN。测试夹具改为调用真实 `_ensure_schema()`，
按生产列写入 chunks 和 FTS 记录，新增多来源覆盖；原“禁用来源不占用 limit”检查保留。

隔离分支 `fix/memory-keyword-sql-source` 携带原有修复，仅追加这个 SQL 修复和回归。
用同一组真实表结构测试核对：原候选 **4 failed, 10 passed**，修复后 **14 passed**。
验证加载真实 config/internal/embeddings/types/manager；仅跳过 SDK 包初始化和无关
pytest fixtures，将两个运行目录解析函数指向临时路径。Python 3.14、pytest 9.2.0；
不初始化外部 embedding provider，不调用模型，不声称完整 Swarm 部署或真实 sqlite-vec 验证。

复现脚本及原始输出保存在工作区研究目录
`research/2026-11-05-memory-combinations/run_swarm_regression.py` 与
`runs/swarm-source-regression-001/`。原研究基线工作树保持不变，公开数据上的原始
关键词错误单独记载，不当作健康查询的零召回分数。本分支仍保留原十词查询上限；
取消上限只在独立研究对照中评估，未混入 SQL 修复。
