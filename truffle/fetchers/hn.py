import html
import re
import requests
from bs4 import BeautifulSoup

from truffle.state import JobPosting

HN_API = "https://hacker-news.firebaseio.com/v0"
HN_SEARCH = "https://hn.algolia.com/api/v1/search_by_date"

def find_latest_whoishiring_thread() -> int | None:
    params = {
        "query": "Ask HN: Who is hiring?",
        "tags": "story,author_whoishiring",
        "hitsPerPage": 5,
    }
    r = requests.get(HN_SEARCH, params=params, timeout=10)
    r.raise_for_status()
    hits = r.json().get("hits", [])
    hits.sort(key=lambda h: h.get("created_at_i", 0), reverse=True)
    return int(hits[0]["objectID"]) if hits else None

def get_item(item_id: int) -> dict | None:
    r = requests.get(f"{HN_API}/item/{item_id}.json", timeout=10)
    r.raise_for_status()
    return r.json()

def clean_html(raw: str) -> str:
    if not raw:
        return ""
    text = BeautifulSoup(raw, "html.parser").get_text(separator="\n")
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text

def fetch_hn(max_postings: int = 50) -> list[JobPosting]:
    thread_id = find_latest_whoishiring_thread()
    if not thread_id:
        print("[hn] no thread found")
        return []

    thread = get_item(thread_id)
    if not thread:
        return []

    comment_ids = thread.get("kids", [])[:max_postings]
    print(f"[hn] thread {thread_id}, fetching {len(comment_ids)} comments")

    postings: list[JobPosting] = []
    for cid in comment_ids:
        c = get_item(cid)
        if not c or c.get("deleted") or c.get("dead"):
            continue
        text = clean_html(c.get("text", ""))
        if len(text) < 50:
            continue
        postings.append(JobPosting(
            source="hackernews",
            source_url=f"https://news.ycombinator.com/item?id={cid}",
            raw_text=text,
            company=None,
            role=None,
            location=None,
            stage=None,
            tech_stack=[],
            is_real_job=None,
            score=None,
            score_reasoning=None,
            summary=None,
        ))
    return postings

def hn_node(state: dict) -> dict:
    postings = fetch_hn(max_postings=50)
    return {"raw_postings": postings}