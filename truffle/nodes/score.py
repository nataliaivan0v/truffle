from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from truffle.state import JobPosting
import time

class Score(BaseModel):
    score: float = Field(
        ge=0, le=100,
        description="0-100 fit score. 0=irrelevant, 50=plausible, "
                    "80+=strong match, 95+=ideal."
    )
    reasoning: str = Field(
        description="One or two sentences explaining the score. "
                    "Reference specific overlaps (or gaps) with the candidate profile."
    )

SCORER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You score job postings against a candidate's profile on a 0-100 scale.\n\n"
     "HARD CONSTRAINTS — violations cap the score at 25:\n"
     "- Location must overlap with the candidate's locations\n"
     "- Work arrangement must match (e.g. don't recommend 'remote-only' if "
     "candidate wants in-person/hybrid)\n"
     "- Seniority must match — if posting requires 5+ years, or says "
     "'senior/staff/principal/lead', it does NOT fit an entry-level candidate\n"
     "- If salary is stated and below the candidate's minimum, cap at 25\n"
     "- Any deal-breaker present → cap at 20\n\n"
     "Within those constraints, score on fit:\n"
     "- 90+: Role, stage, skills, interests all align strongly\n"
     "- 70-89: Good fit, minor gaps\n"
     "- 50-69: Plausible but with notable mismatches\n"
     "- 30-49: Weak fit\n"
     "- 0-29: Bad fit or hard-constraint violation\n\n"
     "Be honest. A bad score is more useful than an inflated one. "
     "If salary or seniority isn't mentioned in the posting, note that in the "
     "reasoning but don't auto-penalize — score the rest of the fit normally."),
    ("user",
     "Candidate profile:\n{profile}\n\n"
     "Job posting:\n"
     "Company: {company}\nRole: {role}\nLocation: {location}\n"
     "Stage: {stage}\nTech: {tech}\n\n"
     "Full text:\n{text}"),
])

_llm = ChatAnthropic(model="claude-haiku-4-5", max_tokens=400)
_scorer = SCORER_PROMPT | _llm.with_structured_output(Score)

def score_postings(
    postings: list[JobPosting],
    profile: dict,
    chunk_size: int = 10,
    pause_seconds: int = 12,
) -> list[JobPosting]:
    if not postings:
        return []

    profile_str = (
        f"- Experience: {profile['years_experience']} years (early-career)\n"
        f"- Seniority levels OK: {', '.join(profile['seniority'])}\n"
        f"- Roles wanted: {', '.join(profile['desired_roles'])}\n"
        f"- Stages wanted: {', '.join(profile['desired_stages'])}\n"
        f"- Locations: {', '.join(profile['locations'])}\n"
        f"- Work arrangement: {', '.join(profile['work_arrangement'])}\n"
        f"- Minimum salary: ${profile['min_salary_usd']:,}\n"
        f"- Skills: {', '.join(profile['skills'])}\n"
        f"- Interests: {', '.join(profile['interests'])}\n"
        f"- Deal-breakers: {', '.join(profile['deal_breakers']) or 'none'}"
    )

    all_results: list[Score] = []
    num_chunks = (len(postings) + chunk_size - 1) // chunk_size

    for i in range(0, len(postings), chunk_size):
        chunk = postings[i:i + chunk_size]
        inputs = [
            {
                "profile": profile_str,
                "company": p["company"] or "Unknown",
                "role": p["role"] or "Unknown",
                "location": p["location"] or "Unknown",
                "stage": p["stage"] or "unknown",
                "tech": ", ".join(p["tech_stack"]) or "unspecified",
                "text": p["raw_text"][:800],
            }
            for p in chunk
        ]
        chunk_num = i // chunk_size + 1
        print(f"[score] chunk {chunk_num}/{num_chunks} ({len(chunk)} postings)...")
        results = _scorer.batch(inputs, config={"max_concurrency": 3})
        all_results.extend(results)

        if i + chunk_size < len(postings):
            time.sleep(pause_seconds)

    for posting, result in zip(postings, all_results):
        posting["score"] = result.score
        posting["score_reasoning"] = result.reasoning

    postings.sort(key=lambda p: p["score"] or 0, reverse=True)
    print(f"[score] done — top score: {postings[0]['score'] if postings else 'n/a'}")
    return postings

def score_node(state: dict) -> dict:
    return {"scored": score_postings(state["extracted"], state["profile"])}