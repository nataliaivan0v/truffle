from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from truffle.state import JobPosting

class Classification(BaseModel):
    is_real_job: bool = Field(
        description="True if this is a legitimate, currently-open job posting "
                    "from a company hiring. False for noise: job-seeker posts, "
                    "replies/discussion, recruiters posting many unrelated roles, "
                    "expired listings, or anything not a real single opening."
    )
    reason: str = Field(
        description="One short sentence explaining the decision."
    )

CLASSIFIER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a hiring-signal classifier. You read raw text scraped from "
     "forums (Hacker News, YC jobs, etc.) and decide whether it represents "
     "a real, currently-open job opportunity at a company.\n\n"
     "REAL JOB posts: a company is hiring for one or a few specific roles, "
     "with enough info to apply (role title, company, contact/link, etc.)\n\n"
     "NOISE includes:\n"
     "- Job seekers advertising themselves ('I'm a senior dev looking for...')\n"
     "- Replies/comments ('great fit, just emailed you')\n"
     "- Meta-discussion ('this thread is quiet')\n"
     "- Recruiter dumps listing 10+ unrelated companies\n"
     "- Expired or unclear posts with no role info\n\n"
     "Be decisive. When in doubt, lean toward marking it noise."),
    ("user", "Source: {source}\n\nPosting:\n{text}"),
])

_llm = ChatAnthropic(model="claude-haiku-4-5", max_tokens=300)
_classifier = CLASSIFIER_PROMPT | _llm.with_structured_output(Classification)

def classify_postings(postings: list[JobPosting]) -> list[JobPosting]:
    if not postings:
        return []

    inputs = [
        {"source": p["source"], "text": p["raw_text"][:3000]}
        for p in postings
    ]

    print(f"[classify] running {len(inputs)} classifications in parallel...")
    results: list[Classification] = _classifier.batch(
        inputs, config={"max_concurrency": 2}
    )

    real_postings: list[JobPosting] = []
    for posting, result in zip(postings, results):
        posting["is_real_job"] = result.is_real_job
        if result.is_real_job:
            real_postings.append(posting)

    print(f"[classify] kept {len(real_postings)}/{len(postings)} as real jobs")
    return real_postings

def classify_node(state: dict) -> dict:
    real = classify_postings(state["raw_postings_deduped"])
    return {"classified": real}