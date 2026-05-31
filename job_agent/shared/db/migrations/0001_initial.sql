-- 0001_initial.sql — idempotent (CREATE TABLE IF NOT EXISTS)
-- 페르소나 11섹션 테이블

CREATE TABLE IF NOT EXISTS personas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    birth       TEXT,
    address     TEXT,
    disability  TEXT,
    career_stage TEXT,
    created_at  TEXT,
    updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS persona_educations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL REFERENCES personas(user_id),
    school      TEXT NOT NULL,
    major       TEXT,
    degree      TEXT,
    graduated   TEXT
);

CREATE TABLE IF NOT EXISTS persona_target_jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL REFERENCES personas(user_id),
    industry    TEXT NOT NULL,
    job_role    TEXT NOT NULL,
    priority    INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS persona_content_assets (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT NOT NULL REFERENCES personas(user_id),
    title        TEXT NOT NULL,
    description  TEXT NOT NULL,
    context      TEXT NOT NULL,
    tags         TEXT DEFAULT '[]',
    is_killer    INTEGER DEFAULT 0,
    ai_relevance REAL DEFAULT 0.0,
    usage_count  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS persona_skills (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       TEXT NOT NULL REFERENCES personas(user_id),
    skill_type    TEXT NOT NULL,
    name          TEXT NOT NULL,
    acquired_date TEXT,
    ai_relevance  REAL DEFAULT 0.0,
    status        TEXT DEFAULT '보유'
);

CREATE TABLE IF NOT EXISTS persona_style_markers (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT NOT NULL REFERENCES personas(user_id),
    marker_name  TEXT NOT NULL,
    description  TEXT NOT NULL,
    examples     TEXT DEFAULT '[]',
    weight       REAL DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS persona_anti_patterns (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT NOT NULL REFERENCES personas(user_id),
    pattern_name TEXT NOT NULL,
    description  TEXT NOT NULL,
    examples     TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS persona_traits (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT NOT NULL REFERENCES personas(user_id),
    trait_type TEXT NOT NULL,
    trait      TEXT NOT NULL,
    evidence   TEXT,
    self_aware INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS persona_values (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT NOT NULL REFERENCES personas(user_id),
    value_text TEXT NOT NULL,
    source     TEXT
);

CREATE TABLE IF NOT EXISTS persona_constraints (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           TEXT NOT NULL REFERENCES personas(user_id),
    constraint_type   TEXT NOT NULL,
    value             TEXT NOT NULL,
    is_hard           INTEGER DEFAULT 1,
    threshold_dynamic TEXT
);

CREATE TABLE IF NOT EXISTS persona_career_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT NOT NULL REFERENCES personas(user_id),
    stage        TEXT NOT NULL,
    changed_date TEXT
);

-- 변경 이력 (#37)
CREATE TABLE IF NOT EXISTS persona_changelog (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL,
    section     TEXT NOT NULL,
    before_json TEXT,
    after_json  TEXT,
    reason      TEXT,
    trigger     TEXT,
    timestamp   TEXT,
    year        INTEGER,
    month       INTEGER,
    day         INTEGER
);

-- 패스·배제 기록
CREATE TABLE IF NOT EXISTS pass_records (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          TEXT NOT NULL,
    company          TEXT NOT NULL,
    job_role         TEXT,
    reason           TEXT,
    analysis_result  TEXT,
    company_snapshot TEXT DEFAULT '{}',
    year             INTEGER,
    month            INTEGER,
    day              INTEGER
);

-- 학습 신호 5층
CREATE TABLE IF NOT EXISTS learning_signals (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          TEXT NOT NULL,
    layer            TEXT NOT NULL,
    signal_type      TEXT NOT NULL,
    payload          TEXT DEFAULT '{}',
    source_module    TEXT,
    reference_id     TEXT,
    is_labeled       INTEGER DEFAULT 0,
    label            TEXT,
    revision_history TEXT DEFAULT '[]',
    timestamp        TEXT,
    year             INTEGER,
    month            INTEGER,
    day              INTEGER
);

-- 이벤트 로그
CREATE TABLE IF NOT EXISTS event_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    event_data  TEXT DEFAULT '{}',
    timestamp   TEXT,
    year        INTEGER,
    month       INTEGER,
    day         INTEGER
);

-- 동적 기준값 (#37)
CREATE TABLE IF NOT EXISTS dynamic_thresholds (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT NOT NULL,
    domain         TEXT NOT NULL,
    context_key    TEXT NOT NULL,
    value          TEXT NOT NULL,
    changed_at     TEXT,
    change_history TEXT DEFAULT '[]',
    UNIQUE(user_id, domain, context_key)
);

-- RAG 공유 지식 (user_id 없음 — 전체 공유 #38)
CREATE TABLE IF NOT EXISTS rag_knowledge (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    content   TEXT NOT NULL,
    embedding BLOB,
    source    TEXT,
    domain    TEXT,
    year      INTEGER,
    month     INTEGER,
    day       INTEGER
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_personas_user         ON personas(user_id);
CREATE INDEX IF NOT EXISTS idx_signals_user_layer    ON learning_signals(user_id, layer);
CREATE INDEX IF NOT EXISTS idx_signals_year_month    ON learning_signals(year, month);
CREATE INDEX IF NOT EXISTS idx_events_user_type      ON event_logs(user_id, event_type);
CREATE INDEX IF NOT EXISTS idx_pass_user             ON pass_records(user_id);
CREATE INDEX IF NOT EXISTS idx_thresholds_user       ON dynamic_thresholds(user_id, domain);
CREATE INDEX IF NOT EXISTS idx_changelog_user_sec    ON persona_changelog(user_id, section);
