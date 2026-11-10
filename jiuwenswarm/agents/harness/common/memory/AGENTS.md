# Local memory search

## Module map

- `internal.py`: FTS query construction, native-rank conversion and shared cosine score conversion.
- `manager.py`: index management, eligible keyword/vector candidates, failure-aware hybrid search.
- `config.py`: settings and default weights/thresholds.
- `embeddings.py`: embedding provider contracts and implementations.

## Invariants

- Native FTS5 rank is negative and lower is stronger; exposed lexical strength is higher-is-better.
- Normalize lexical strength within the eligible query result list; do not treat it as probability.
- Apply enabled-source membership before a ranked SQL limit.
- Qualify source predicates as `chunks.source`: the production FTS5 table also has a `source` column. Keyword regression fixtures must use `_ensure_schema()` so joined-column ambiguity remains covered.
- Keyword query terms are literal, preserve negation and identifiers, and use `query.keywordMaxTerms` (default 64, valid integer range 1–256). A value of 10 restores the earlier term budget. Do not apply the keyword budget to the raw semantic query or silently remove function words.
- Both vector implementations use the same bounded cosine score conversion.
- Failed/unavailable arms may renormalize surviving weights; healthy empty arms must not.
- Keep hybrid merge inputs unchanged, since callers may reuse cached candidate lists.
- SQL/provider failures remain visible to the orchestration layer; do not report them as healthy empty results.

## Boundary

This module implements host-local memory. External JiuwenMemory providers and their rerankers
have separate score contracts and must be changed in their own repository.
