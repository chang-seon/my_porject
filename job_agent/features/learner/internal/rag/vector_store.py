"""RAG 벡터 스토어 — rag_knowledge 테이블 CRUD + 유사도 검색."""
from __future__ import annotations

import json
import pickle
import struct
from datetime import date
from pathlib import Path
from typing import Any

from job_agent.shared.db.connection import get_connection, init_db

_DEFAULT_DB_PATH = Path(__file__).parents[5] / "data" / "agent.db"


def save_knowledge(
    content: str,
    embedding: list[float],
    source: str = "",
    domain: str = "",
    db_path: Path | None = None,
) -> dict:
    """콘텐츠와 임베딩을 rag_knowledge 테이블에 저장한다."""
    try:
        _db = db_path or _DEFAULT_DB_PATH
        init_db(_db)
        blob = _to_blob(embedding)
        d = date.today()
        conn = get_connection(_db)
        try:
            cursor = conn.execute(
                "INSERT INTO rag_knowledge(content, embedding, source, domain, year, month, day) VALUES(?,?,?,?,?,?,?)",
                (content, blob, source, domain, d.year, d.month, d.day),
            )
            conn.commit()
            row_id = cursor.lastrowid
        finally:
            conn.close()
        return {"결과": "성공", "id": row_id, "domain": domain}
    except Exception as e:
        return {"결과": "실���", "이유": str(e)}


def search_similar(
    query_embedding: list[float],
    top_k: int = 5,
    domain: str | None = None,
    db_path: Path | None = None,
) -> dict:
    """코사인 유사도로 가장 유사한 k개 문서를 반환한다."""
    try:
        _db = db_path or _DEFAULT_DB_PATH
        conn = get_connection(_db)
        try:
            if domain:
                rows = conn.execute(
                    "SELECT id, content, embedding, source, domain FROM rag_knowledge WHERE domain=?",
                    (domain,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, content, embedding, source, domain FROM rag_knowledge"
                ).fetchall()
        finally:
            conn.close()

        if not rows:
            return {"결과": "성공", "results": []}

        scored = []
        for row in rows:
            if row["embedding"] is None:
                continue
            doc_emb = _from_blob(row["embedding"])
            score = _cosine_similarity(query_embedding, doc_emb)
            scored.append({
                "id": row["id"],
                "content": row["content"],
                "source": row["source"],
                "domain": row["domain"],
                "score": score,
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return {"결과": "성공", "results": scored[:top_k]}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def get_knowledge(knowledge_id: int, db_path: Path | None = None) -> dict:
    """ID로 단일 지식 항목을 조회한다."""
    try:
        _db = db_path or _DEFAULT_DB_PATH
        conn = get_connection(_db)
        try:
            row = conn.execute("SELECT * FROM rag_knowledge WHERE id=?", (knowledge_id,)).fetchone()
        finally:
            conn.close()
        if row is None:
            return {"결과": "실패", "이유": f"지식 없음: id={knowledge_id}"}
        return {"결과": "성공", "id": row["id"], "content": row["content"], "domain": row["domain"]}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def delete_knowledge(knowledge_id: int, db_path: Path | None = None) -> dict:
    """ID로 지식 항목을 삭제한다."""
    try:
        _db = db_path or _DEFAULT_DB_PATH
        conn = get_connection(_db)
        try:
            conn.execute("DELETE FROM rag_knowledge WHERE id=?", (knowledge_id,))
            conn.commit()
        finally:
            conn.close()
        return {"결과": "성공", "deleted_id": knowledge_id}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def _to_blob(embedding: list[float]) -> bytes:
    """float 리스트를 binary blob으로 변환한다."""
    return struct.pack(f"{len(embedding)}f", *embedding)


def _from_blob(blob: bytes) -> list[float]:
    """binary blob을 float 리스트로 변환한다."""
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """두 벡터의 코사인 유사도를 계산한다."""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
