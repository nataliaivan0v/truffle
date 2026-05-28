import requests

from truffle.state import JobPosting
from truffle.fetchers.hn import get_item, clean_html

JOBSTORIES_URL = "https://hacker-news.firebaseio.com/v0/jobstories.json"

def fetch_yc_jobs(max_postings: int = 30) -> list[JobPosting]:
    r = requests.get(JOBSTORIES_URL, timeout=10)
    r.raise_for_status()
    job_ids = r.json()[:max_postings]
    print(f"[yc] fetching {len(job_ids)} YC job posts")

    postings: list[JobPosting] = []
    for jid in job_ids:
        item = get_item(jid)
        if not item or item.get("deleted") or item.get("dead"):
            continue

        title = item.get("title", "")
        body = clean_html(item.get("text", ""))
        external_url = item.get("url", "")

        parts = [title]
        if body:
            parts.append(body)
        if external_url:
            parts.append(f"Apply: {external_url}")
        raw_text = "\n\n".join(parts).strip()

        if len(raw_text) < 30:
            continue

        postings.append(JobPosting(
            source="yc",
            source_url=f"https://news.ycombinator.com/item?id={jid}",
            raw_text=raw_text,
            company=None, role=None, location=None,
            stage="early",
            tech_stack=[],
            is_real_job=None,
            score=None,
            score_reasoning=None,
            summary=None,
        ))
    return postings

def yc_node(state: dict) -> dict:
    return {"raw_postings": fetch_yc_jobs()}