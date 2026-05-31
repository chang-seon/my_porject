"""운영 모니터링 대시보드 — FastAPI + 정적 HTML (#54).

실행: python -m tools.dashboard.server
또는: uvicorn tools.dashboard.server:app --host 0.0.0.0 --port 8080
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

_DB_PATH = Path(os.getenv("DB_PATH", r"D:\IT\Agentic_AI\data\agent.db"))

app = FastAPI(title="구직 에이전트 대시보드", version="1.0.0")


# ─────────────────────────────────────────
# API 엔드포인트
# ─────────────────────────────────────────

@app.get("/api/cost", response_class=JSONResponse)
def api_cost_summary(days: int = Query(default=7, ge=1, le=90)):
    """최근 N일 LLM 비용 요약을 반환한다."""
    try:
        conn = _get_conn()
        today = date.today()
        start = today - timedelta(days=days - 1)
        rows = conn.execute(
            """SELECT model, SUM(input_tokens) AS inp, SUM(output_tokens) AS out, SUM(cost_usd) AS cost
               FROM cost_log
               WHERE (year > ? OR (year = ? AND month > ?) OR (year = ? AND month = ? AND day >= ?))
               GROUP BY model""",
            (start.year, start.year, start.month, start.year, start.month, start.day),
        ).fetchall()
        conn.close()
        return {
            "period": f"{start.isoformat()} ~ {today.isoformat()}",
            "models": [{"model": r[0], "input_tokens": r[1], "output_tokens": r[2], "cost_usd": round(r[3], 6)} for r in rows],
            "total_cost_usd": round(sum(r[3] for r in rows), 6),
        }
    except Exception as e:
        return JSONResponse({"error": str(e)})


@app.get("/api/hitl", response_class=JSONResponse)
def api_hitl_pending():
    """대기 중인 HITL 요청 수를 반환한다."""
    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT COUNT(*) AS cnt FROM hitl_requests WHERE status='pending'"
        ).fetchone()
        conn.close()
        count = rows[0] if rows else 0
        return {"pending_hitl": count}
    except Exception as e:
        return JSONResponse({"error": str(e)})


@app.get("/api/validation", response_class=JSONResponse)
def api_validation_stats(days: int = Query(default=7, ge=1, le=90)):
    """최근 N일 검증 통과율을 반환한다."""
    try:
        conn = _get_conn()
        today = date.today()
        start = today - timedelta(days=days - 1)
        rows = conn.execute(
            """SELECT payload FROM learning_signals
               WHERE layer='B' AND signal_type='validation_result'
               AND (year > ? OR (year = ? AND month >= ?))""",
            (start.year, start.year, start.month),
        ).fetchall()
        conn.close()
        total = len(rows)
        passed = sum(1 for r in rows if _extract_passed(r[0]))
        rate = passed / total if total > 0 else 0.0
        return {"total": total, "passed": passed, "pass_rate": round(rate, 3)}
    except Exception as e:
        return JSONResponse({"error": str(e)})


@app.get("/api/automation", response_class=JSONResponse)
def api_automation_levels():
    """사용자별 자동화 수준을 반환한다."""
    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT user_id, value FROM dynamic_thresholds WHERE domain='automation' AND context_key='current_level'"
        ).fetchall()
        conn.close()
        return {"users": [{"user_id": r[0], "level": int(r[1])} for r in rows]}
    except Exception as e:
        return JSONResponse({"error": str(e)})


@app.get("/api/applications", response_class=JSONResponse)
def api_application_stats(days: int = Query(default=30, ge=1, le=365)):
    """최근 N일 지원 현황을 반환한다."""
    try:
        conn = _get_conn()
        today = date.today()
        start = today - timedelta(days=days - 1)
        rows = conn.execute(
            """SELECT COUNT(*) FROM event_logs
               WHERE event_type='application_created'
               AND (year > ? OR (year = ? AND month >= ?))""",
            (start.year, start.year, start.month),
        ).fetchone()
        conn.close()
        return {"total_applications": rows[0] if rows else 0, "period_days": days}
    except Exception as e:
        return JSONResponse({"error": str(e)})


@app.get("/", response_class=HTMLResponse)
def dashboard_html():
    """대시보드 메인 HTML 페이지."""
    return HTMLResponse(_DASHBOARD_HTML)


# ─────────────────────────────────────────
# 내부 유틸
# ─────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _extract_passed(payload_json: str) -> bool:
    try:
        return json.loads(payload_json).get("passed", False)
    except Exception:
        return False


_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>구직 에이전트 대시보드</title>
<style>
  body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }
  h1 { color: #60a5fa; font-size: 1.5rem; margin-bottom: 20px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
  .card { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; }
  .card h2 { font-size: 0.85rem; color: #94a3b8; margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.05em; }
  .card .value { font-size: 2rem; font-weight: bold; color: #f1f5f9; }
  .card .sub { font-size: 0.8rem; color: #64748b; margin-top: 4px; }
  .status { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }
  .ok { background: #064e3b; color: #34d399; }
  .warn { background: #78350f; color: #fbbf24; }
  pre { background: #0f172a; padding: 12px; border-radius: 8px; overflow-x: auto; font-size: 0.8rem; color: #a5b4fc; }
</style>
</head>
<body>
<h1>🤖 구직 에이전트 운영 대시보드</h1>
<div class="grid" id="cards"></div>
<div style="margin-top:20px">
  <h2 style="color:#94a3b8;font-size:0.85rem;">API 원시 데이터</h2>
  <pre id="raw"></pre>
</div>
<script>
async function load() {
  const [cost, hitl, val, auto_, apps] = await Promise.all([
    fetch('/api/cost').then(r=>r.json()),
    fetch('/api/hitl').then(r=>r.json()),
    fetch('/api/validation').then(r=>r.json()),
    fetch('/api/automation').then(r=>r.json()),
    fetch('/api/applications').then(r=>r.json()),
  ]);
  const cards = document.getElementById('cards');
  cards.innerHTML = `
    <div class="card">
      <h2>💰 7일 LLM 비용</h2>
      <div class="value">$${cost.total_cost_usd || 0}</div>
      <div class="sub">${cost.period || ''}</div>
    </div>
    <div class="card">
      <h2>🔔 HITL 대기</h2>
      <div class="value">${hitl.pending_hitl || 0}</div>
      <div class="sub"><span class="status ${hitl.pending_hitl > 5 ? 'warn' : 'ok'}">${hitl.pending_hitl > 5 ? '주의' : '정상'}</span></div>
    </div>
    <div class="card">
      <h2>✅ 검증 통과율 (7일)</h2>
      <div class="value">${((val.pass_rate || 0)*100).toFixed(1)}%</div>
      <div class="sub">${val.passed || 0} / ${val.total || 0} 통과</div>
    </div>
    <div class="card">
      <h2>🚀 자동화 수준</h2>
      <div class="value">${auto_.users ? auto_.users.length : 0}명</div>
      <div class="sub">자동화 설정 사용자</div>
    </div>
    <div class="card">
      <h2>📋 지원 현황 (30일)</h2>
      <div class="value">${apps.total_applications || 0}</div>
      <div class="sub">총 지원 건수</div>
    </div>
  `;
  document.getElementById('raw').textContent = JSON.stringify({cost,hitl,val,automation:auto_,apps}, null, 2);
}
load();
setInterval(load, 30000);
</script>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("tools.dashboard.server:app", host="0.0.0.0", port=8080, reload=False)
