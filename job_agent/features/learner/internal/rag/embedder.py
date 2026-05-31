"""임베딩 생성 — 로컬 우선(#39). TF-IDF 기반 간이 임베딩 (sentence-transformers 스왑 가능)."""
from __future__ import annotations

import hashlib
import math
import re
from collections import Counter


_DIM = 128


def embed(text: str) -> list[float]:
    """텍스트를 128차원 벡터로 임베딩한다.

    v1: 한국어 음절 기반 TF 해시 임베딩 (로컬, 비용 0)
    v2 업그레이드: sentence-transformers 교체 가능
    """
    tokens = _tokenize(text)
    if not tokens:
        return [0.0] * _DIM
    freq = Counter(tokens)
    vec = [0.0] * _DIM
    for token, count in freq.items():
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        idx = h % _DIM
        vec[idx] += math.log1p(count)
    return _normalize(vec)


def embed_batch(texts: list[str]) -> list[list[float]]:
    """텍스트 목록을 일괄 임베딩한다."""
    return [embed(t) for t in texts]


def _tokenize(text: str) -> list[str]:
    """한국어 2~4음절 n-gram 토큰화."""
    cleaned = re.sub(r"\s+", " ", text.strip())
    tokens = []
    for n in (2, 3):
        for i in range(len(cleaned) - n + 1):
            gram = cleaned[i:i + n]
            if gram.strip():
                tokens.append(gram)
    return tokens


def _normalize(vec: list[float]) -> list[float]:
    norm = sum(x * x for x in vec) ** 0.5
    if norm == 0:
        return vec
    return [x / norm for x in vec]
