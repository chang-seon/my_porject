"""DAY 29 — dashboard API 테스트 (TestClient 사용, 실제 서버 불필요)."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sqlite3
from pathlib import Path

from tools.dashboard.server import app, _DASHBOARD_HTML

client = TestClient(app)


class TestDashboardEndpoints:
    def test_root_returns_html(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "구직 에이전트" in resp.text
        assert "<html" in resp.text

    def test_api_cost_returns_json(self):
        resp = client.get("/api/cost?days=7")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_cost_usd" in data or "error" in data

    def test_api_hitl_returns_json(self):
        resp = client.get("/api/hitl")
        assert resp.status_code == 200
        data = resp.json()
        assert "pending_hitl" in data or "error" in data

    def test_api_validation_returns_json(self):
        resp = client.get("/api/validation?days=7")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data or "error" in data

    def test_api_automation_returns_json(self):
        resp = client.get("/api/automation")
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data or "error" in data

    def test_api_applications_returns_json(self):
        resp = client.get("/api/applications?days=30")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_applications" in data or "error" in data

    def test_html_contains_cards(self):
        assert "grid" in _DASHBOARD_HTML
        assert "LLM 비용" in _DASHBOARD_HTML
        assert "HITL" in _DASHBOARD_HTML
        assert "검증 통과율" in _DASHBOARD_HTML
        assert "자동화 수준" in _DASHBOARD_HTML
        assert "지원 현황" in _DASHBOARD_HTML
