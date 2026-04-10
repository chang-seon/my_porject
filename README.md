# Agentic AI — PC 관리 에이전트

사용자의 Windows PC에서 자율적으로 동작하는 AI 에이전트.  
반복 작업 자동화, 시스템 모니터링, 파일 정리, 웹 검색을 대화형으로 수행한다.

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| 시스템 모니터링 | CPU·RAM·디스크 사용률 및 상위 프로세스 조회 |
| 파일 관리 | 디렉터리 탐색, 대용량 파일 탐색, 다운로드 폴더 자동 정리 |
| 웹 검색 | DuckDuckGo 기반 검색 및 결과 요약 |
| 데스크톱 알림 | Windows 토스트 알림 전송 |
| 스케줄러 | 반복 작업 예약 실행 |
| 대화 기억 | 대화·작업 이력 JSON 영속 저장 |

---

## 프로젝트 구조

```
Agentic_AI/
├── main.py              # 진입점 (CLI 대화형 / 스케줄러 모드)
├── agent/
│   ├── core.py          # 메인 에이전트 루프 (LLM + 도구 호출)
│   └── memory.py        # 대화·작업 기억 (JSON 영속 저장)
├── tools/
│   ├── system_tools.py  # CPU·RAM·디스크 모니터링, 프로세스 관리
│   ├── file_tools.py    # 파일 탐색·이동·삭제·정리
│   ├── scheduler.py     # 작업 예약·반복 실행
│   ├── web_tools.py     # 웹 검색 (DuckDuckGo)
│   └── notify.py        # 데스크톱 알림
├── config/
│   └── settings.py      # .env 기반 전역 설정 로더
├── memory/              # 대화·작업 이력 저장소 (git 제외)
├── logs/                # 실행 로그 (git 제외)
├── .env.example         # 환경변수 템플릿
└── requirements.txt
```

---

## 시작하기

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열고 Anthropic API 키를 입력한다.

```env
ANTHROPIC_API_KEY=your_api_key_here
```

> API 키는 [Anthropic Console](https://console.anthropic.com) 에서 발급받는다.

### 3. 실행

```bash
# 대화형 모드
python main.py

# 백그라운드 스케줄러 모드
python main.py --mode scheduler
```

---

## 환경변수 목록

| 키 | 필수 | 기본값 | 설명 |
|----|------|--------|------|
| `ANTHROPIC_API_KEY` | ✅ | — | Anthropic API 인증 키 |
| `AGENT_MODEL` | | `claude-sonnet-4-6` | 사용할 LLM 모델 |
| `AGENT_MAX_TOKENS` | | `4096` | 응답 최대 토큰 수 |
| `LOG_LEVEL` | | `INFO` | 로그 레벨 (DEBUG/INFO/WARNING/ERROR) |
| `SCHEDULER_INTERVAL` | | `60` | 스케줄러 실행 주기 (초) |
| `ENABLE_NOTIFICATIONS` | | `true` | 윈도우 토스트 알림 활성화 여부 |

---

## 사용 예시

```
사용자: 지금 CPU 얼마나 쓰고 있어?
에이전트: 현재 CPU 사용률은 23%입니다. 코어 수는 12개이며, 메모리는 16GB 중 9.2GB 사용 중입니다.

사용자: 다운로드 폴더 정리해줘
에이전트: C:\Users\User\Downloads 폴더를 정리했습니다. 이미지 12개, 문서 5개, 압축파일 3개를 각 폴더로 이동했습니다.
```

---

## 기술 스택

- **LLM**: Claude (Anthropic) — `claude-sonnet-4-6`
- **언어**: Python 3.10+
- **주요 라이브러리**: `anthropic`, `psutil`, `duckduckgo-search`, `winotify`

---

## 의존성 관리 원칙

- `requirements.txt`는 삭제 없이 누적 기록한다 — PC 교체 시 동일 환경 복원 목적
- 버전 업그레이드 시 구버전을 주석으로 보존해 즉시 롤백 가능하도록 유지한다

```bash
pip install -r requirements.txt
```

---

## 라이선스

개인 프로젝트 — 별도 라이선스 미지정
