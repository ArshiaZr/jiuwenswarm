"""Local memory search regression checks using real SQLite FTS5 records."""
import asyncio
import math
import logging
import sqlite3

import pytest

from jiuwenswarm.agents.harness.common.memory.config import MemorySettings
from jiuwenswarm.agents.harness.common.memory import config as memory_config
from jiuwenswarm.agents.harness.common.memory.internal import (
    bm25_rank_to_score,
    build_fts_query,
    cosine_similarity_to_score,
)
from jiuwenswarm.agents.harness.common.memory.manager import (
    MemoryIndexManager,
    blob_to_vector,
    vector_to_blob,
)


@pytest.fixture
def manager(tmp_path, caplog):
    settings = MemorySettings(sources=["memory"], sync={"onSearch": False})
    instance = MemoryIndexManager("test", str(tmp_path), settings)
    instance.db = sqlite3.connect(":memory:")
    instance.db.row_factory = sqlite3.Row
    instance._ensure_schema()
    assert instance.fts_available, instance.fts_error
    instance.db.execute("CREATE TABLE chunks_vec(embedding BLOB)")
    instance.vector_enabled = False
    instance.dirty = False
    logger = logging.getLogger("jiuwenswarm.agents.harness.common.memory.manager")
    logger.addHandler(caplog.handler)
    try:
        yield instance
    finally:
        logger.removeHandler(caplog.handler)
        instance.db.close()


def add(manager, uid, text, source="memory", embedding=None):
    blob = vector_to_blob(embedding) if embedding is not None else None
    cursor = manager.db.execute("""INSERT INTO chunks
                                (id,path,source,start_line,end_line,text,embedding)
                                VALUES(?,?,?,?,?,?,?)""",
                                (uid, f"memory/{uid}.md", source, 1, 1, text, blob))
    manager.db.execute("INSERT INTO chunks_fts(rowid,id,path,source,text) VALUES(?,?,?,?,?)",
                       (cursor.lastrowid, uid, f"memory/{uid}.md", source, text))
    if blob is not None:
        manager.db.execute("INSERT INTO chunks_vec(rowid,embedding) VALUES(?,?)",
                           (cursor.lastrowid, blob))


def test_fts_score_direction_and_query_relative_strength(manager):
    add(manager, "strong", "espresso espresso")
    add(manager, "weak", "espresso with several unrelated filler words")
    hits = asyncio.run(manager._search_keyword("espresso", 10))
    assert [hit["id"] for hit in hits] == ["strong", "weak"]
    assert hits[0]["score"] == 1.0
    assert 0 < hits[1]["score"] < hits[0]["score"]
    assert bm25_rank_to_score(-10) > bm25_rank_to_score(-1) > bm25_rank_to_score(-0.01)


def test_disabled_sources_cannot_consume_keyword_limit(manager):
    for i in range(30):
        add(manager, f"disabled-{i}", "espresso espresso", source="sessions")
    add(manager, "allowed", "espresso with additional context")
    hits = asyncio.run(manager._search_keyword("espresso", 1))
    assert [hit["id"] for hit in hits] == ["allowed"]


def test_multiple_enabled_sources_use_real_fts_schema(manager):
    manager.settings.sources = ["memory", "sessions"]
    add(manager, "memory-fact", "espresso", source="memory")
    add(manager, "session-fact", "espresso", source="sessions")
    add(manager, "disabled", "espresso espresso", source="disabled")
    hits = asyncio.run(manager._search_keyword("espresso", 10))
    assert {hit["id"] for hit in hits} == {"memory-fact", "session-fact"}


def test_keyword_budget_keeps_book_title_after_tenth_word(manager):
    add(manager, "book", "Nightingale")
    query = "How many days did it take me to finish The Nightingale?"
    assert [hit["id"] for hit in asyncio.run(manager._search_keyword(query, 5))] == ["book"]
    manager.settings.query["keywordMaxTerms"] = 10
    assert asyncio.run(manager._search_keyword(query, 5)) == []


def test_keyword_term_budget_stays_bounded_for_long_inputs(manager):
    add(manager, "tail", "Nightingale")
    query = "filler " * 64 + "Nightingale"
    assert asyncio.run(manager._search_keyword(query, 5)) == []
    manager.settings.query["keywordMaxTerms"] = 65
    assert [hit["id"] for hit in asyncio.run(manager._search_keyword(query, 5))] == ["tail"]


def test_keyword_budget_does_not_trim_semantic_query(manager):
    captured = []
    class Provider:
        async def embed_query(self, text):
            captured.append(text)
            return [0.0, 0.0]
    manager.provider = Provider()
    add(manager, "book", "Nightingale")
    query = "Nightingale " + "filler " * 100 + "SemanticTail"
    assert asyncio.run(manager.search(query))[0]["id"] == "book"
    assert captured == [query]


def test_keyword_identifiers_and_negation_remain_literal(manager):
    add(manager, "exact", "The deployment label is C-prod-07; do not change it.")
    add(manager, "other", "The deployment label is C-prod-08; do change it.")
    assert '"not"' in build_fts_query("do not change C-prod-07")
    assert asyncio.run(manager._search_keyword("C-prod-07", 2))[0]["id"] == "exact"
    assert asyncio.run(manager._search_keyword('"C-prod-07" OR (nothing*)', 2))


@pytest.mark.parametrize("value", [0, -1, 257, True, False, None, 1.5, "64"])
def test_invalid_keyword_budgets_are_rejected(value):
    with pytest.raises(ValueError, match="keywordMaxTerms"):
        MemorySettings(query={"keywordMaxTerms": value})
    with pytest.raises(ValueError, match="keywordMaxTerms"):
        build_fts_query("Nightingale", max_terms=value)


def test_keyword_budget_loads_from_yaml_and_runtime_overrides(tmp_path, monkeypatch):
    path = tmp_path / "config.yaml"
    path.write_text("memory:\n  query:\n    keywordMaxTerms: 10\n", encoding="utf-8")
    monkeypatch.setattr(memory_config, "DEFAULT_CONFIG_PATH", str(path))
    monkeypatch.setattr(memory_config, "_config_cache", None)
    assert memory_config.create_memory_settings().query["keywordMaxTerms"] == 10
    assert memory_config.create_memory_settings(query={"keywordMaxTerms": 32}).query["keywordMaxTerms"] == 32
    assert MemorySettings().query["keywordMaxTerms"] == 64
    path.write_text("memory:\n  query:\n    keywordMaxTerms: '64'\n", encoding="utf-8")
    memory_config.clear_config_cache()
    with pytest.raises(ValueError, match="keywordMaxTerms"):
        memory_config.create_memory_settings()


@pytest.mark.parametrize("similarity", [-1.0, -0.4, 0.0, 0.2, 1.0])
def test_native_and_python_vector_scores_agree(manager, similarity):
    add(manager, "fact", "coffee preference", embedding=[similarity, math.sqrt(1-similarity**2)])
    fallback = asyncio.run(manager._search_vector_fallback([1.0, 0.0], 1))
    manager.vector_enabled = True
    manager.vector_available = True
    manager.vector_dims = 2
    manager._ensure_vector_table = lambda dims: None
    manager.db.create_function("vec_f32", 1, lambda value: value)

    def cosine_distance(document, query):
        a, b = blob_to_vector(document), blob_to_vector(query)
        dot = sum(x*y for x,y in zip(a,b))
        norm = math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))
        return 1 - dot/norm

    # Exercise the real SQL branch; only the optional extension's UDF is supplied.
    manager.db.create_function("vec_distance_cosine", 2, cosine_distance)
    native = asyncio.run(manager._search_vector([1.0, 0.0], 1))
    expected = (1 + similarity) / 2
    assert native[0]["score"] == pytest.approx(expected)
    assert fallback[0]["score"] == pytest.approx(expected)


def test_non_finite_scores_do_not_enter_hybrid_ranking():
    assert bm25_rank_to_score(float("nan")) == 0
    assert cosine_similarity_to_score(float("inf")) == 0


def test_embedding_failure_preserves_working_keyword_search(manager, caplog):
    class FailedProvider:
        async def embed_query(self, text):
            raise TimeoutError("provider unavailable")

    manager.provider = FailedProvider()
    add(manager, "saved", "espresso preference")
    hits = asyncio.run(manager.search("espresso"))
    assert [hit["id"] for hit in hits] == ["saved"]
    assert "degraded" in caplog.text


def test_healthy_empty_vector_arm_keeps_configured_weights(manager):
    class Provider:
        async def embed_query(self, text):
            return [1.0, 0.0]

    manager.provider = Provider()
    add(manager, "text-only", "espresso preference")
    # A healthy empty vector result is not an outage and does not renormalize.
    assert asyncio.run(manager.search("espresso", {"minScore": 0.5})) == []


def test_embedding_failure_does_not_enable_a_zero_weight_keyword_arm(manager):
    class FailedProvider:
        async def embed_query(self, text):
            raise TimeoutError("provider unavailable")

    manager.provider = FailedProvider()
    manager.settings.query["hybrid"]["textWeight"] = 0.0
    add(manager, "text-only", "espresso preference")
    assert asyncio.run(manager.search("espresso")) == []


def test_keyword_failure_preserves_working_vector_search(manager, caplog):
    class Provider:
        async def embed_query(self, text):
            return [1.0, 0.0]

    manager.provider = Provider()
    add(manager, "vector", "coffee preference", embedding=[0.2, math.sqrt(0.96)])
    manager.db.execute("DROP TABLE chunks_fts")
    hits = asyncio.run(manager.search("coffee", {"minScore": 0.5}))
    assert [hit["id"] for hit in hits] == ["vector"]
    assert hits[0]["score"] == pytest.approx(0.6)
    assert "degraded" in caplog.text


def test_hybrid_merge_does_not_modify_or_rescale_cached_inputs(manager):
    vectors = [{"id": "one", "score": 0.8}]
    keywords = [{"id": "one", "score": 1.0}]
    first = manager._merge_hybrid_results(vectors, keywords, 0.7, 0.3)
    second = manager._merge_hybrid_results(vectors, keywords, 0.7, 0.3)
    assert first == second
    assert vectors == [{"id": "one", "score": 0.8}]
    assert keywords == [{"id": "one", "score": 1.0}]
