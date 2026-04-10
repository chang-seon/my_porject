"""웹 도구 - 웹 검색 및 페이지 스크래핑 기능을 제공한다."""

import requests
from bs4 import BeautifulSoup


def fetch_page(url: str, timeout: int = 10) -> dict:
    """지정 URL 의 텍스트 내용을 가져온다."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (AgentAI/1.0)"}
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        # 스크립트·스타일 태그 제거
        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # 너무 긴 내용은 잘라서 반환
        return {
            "결과": "성공",
            "url": url,
            "내용": text[:3000] + ("..." if len(text) > 3000 else ""),
        }
    except requests.RequestException as e:
        return {"결과": "실패", "url": url, "이유": str(e)}


def search_duckduckgo(query: str, max_results: int = 5) -> dict:
    """DuckDuckGo HTML 검색으로 결과를 가져온다 (API 키 불필요)."""
    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {"User-Agent": "Mozilla/5.0 (AgentAI/1.0)"}
        resp = requests.post(url, data={"q": query}, headers=headers, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for result in soup.select(".result__body")[:max_results]:
            title_tag = result.select_one(".result__title")
            snippet_tag = result.select_one(".result__snippet")
            link_tag = result.select_one(".result__url")
            results.append({
                "제목": title_tag.get_text(strip=True) if title_tag else "",
                "요약": snippet_tag.get_text(strip=True) if snippet_tag else "",
                "url": link_tag.get_text(strip=True) if link_tag else "",
            })

        return {"검색어": query, "결과 수": len(results), "결과": results}
    except Exception as e:
        return {"결과": "실패", "이유": str(e)}
