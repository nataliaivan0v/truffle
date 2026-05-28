import os
import praw

from truffle.state import JobPosting

SUBREDDIT_QUERIES = [
    ("forhire", "[Hiring]"),
    ("startups", "hiring"),
    ("cscareerquestions", "hiring"),
    ("MachineLearningJobs", ""),
    ("remotejs", ""),
]

def _client() -> praw.Reddit:
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
    )

def fetch_reddit(per_subreddit: int = 15) -> list[JobPosting]:
    reddit = _client()
    reddit.read_only = True

    postings: list[JobPosting] = []
    for sub_name, query in SUBREDDIT_QUERIES:
        try:
            sub = reddit.subreddit(sub_name)
            if query:
                results = sub.search(query, sort="new", time_filter="week",
                                     limit=per_subreddit)
            else:
                results = sub.new(limit=per_subreddit)

            count = 0
            for post in results:
                title_low = post.title.lower()
                if "[for hire]" in title_low or "looking for" in title_low:
                    continue

                text = f"{post.title}\n\n{post.selftext}".strip()
                if len(text) < 50:
                    continue

                postings.append(JobPosting(
                    source="reddit",
                    source_url=f"https://reddit.com{post.permalink}",
                    raw_text=text,
                    company=None, role=None, location=None,
                    stage=None, tech_stack=[],
                    is_real_job=None, score=None,
                    score_reasoning=None, summary=None,
                ))
                count += 1
            print(f"[reddit] r/{sub_name}: {count} posts")
        except Exception as e:
            print(f"[reddit] r/{sub_name} failed: {e}")
            continue

    return postings

def reddit_node(state: dict) -> dict:
    return {"raw_postings": fetch_reddit()}