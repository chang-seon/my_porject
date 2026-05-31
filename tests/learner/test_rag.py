"""DAY 25 — RAG vector_store / ingest / retriever 테스트."""
import pytest
from job_agent.features.learner.internal.rag.embedder import embed, _tokenize
from job_agent.features.learner.internal.rag.vector_store import (
    save_knowledge, search_similar, get_knowledge, delete_knowledge,
    _cosine_similarity,
)
from job_agent.features.learner.internal.rag.ingest import (
    ingest_text, ingest_batch, ingest_company_reviews, ingest_interview_questions,
)
from job_agent.features.learner.internal.rag.retriever import (
    retrieve, retrieve_company_info, retrieve_interview_questions,
)
from job_agent.shared.db.connection import init_db


@pytest.fixture
def tmp_db(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    return db


class TestEmbedder:
    def test_embed_returns_128_dim(self):
        vec = embed("파이썬 AI 개발 경험")
        assert len(vec) == 128

    def test_embed_normalized(self):
        vec = embed("파이썬 AI 개발 경험")
        norm = sum(x * x for x in vec) ** 0.5
        assert abs(norm - 1.0) < 1e-6

    def test_embed_empty_text(self):
        vec = embed("")
        assert all(v == 0.0 for v in vec)

    def test_embed_different_texts_differ(self):
        v1 = embed("파이썬 AI 개발 경험")
        v2 = embed("영업 마케팅 전략")
        assert v1 != v2

    def test_embed_deterministic(self):
        text = "AI 엔지니어 직무"
        assert embed(text) == embed(text)


class TestVectorStore:
    def test_save_and_get(self, tmp_db):
        vec = embed("테스트 콘텐츠")
        r = save_knowledge("테스트 콘텐츠", vec, source="test", domain="test", db_path=tmp_db)
        assert r["결과"] == "성공"
        kid = r["id"]
        g = get_knowledge(kid, db_path=tmp_db)
        assert g["결과"] == "성공"
        assert g["content"] == "테스트 콘텐츠"

    def test_get_nonexistent(self, tmp_db):
        r = get_knowledge(9999, db_path=tmp_db)
        assert r["결과"] == "실패"

    def test_search_similar_top_k(self, tmp_db):
        texts = ["파이썬 AI 개발", "데이터 분석 통계", "영업 마케팅"]
        for t in texts:
            save_knowledge(t, embed(t), domain="test", db_path=tmp_db)
        q = embed("파이썬 머신러닝")
        r = search_similar(q, top_k=2, domain="test", db_path=tmp_db)
        assert r["결과"] == "성공"
        assert len(r["results"]) <= 2

    def test_search_returns_scores(self, tmp_db):
        save_knowledge("AI 개발 경험", embed("AI 개발 경험"), domain="x", db_path=tmp_db)
        q = embed("AI")
        r = search_similar(q, top_k=1, domain="x", db_path=tmp_db)
        assert "score" in r["results"][0]

    def test_cosine_similarity_same_vector(self):
        v = [1.0, 0.0, 0.5]
        score = _cosine_similarity(v, v)
        assert abs(score - 1.0) < 1e-6

    def test_cosine_similarity_zero_vector(self):
        assert _cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0

    def test_delete(self, tmp_db):
        v = embed("삭제 테스트")
        r = save_knowledge("삭제 테스트", v, db_path=tmp_db)
        kid = r["id"]
        d = delete_knowledge(kid, db_path=tmp_db)
        assert d["결과"] == "성공"
        g = get_knowledge(kid, db_path=tmp_db)
        assert g["결과"] == "실패"


class TestIngest:
    def test_ingest_text_success(self, tmp_db):
        r = ingest_text("면접에서 자주 나오는 질문", source="glassdoor", domain="interview_question", db_path=tmp_db)
        assert r["결과"] == "성공"

    def test_ingest_empty_text_fails(self, tmp_db):
        r = ingest_text("", db_path=tmp_db)
        assert r["결과"] == "실패"

    def test_ingest_batch(self, tmp_db):
        items = [
            {"content": "평점 3.5 이상 선호", "source": "잡플래닛", "domain": "company_review"},
            {"content": "야근이 많습니다", "source": "잡플래닛", "domain": "company_review"},
        ]
        r = ingest_batch(items, db_path=tmp_db)
        assert r["결과"] == "성공"
        assert r["success"] == 2

    def test_ingest_company_reviews(self, tmp_db):
        r = ingest_company_reviews("카카오", ["자유로운 분위기", "복지 좋음"], db_path=tmp_db)
        assert r["결과"] == "성공"
        assert r["success"] == 2

    def test_ingest_interview_questions(self, tmp_db):
        r = ingest_interview_questions("네이버", ["지원 동기를 말씀해주세요.", "장단점은?"], db_path=tmp_db)
        assert r["결과"] == "성공"


class TestRetriever:
    def test_retrieve_basic(self, tmp_db):
        ingest_text("AI 모델 개발 경험 5년", domain="test", db_path=tmp_db)
        r = retrieve("AI 개발", top_k=1, domain="test", db_path=tmp_db)
        assert r["결과"] == "성공"

    def test_retrieve_empty_query(self, tmp_db):
        r = retrieve("", db_path=tmp_db)
        assert r["결과"] == "실패"

    def test_retrieve_company_info(self, tmp_db):
        ingest_company_reviews("삼성전자", ["안정적인 회사"], db_path=tmp_db)
        r = retrieve_company_info("삼성전자", top_k=1, db_path=tmp_db)
        assert r["결과"] == "성공"

    def test_retrieve_interview_questions(self, tmp_db):
        ingest_interview_questions("카카오", ["자기소개 해주세요."], db_path=tmp_db)
        r = retrieve_interview_questions("카카오", "AI 엔지니어", top_k=1, db_path=tmp_db)
        assert r["결과"] == "성공"
