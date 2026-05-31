-- 0002: pass_records 테이블 컬럼 추가
-- SQLite는 ADD COLUMN IF NOT EXISTS 미지원 → Python 레벨에서 처리
ALTER TABLE pass_records ADD COLUMN job_url    TEXT DEFAULT '';
ALTER TABLE pass_records ADD COLUMN is_active  INTEGER DEFAULT 1;
ALTER TABLE pass_records ADD COLUMN passed_at  TEXT DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_pass_url ON pass_records(user_id, job_url);
