"""채용 도구 - 채용공고 크롤링, 회사 인재상 분석, 자소서 저장, 맞춤 브리핑 기능을 제공한다."""

import json
import re
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from config import settings

# ── 경로 상수 ─────────────────────────────────────────────────────────────────

RESUME_PROFILE_PATH = settings.MEMORY_DIR / "resume_profile.json"
COVER_LETTERS_DIR   = settings.MEMORY_DIR / "cover_letters"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


# ── 이력서 프로필 ─────────────────────────────────────────────────────────────

def save_resume_profile(profile: dict) -> dict:
    """이력서 프로필을 JSON 파일로 저장한다."""
    try:
        RESUME_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(RESUME_PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
        return {"결과": "성공", "저장_경로": str(RESUME_PROFILE_PATH)}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def load_resume_profile() -> dict:
    """저장된 이력서 프로필을 불러온다."""
    try:
        if not RESUME_PROFILE_PATH.exists():
            return {
                "결과": "없음",
                "이유": "저장된 프로필이 없습니다. save_resume_profile 도구로 먼저 저장해 주세요.",
            }
        with open(RESUME_PROFILE_PATH, "r", encoding="utf-8") as f:
            return {"결과": "성공", "프로필": json.load(f)}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


# ── 채용공고 크롤링 ───────────────────────────────────────────────────────────

def _crawl_saramin(keyword: str, count: int) -> list[dict]:
    """사람인 검색 결과를 크롤링한다."""
    url = (
        "https://www.saramin.co.kr/zf_user/search/recruit"
        f"?searchType=search&searchword={quote_plus(keyword)}"
        f"&recruitPage=1&recruitSort=relation&recruitPageCount={count}"
    )
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        jobs = []
        for item in soup.select(".item_recruit")[:count]:
            title_tag   = item.select_one(".job_tit a")
            company_tag = item.select_one(".corp_name a")
            cond_tags   = item.select(".job_condition span")
            date_tag    = item.select_one(".job_date .date")

            if not title_tag:
                continue

            href = title_tag.get("href", "")
            job_url = f"https://www.saramin.co.kr{href}" if href.startswith("/") else href

            jobs.append({
                "제목":   title_tag.get_text(strip=True),
                "회사":   company_tag.get_text(strip=True) if company_tag else "미상",
                "조건":   " | ".join(c.get_text(strip=True) for c in cond_tags),
                "마감일": date_tag.get_text(strip=True) if date_tag else "미상",
                "URL":    job_url,
                "출처":   "사람인",
            })
        return jobs
    except Exception as e:
        return [{"오류": f"사람인 크롤링 실패: {e}"}]


def _crawl_wanted(keyword: str, count: int) -> list[dict]:
    """원티드 검색 결과를 크롤링한다."""
    # 원티드 검색 페이지 직접 파싱
    url = f"https://www.wanted.co.kr/search?query={quote_plus(keyword)}&tab=positions"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        jobs = []
        for item in soup.select("li.Card_Card__WdaUH, li[class*='JobCard'], .job-card")[:count]:
            title_tag   = item.select_one("strong, .job-card-position, h6")
            company_tag = item.select_one(".job-card-company, span[class*='company']")
            link_tag    = item.select_one("a[href]")

            if not title_tag:
                continue

            href = link_tag.get("href", "") if link_tag else ""
            job_url = f"https://www.wanted.co.kr{href}" if href.startswith("/") else href

            jobs.append({
                "제목": title_tag.get_text(strip=True),
                "회사": company_tag.get_text(strip=True) if company_tag else "미상",
                "조건": "",
                "마감일": "상시",
                "URL":  job_url or f"https://www.wanted.co.kr/search?query={quote_plus(keyword)}",
                "출처": "원티드",
            })
        return jobs
    except Exception as e:
        return [{"오류": f"원티드 크롤링 실패: {e}"}]


def crawl_job_postings(keyword: str, site: str = "all", count: int = 10) -> dict:
    """채용 사이트에서 공고를 크롤링한다.

    Args:
        keyword: 검색 키워드 (예: "행정사무", "회계")
        site:    크롤링 대상 사이트. 'saramin' | 'wanted' | 'all'
        count:   사이트당 최대 공고 수
    """
    results: list[dict] = []

    if site in ("saramin", "all"):
        results.extend(_crawl_saramin(keyword, count))
    if site in ("wanted", "all"):
        results.extend(_crawl_wanted(keyword, count))

    # 오류 항목 분리
    errors  = [r for r in results if "오류" in r]
    postings = [r for r in results if "오류" not in r]

    return {
        "키워드":    keyword,
        "공고_수":   len(postings),
        "공고_목록": postings,
        "오류":      errors if errors else None,
    }


# ── 회사 인재상 분석 ──────────────────────────────────────────────────────────

def analyze_company_culture(company_name: str) -> dict:
    """DuckDuckGo 검색으로 회사 인재상·기업문화·복지 정보를 수집한다.
    반환된 데이터를 바탕으로 에이전트(LLM)가 자소서 작성 포인트를 분석한다.
    """
    from tools.web_tools import search_duckduckgo

    queries = [
        f"{company_name} 인재상 핵심가치",
        f"{company_name} 기업문화 복지 채용",
    ]

    search_results = []
    for q in queries:
        res = search_duckduckgo(q, max_results=4)
        search_results.extend(res.get("결과", []))

    return {
        "회사명":      company_name,
        "검색_결과":   search_results[:8],
        "분석_가이드": (
            f"위 검색 결과를 바탕으로 {company_name}의 인재상, 핵심 가치, "
            "지원자가 자소서에 반드시 반영해야 할 포인트를 3~5가지로 정리해 주세요."
        ),
    }


# ── 자소서 저장 ───────────────────────────────────────────────────────────────

def save_cover_letter(company: str, job_title: str, content: str) -> dict:
    """LLM이 생성한 자소서를 텍스트 파일로 저장한다."""
    try:
        COVER_LETTERS_DIR.mkdir(parents=True, exist_ok=True)

        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_co     = re.sub(r'[\\/:*?"<>|]', "_", company)
        safe_title  = re.sub(r'[\\/:*?"<>|]', "_", job_title)
        filename    = f"{timestamp}_{safe_co}_{safe_title}.txt"
        filepath    = COVER_LETTERS_DIR / filename

        header = (
            f"회사:   {company}\n"
            f"직무:   {job_title}\n"
            f"작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"{'=' * 60}\n\n"
        )
        filepath.write_text(header + content, encoding="utf-8")

        return {"결과": "성공", "저장_경로": str(filepath), "파일명": filename}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


def list_cover_letters() -> dict:
    """저장된 자소서 목록을 최신순으로 반환한다."""
    try:
        if not COVER_LETTERS_DIR.exists():
            return {"결과": "없음", "총_개수": 0, "목록": []}

        files = sorted(COVER_LETTERS_DIR.glob("*.txt"), reverse=True)
        letters = []
        for f in files:
            size = f.stat().st_size
            letters.append({
                "파일명": f.name,
                "경로":  str(f),
                "크기":  f"{size // 1024}KB" if size >= 1024 else f"{size}B",
            })
        return {"결과": "성공", "총_개수": len(letters), "목록": letters}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


# ── 맞춤 공고 브리핑 ─────────────────────────────────────────────────────────

def get_job_briefing(keywords: list, count_per_keyword: int = 5) -> dict:
    """키워드 목록으로 맞춤 공고 브리핑을 생성한다.

    Args:
        keywords:          검색 키워드 목록 (예: ["행정사무", "회계사무", "손해평가"])
        count_per_keyword: 키워드당 최대 공고 수
    """
    briefing: dict = {
        "브리핑_일시":   datetime.now().strftime("%Y-%m-%d %H:%M"),
        "검색_키워드":   keywords,
        "공고_목록":     [],
        "키워드별_현황": {},
    }

    for kw in keywords:
        result  = crawl_job_postings(kw, site="all", count=count_per_keyword)
        postings = result.get("공고_목록", [])
        for job in postings:
            job["검색_키워드"] = kw
        briefing["공고_목록"].extend(postings)
        briefing["키워드별_현황"][kw] = len(postings)

    briefing["총_공고_수"] = len(briefing["공고_목록"])
    return briefing


# ── 채용공고 상세 조회 ────────────────────────────────────────────────────────

def fetch_job_detail(url: str) -> dict:
    """채용공고 URL에서 상세 내용(직무 요건·우대 조건·회사 소개)을 가져온다.
    자소서 맞춤 작성에 필요한 핵심 정보를 추출한다.
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # 스크립트·스타일 제거
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # 핵심 섹션 키워드로 슬라이싱 (긴 텍스트 정리)
        keywords = ["담당업무", "자격요건", "우대사항", "복지", "혜택", "회사 소개", "기업 소개"]
        sections: dict[str, str] = {}
        lines = text.split("\n")
        current_key = "기타"
        buffer: list[str] = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            matched = next((k for k in keywords if k in line), None)
            if matched:
                if buffer:
                    sections[current_key] = " ".join(buffer[:30])
                current_key = matched
                buffer = []
            else:
                buffer.append(line)

        if buffer:
            sections[current_key] = " ".join(buffer[:30])

        return {
            "결과":   "성공",
            "URL":    url,
            "섹션":   sections,
            "전문":   text[:2000],  # 전체 텍스트도 앞부분 제공
        }
    except Exception as e:
        return {"결과": "실패", "URL": url, "이유": str(e)}


# ── 자소서 팩트체크 ──────────────────────────────────────────────────────────

def _collect_profile_facts(profile: dict) -> set[str]:
    """프로필 dict에서 팩트체크에 쓸 키워드 집합을 추출한다."""
    facts: set[str] = set()
    for cert in profile.get("자격증", []):
        facts.add(cert.get("자격명", "").replace(" ", "").lower())
    for edu in profile.get("학력", []) + profile.get("교육_이수", []):
        facts.add(edu.get("학교명", edu.get("기관", "")).replace(" ", "").lower())
        facts.add(edu.get("전공", edu.get("과정", "")).replace(" ", "").lower())
    for act in profile.get("활동_경험", []):
        facts.add(act.get("활동", "").replace(" ", "").lower())
    for tech_list in profile.get("기술_스택", {}).values():
        for tech in tech_list:
            facts.add(str(tech).replace(" ", "").lower())
    for career in profile.get("경력", []):
        facts.add(career.get("근무처", "").replace(" ", "").lower())
    return {f for f in facts if f}


def validate_cover_letter(cover_letter_text: str) -> dict:
    """자소서 내용을 resume_profile.json 과 대조해 프로필에 없는 내용을 탐지한다.

    저장된 프로필의 자격증·경력·활동·학력 등 핵심 항목을 추출한 뒤,
    자소서에서 프로필에 없는 주요 주장이 있으면 경고 목록으로 반환한다.
    """
    try:
        profile_result = load_resume_profile()
        if profile_result["결과"] != "성공":
            return {"결과": "실패", "이유": "프로필을 불러올 수 없습니다."}

        facts = _collect_profile_facts(profile_result["프로필"])

        # 자소서에서 의심 패턴 탐지 ─ 자격증·수상·경력 언급 문장 추출
        suspicious_patterns = [
            r"[\w가-힣]+\s*[1-9]급",          # ○○ N급 자격증
            r"수상",                            # 수상 경력
            r"인턴",                            # 인턴십
            r"[\w가-힣]+\s*자격증",             # ○○ 자격증
            r"[\d]+년\s*(?:간|동안|의)\s*경력", # N년 경력
            r"프로젝트\s*(?:수행|진행|참여)",    # 프로젝트 경험
        ]

        warnings: list[str] = []
        lines = cover_letter_text.split("\n")

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            for pattern in suspicious_patterns:
                if re.search(pattern, line_stripped):
                    # 해당 라인의 핵심 명사가 프로필에 있는지 간단 확인
                    line_key = re.sub(r"[^\w가-힣]", "", line_stripped).lower()
                    matched = any(f and f in line_key for f in facts if len(f) > 2)
                    if not matched:
                        warnings.append(line_stripped[:80])
                    break  # 한 줄에 중복 경고 방지

        # 중복 제거
        warnings = list(dict.fromkeys(warnings))

        if warnings:
            return {
                "결과": "경고",
                "경고_수": len(warnings),
                "의심_문장": warnings,
                "안내": "위 문장들이 프로필에서 확인되지 않았습니다. 사용자에게 확인을 요청하세요.",
            }
        return {
            "결과": "통과",
            "안내": "프로필 기반으로 검토한 결과 명백한 불일치 항목이 발견되지 않았습니다.",
        }
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}


# ── 지원 링크 열기 ────────────────────────────────────────────────────────────

def open_job_posting(url: str) -> dict:
    """채용 공고 URL을 기본 브라우저로 열어 지원 페이지로 이동한다."""
    try:
        if not url.startswith(("http://", "https://")):
            return {"결과": "실패", "이유": "유효하지 않은 URL 형식입니다."}
        webbrowser.open(url)
        return {"결과": "성공", "열린_URL": url}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
