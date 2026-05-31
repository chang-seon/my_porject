from __future__ import annotations
import json
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

_DEFAULT_DB_PATH = Path(os.getenv("DB_PATH", r"D:\IT\Agentic_AI\data\agent.db"))
_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def get_connection(db_path: Path = _DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = _DEFAULT_DB_PATH) -> None:
    """모든 마이그레이션 파일을 순서대로 실행한다. 이미 적용된 컬럼 추가는 무시한다."""
    conn = get_connection(db_path)
    try:
        migrations = sorted(_MIGRATIONS_DIR.glob("*.sql"))
        for migration in migrations:
            sql = migration.read_text(encoding="utf-8")
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            for stmt in statements:
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError as e:
                    msg = str(e).lower()
                    # 이미 추가된 컬럼이거나 이미 존재하는 인덱스는 무시
                    if "duplicate column name" in msg or "already exists" in msg:
                        continue
                    raise
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DB 관리")
    parser.add_argument("--init", action="store_true", help="DB 초기화 (idempotent)")
    args = parser.parse_args()

    if args.init:
        init_db()
        print(f"DB 초기화 완료: {_DEFAULT_DB_PATH}")
