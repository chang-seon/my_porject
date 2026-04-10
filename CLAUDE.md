# Agentic AI - PC 관리 에이전트

## 언어 사용 규칙

- **모든 응답과 설명은 한국어로 작성한다.**
- 코드 내 주석은 한국어로 작성한다.
- 변수명·함수명·클래스명은 영어(snake_case / PascalCase)로 작성한다.
- 오류 메시지와 로그 출력도 한국어로 작성한다.
- 기술 용어(API, LLM, token 등)는 영어 원어 그대로 사용한다.

## 프로젝트 개요

사용자의 PC에서 자율적으로 동작하는 에이전트 AI.
귀찮은 반복 작업을 자동화하고, 시스템 상태를 모니터링하며, 필요 시 사용자에게 알림을 전송한다.

## 아키텍처

```
Agentic_AI/
├── main.py              # 진입점 (CLI / 대화형 모드)
├── agent/
│   ├── core.py          # 메인 에이전트 루프 (LLM + 도구 호출)
│   ├── memory.py        # 대화·작업 기억 (JSON 영속 저장)
│   └── planner.py       # 작업 계획 및 분해
├── tools/
│   ├── system_tools.py  # CPU·RAM·디스크 모니터링, 프로세스 관리
│   ├── file_tools.py    # 파일 탐색·이동·삭제·정리
│   ├── scheduler.py     # 작업 예약·반복 실행
│   ├── web_tools.py     # 웹 검색·페이지 스크래핑
│   └── notify.py        # 데스크톱 알림·로그 알림
├── config/
│   └── settings.py      # 전역 설정 로더
├── memory/              # 에이전트 기억 저장소 (JSON)
├── logs/                # 실행 로그
├── .env                 # API 키 등 민감 정보 (git 제외)
├── .env.example         # 환경변수 템플릿
└── requirements.txt
```

## 개발 규칙

- 새 도구(tool)는 `tools/` 아래에 모듈로 추가한다.
- 모든 도구 함수는 `dict` 를 반환해 에이전트가 결과를 파싱하기 쉽게 한다.
- 민감 정보(API 키, 경로)는 반드시 `.env`에서 읽고, 코드에 하드코딩하지 않는다.
- 에이전트가 파일·시스템에 변경을 가할 때는 로그에 반드시 기록한다.
- 파괴적 작업(파일 삭제, 프로세스 종료)은 사용자 확인 후 실행한다.

## 의존성 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
# 대화형 모드
python main.py

# 백그라운드 스케줄러 모드
python main.py --mode scheduler
```

---

## 환경변수 목록

`.env` 파일에 아래 키가 반드시 존재해야 한다. `.env.example` 참고.

| 키 | 필수 | 기본값 | 설명 |
|----|------|--------|------|
| `ANTHROPIC_API_KEY` | ✅ | 없음 | Anthropic API 인증 키 |
| `AGENT_MODEL` | - | `claude-sonnet-4-6` | 사용할 LLM 모델 ID |
| `AGENT_MAX_TOKENS` | - | `4096` | 응답 최대 토큰 수 |
| `LOG_LEVEL` | - | `INFO` | 로그 레벨 (DEBUG/INFO/WARNING/ERROR) |
| `SCHEDULER_INTERVAL` | - | `60` | 스케줄러 실행 주기 (초) |
| `ENABLE_NOTIFICATIONS` | - | `true` | 윈도우 토스트 알림 활성화 여부 |

- `settings.py` 외부에서 `os.getenv()`를 직접 호출하지 않는다. 모든 설정 값은 `config.settings`에서 import해서 사용한다.

---

## 도구 반환 스키마

도구 함수의 반환 형식은 용도에 따라 두 가지 패턴을 따른다.

**조회(read-only) 함수** — 도메인 키를 직접 반환한다.
```python
# 예: get_system_status(), list_top_processes()
return {"cpu": {...}, "memory": {...}, "disk": {...}}
```

**변경·파괴 작업 함수** — 결과/실패 여부를 명시한다.
```python
# 성공
return {"결과": "성공", "원본": src, "대상": dst}
# 실패
return {"결과": "실패", "이유": "한국어로 된 원인 설명"}
# 사용자 미확인으로 취소
return {"결과": "취소됨", "이유": "confirm=True 로 호출해야 삭제가 실행됩니다."}
```

---

## 에러 처리 패턴

모든 도구 함수는 예외를 함수 밖으로 전파하지 않는다. `core.py`의 `_run_tool`은 핸들러 반환값을 그대로 JSON 직렬화하므로, 예외가 전파되면 에이전트 루프 전체가 중단된다.

```python
def some_tool(path: str) -> dict:
    try:
        # 작업 수행
        return {"결과": "성공", ...}
    except PermissionError:
        return {"결과": "실패", "이유": "접근 권한이 없습니다."}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
```

---

## 보호 컴포넌트 수정 승인 절차

**핵심 컴포넌트를 수정하지 않으면 구현이 불가능한 상황이 발생할 수 있다.**
그 경우 아래 절차를 반드시 따른다. 사용자 승인 없이 임의로 수정하지 않는다.

### 절차

1. **작업 중단** — 보호 컴포넌트 수정이 필요한 시점에서 즉시 멈춘다.
2. **이유 보고** — 아래 형식으로 사용자에게 설명한다.

   ```
   [보호 컴포넌트 수정 요청]
   - 수정 대상 파일: <파일 경로>
   - 수정이 필요한 이유: <왜 이 파일을 건드리지 않으면 구현이 불가능한지>
   - 변경 범위: <어떤 부분을 어떻게 바꿀 것인지>
   - 발생 가능한 부작용: <수정으로 인해 영향을 받을 수 있는 다른 코드>
   승인하시면 진행하겠습니다.
   ```

3. **승인 대기** — 사용자가 명시적으로 승인("응", "ㅇㅇ", "해줘", "ok" 등)한 경우에만 수정을 진행한다.
4. **수정 후 보고** — 수정 완료 후 변경된 내용을 간략히 요약한다.

### 보호 대상 컴포넌트 목록

| 파일 | 보호 이유 |
|------|-----------|
| `agent/core.py` — `TOOLS` / `TOOL_HANDLERS` | LLM 도구 선언과 실행 핸들러의 쌍 — 불일치 시 에이전트 루프 오류 |
| `agent/core.py` — `_run_agent_loop` | Anthropic multi-turn tool use 프로토콜 — 변경 시 API 오류 |
| `agent/memory.py` — `get_messages()` | Anthropic API 입력 형식 — 필드 추가 시 API 오류 |
| `config/settings.py` — `validate()` | API 키 미설정 방어선 — 삭제 시 에이전트가 키 없이 실행됨 |
| `tools/file_tools.py` — `delete_file` confirm 가드 | 파괴적 작업 안전장치 — 제거 시 LLM이 직접 파일 삭제 가능 |

---

## 핵심 컴포넌트 수정 시 주의사항

기존에 동작하는 코드를 수정할 때 아래 규칙을 반드시 확인한다.

### `agent/core.py`

- **`TOOLS` ↔ `TOOL_HANDLERS` 쌍 유지**: 두 구조는 항상 같이 수정한다. 하나만 수정하면 LLM이 선언한 도구를 실행하지 못하거나, 미선언 도구가 실행되는 오류가 발생한다.
- **`_run_agent_loop` stop_reason 분기 수정 금지**: `"end_turn"` / `"tool_use"` 분기 처리와 `loop_messages.append({"role": "assistant", "content": response.content})` 형식은 Anthropic multi-turn tool use 프로토콜이다. 변경 시 API 오류가 발생한다.

### `agent/memory.py`

- **`get_messages()` 반환 형식 고정**: 반환 형식은 `[{"role": "...", "content": "..."}]`이어야 한다. `timestamp` 등 추가 필드를 포함시키면 Anthropic API 오류가 발생한다.
- **저장 경로 변경 시 마이그레이션 필요**: `MEMORY_DIR` 변경 시 기존 JSON 파일을 이전하지 않으면 대화 이력이 소실된다.

### `config/settings.py`

- **상수명 변경 시 전파 확인**: 상수명 변경(예: `ANTHROPIC_API_KEY`)은 이를 import하는 모든 파일(`agent/core.py`, `agent/memory.py` 등)을 함께 수정해야 한다.
- **`validate()` 함수 삭제 금지**: `PCAgent.__init__`에서 반드시 호출된다. 삭제하면 API 키 미설정 상태로 에이전트가 실행된다.

---

## 새 도구 추가 체크리스트

새 도구를 추가할 때 아래 순서를 모두 완료해야 한다.

```
[ ] 1. tools/ 아래 모듈에 함수 작성 — dict 반환, 예외 내부 처리
[ ] 2. 파괴적 작업이면 함수 시그니처에 confirm: bool = False 가드 추가
[ ] 3. agent/core.py TOOLS 리스트에 Anthropic tool 스키마 추가
[ ] 4. agent/core.py TOOL_HANDLERS 딕셔너리에 람다 핸들러 추가
[ ] 5. tools/__init__.py에 import 추가 여부 확인
[ ] 6. python main.py 로 직접 호출해 동작 확인
```

---

## 보안 규칙

### 미등록 위험 도구 보호

`system_tools.kill_process()`는 구현되어 있으나 `TOOL_HANDLERS`에 **의도적으로 등록되지 않았다**. LLM이 임의로 호출할 수 없도록 이 상태를 유지한다. 등록하려면 반드시 사용자 확인 UI를 `main.py`에 먼저 구현한 뒤 진행한다.

### 파일 접근 경계

파일 도구의 `path` 인수가 아래 시스템 경로를 가리킬 경우 작업을 거부해야 한다. 검증 로직을 `file_tools.py` 함수 내에 추가한다.

```
금지 경로 (Windows): C:\Windows, C:\Program Files, C:\Program Files (x86)
금지 경로 (공통):    /etc, /sys, /proc, /boot
```

### 셸 실행 금지

도구 함수 내에서 `subprocess`, `os.system`, `eval`, `exec`을 사용하지 않는다. 임의 명령 실행이 가능해져 에이전트가 악용될 수 있다.

### API 키 보호

- `.env`는 이미 `.gitignore`에 등록되어 있다. 절대 `git add .env`하지 않는다.
- 코드 어디에도 API 키 값을 문자열 리터럴로 작성하지 않는다.

### 파괴적 작업 confirm 패턴

`delete_file(confirm=False)` 패턴을 모든 파괴적 도구 함수에 동일하게 적용한다. LLM이 `confirm=True`를 직접 인수로 넘기지 못하도록, 사용자 확인 처리는 반드시 `main.py` UI 레이어에서 수행한다.

---

## requirements.txt 관리 규칙

### 원칙

- **삭제 금지**: 한 번 기록된 라이브러리는 코드에서 더 이상 사용하지 않더라도 절대 삭제하지 않는다. PC 교체 시 동일 환경 복원을 위한 영구 기록부다.
- **신규 추가 의무**: 새 라이브러리가 필요해지면 `pip install` 전후로 반드시 `requirements.txt`에 추가한다.

### 버전 업그레이드 시 절차

버전 업그레이드가 필요하다고 판단될 경우 아래 절차를 따른다.

1. **승인 요청**: 업그레이드 이유를 사용자에게 먼저 설명한다.
2. **승인 후 업데이트**: 사용자가 승인하면 기존 버전을 주석으로 보존한 채 새 버전으로 교체한다.

```
# anthropic>=0.40.0  (구버전 — 롤백 필요 시 주석 해제)
anthropic>=0.50.0
```

3. 롤백이 필요한 경우 새 버전 줄을 주석 처리하고 기존 버전 주석을 해제하면 즉시 복원된다.

---

## 로그 규칙

현재 `core.py`는 `print()`로 도구 실행을 출력한다. 향후 `logging` 모듈 도입 시 아래 규칙을 따른다.

- 로거 이름: 모듈 경로 그대로 사용 (`agent.core`, `tools.file_tools` 등)
- 레벨: `settings.LOG_LEVEL` 값 사용
- 포맷: `[%(asctime)s] %(levelname)s %(name)s - %(message)s`
- 파괴적 작업(삭제·이동·프로세스 종료) 실행은 반드시 `WARNING` 레벨 이상으로 기록한다.

---

## 미구현 컴포넌트

아래 파일은 아키텍처에 명시되어 있으나 아직 구현되지 않았다. 존재하지 않는 모듈을 import하는 코드를 작성하지 않는다.

| 파일 | 상태 | 예정 기능 |
|------|------|-----------|
| `agent/planner.py` | 미구현 | 복합 작업의 단계별 계획 수립 및 분해 |

---

## 자동 Git Push 규칙

### Push 원격 저장소

```
https://github.com/chang-seon/my_porject.git
```

### Push 트리거 조건

아래 두 조건 중 하나라도 충족되면 즉시 Push 절차를 실행한다.

| 조건 | 설명 |
|------|------|
| **개발 중단 명령** | 사용자가 "개발 그만", "중단", "여기까지", "멈춰" 등 개발 종료 의사를 표현할 때 |
| **일일 토큰 소진 임박** | 하루 Claude 토큰 사용량이 95% 소진되어 5%만 남았을 때 |

### Push 절차

트리거 조건 충족 시 아래 순서를 자동으로 실행한다.

```
1. git status 로 변경 파일 확인
2. .env 파일은 절대 staging 하지 않는다
3. README.md 를 현재 구현 상태에 맞게 최신화한다 (아래 규칙 적용)
4. 변경된 파일을 파일명 지정 방식으로 git add (README.md 포함)
5. 커밋 메시지 작성 (한국어, 변경 내용 요약)
6. git push https://github.com/chang-seon/my_porject.git main
7. Push 완료 여부를 사용자에게 보고한다
```

**README.md 최신화 기준 (3번 단계 적용)**

- 새 도구 추가/삭제 시 → 주요 기능 표 반영
- 새 파일 생성/삭제 시 → 프로젝트 구조 트리 업데이트
- `.env.example` 변경 시 → 환경변수 목록 업데이트
- 새 라이브러리 추가 시 → 기술 스택 반영
- 항상 한국어로 작성하되 코드 블록·명령어·기술 용어는 영어 원어 유지

### Push 시 커밋 메시지 형식

```
작업 요약 한 줄

- 변경 파일1: 변경 내용
- 변경 파일2: 변경 내용

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

### 주의사항

- Push 전 반드시 `.env`가 `.gitignore`에 포함되어 있는지 확인한다.
- 스테이징할 파일이 없으면 커밋 없이 Push만 시도한다.
- Push 실패 시 (인증 오류, 충돌 등) 오류 내용을 사용자에게 보고하고 강제 push는 절대 하지 않는다.
