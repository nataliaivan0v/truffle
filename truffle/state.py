from typing import TypedDict, Annotated
from operator import add


class JobPosting(TypedDict):
    source: str
    source_url: str
    raw_text: str
    company: str | None
    role: str | None
    location: str | None
    stage: str | None
    tech_stack: list[str]
    is_real_job: bool | None
    score: float | None
    score_reasoning: str | None
    summary: str | None


class TruffleState(TypedDict):
    profile: dict

    raw_postings: Annotated[list[JobPosting], add]
    raw_postings_deduped: list[JobPosting]

    classified: list[JobPosting]
    extracted: list[JobPosting]
    scored: list[JobPosting]
    digest: str