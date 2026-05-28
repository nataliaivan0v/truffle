from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from truffle.state import JobPosting
import time

class ExtractedFields(BaseModel):
    company: str = Field(description="Company name. If unclear, use 'Unknown'.")
    role: str = Field(
        description="The role being hired for. If multiple, pick the most "
                    "engineering-focused one. Keep concise (e.g. 'Senior Backend Engineer')."
    )
    location: str = Field(
        description="Location or 'Remote'. Use comma-separated cities if multiple. "
                    "If unclear, use 'Unknown'."
    )
    stage: str = Field(
        description="Best guess at company stage. One of: "
                    "'seed', 'series-a', 'series-b', 'series-c+', 'public', 'unknown'."
    )
    tech_stack: list[str] = Field(
        description="Technologies mentioned (languages, frameworks, tools). "
                    "Empty list if none mentioned. Lowercase, deduped."
    )

EXTRACTOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "Extract structured fields from a job posting. Be concise and accurate. "
     "If a field isn't clearly stated, use 'Unknown' rather than guessing. "
     "For 'stage': infer from context (e.g. 'YC W24' → seed, 'Series A' → series-a, "
     "a Fortune 500 company → public). When truly unclear, use 'unknown'."),
    ("user", "Source: {source}\nPre-known stage hint: {stage_hint}\n\nPosting:\n{text}"),
])

_llm = ChatAnthropic(model="claude-sonnet-4-5", max_tokens=500)
_extractor = EXTRACTOR_PROMPT | _llm.with_structured_output(ExtractedFields)

def extract_postings(
    postings: list[JobPosting],
    chunk_size: int = 6,
    pause_seconds: int = 15,
) -> list[JobPosting]:
    if not postings:
        return []

    all_results: list[ExtractedFields] = []
    num_chunks = (len(postings) + chunk_size - 1) // chunk_size

    for i in range(0, len(postings), chunk_size):
        chunk = postings[i:i + chunk_size]
        inputs = [
            {
                "source": p["source"],
                "stage_hint": p.get("stage") or "none",
                "text": p["raw_text"][:3000],
            }
            for p in chunk
        ]
        chunk_num = i // chunk_size + 1
        print(f"[extract] chunk {chunk_num}/{num_chunks} ({len(chunk)} postings)...")
        results = _extractor.batch(inputs, config={"max_concurrency": 3})
        all_results.extend(results)

        if i + chunk_size < len(postings):
            time.sleep(pause_seconds)

    for posting, result in zip(postings, all_results):
        posting["company"] = result.company
        posting["role"] = result.role
        posting["location"] = result.location
        if not posting.get("stage") or posting["stage"] == "unknown":
            posting["stage"] = result.stage
        posting["tech_stack"] = result.tech_stack

    print(f"[extract] done — {len(all_results)} extractions")
    return postings

def extract_node(state: dict) -> dict:
    return {"extracted": extract_postings(state["classified"])}