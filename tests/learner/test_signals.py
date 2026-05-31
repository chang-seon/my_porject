"""DAY 15 — 학습신호 수집 + 동적 기준값 테스트"""
import pytest
from job_agent.shared.db.connection import init_db
from job_agent.shared.schemas.learning_signal import LearningSignal, SignalLayer
from job_agent.features.learner.internal.signal_collector import record_signal, get_signals
from job_agent.features.learner.internal.dynamic_threshold import get_threshold, update_threshold


@pytest.fixture
def tmp_db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    return db_path


class TestSignalCollector:
    @pytest.mark.parametrize("layer", list(SignalLayer))
    def test_all_layers_recordable(self, layer, tmp_db):
        signal = LearningSignal(
            user_id="u001", layer=layer, signal_type="test",
            payload={"test": True}, source_module="test",
        )
        result = record_signal(signal, db_path=tmp_db)
        assert result["결과"] == "성공", f"{layer} 기록 실패: {result.get('이유')}"
        assert result["layer"] == layer.value

    def test_get_signals_by_layer(self, tmp_db):
        for layer in [SignalLayer.A, SignalLayer.B, SignalLayer.B]:
            signal = LearningSignal(user_id="u001", layer=layer, signal_type="t")
            record_signal(signal, db_path=tmp_db)
        b_signals = get_signals("u001", layer="B", db_path=tmp_db)
        assert len(b_signals["signals"]) == 2

    def test_user_isolation(self, tmp_db):
        record_signal(LearningSignal(user_id="u001", layer=SignalLayer.A, signal_type="t"), db_path=tmp_db)
        record_signal(LearningSignal(user_id="u002", layer=SignalLayer.A, signal_type="t"), db_path=tmp_db)
        u1 = get_signals("u001", db_path=tmp_db)
        assert all(r["user_id"] == "u001" for r in u1["signals"])


class TestDynamicThreshold:
    def test_get_default_value(self, tmp_db):
        result = get_threshold("", "automation_promotion_n", "u001", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["source"] == "default"
        assert result["value"] == 5

    def test_update_and_get(self, tmp_db):
        update_threshold("validator", "min_score", 0.75, "u001", db_path=tmp_db)
        result = get_threshold("validator", "min_score", "u001", db_path=tmp_db)
        assert result["결과"] == "성공"
        assert result["source"] == "db"
        assert result["value"] == "0.75"

    def test_update_records_history(self, tmp_db):
        update_threshold("test", "key", 1, "u001", db_path=tmp_db)
        update_threshold("test", "key", 2, "u001", db_path=tmp_db)
        result = get_threshold("test", "key", "u001", db_path=tmp_db)
        assert result["value"] == "2"

    def test_missing_threshold_returns_failure(self, tmp_db):
        result = get_threshold("없는도메인", "없는키", "u001", db_path=tmp_db)
        assert result["결과"] == "실패"
