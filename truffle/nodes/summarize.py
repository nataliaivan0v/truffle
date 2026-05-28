from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime
from truffle.state import JobPosting

SUMMARIZER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "Write a tight 2-3 sentence blurb about this job opportunity for a candidate's "
     "daily digest. Lead with what the company does, then the role's focus, then "
     "anything notable (comp, unusual perks, who they want). No fluff, no hype words "
     "('exciting opportunity', 'fast-paced'). Write in plain declarative prose."),
    ("user",
     "Company: {company}\nRole: {role}\nStage: {stage}\nLocation: {location}\n"
     "Tech: {tech}\n\nRaw posting:\n{text}"),
])

_llm = ChatAnthropic(model="claude-haiku-4-5", max_tokens=250)
_summarizer = SUMMARIZER_PROMPT | _llm | StrOutputParser()

def summarize_postings(
    postings: list[JobPosting], top_n: int = 10
) -> list[JobPosting]:
    if not postings:
        return []

    top = postings[:top_n]
    inputs = [
        {
            "company": p["company"] or "Unknown",
            "role": p["role"] or "Unknown",
            "stage": p["stage"] or "unknown",
            "location": p["location"] or "Unknown",
            "tech": ", ".join(p["tech_stack"]) or "unspecified",
            "text": p["raw_text"][:1500],
        }
        for p in top
    ]

    print(f"[summarize] summarizing top {len(top)} postings...")
    summaries: list[str] = _summarizer.batch(
        inputs, config={"max_concurrency": 2}
    )

    for posting, summary in zip(top, summaries):
        posting["summary"] = summary.strip()

    print(f"[summarize] done")
    return postings

def build_digest(postings: list[JobPosting], min_score: float = 50.0) -> str:
    today = datetime.now().strftime("%A, %B %d, %Y")
    qualifying = [p for p in postings if (p["score"] or 0) >= min_score and p.get("summary")]

    if not qualifying:
        return f"# Truffle Digest — {today}\n\n_No qualifying opportunities today._\n"

    lines = [
        f"# Truffle Digest — {today}",
        "",
        f"_{len(qualifying)} opportunities sniffed out from Hacker News + YC._",
        "",
    ]

    for i, p in enumerate(qualifying, 1):
        score = p["score"]
        company = p["company"] or "Unknown"
        role = p["role"] or "Unknown"
        loc = p["location"] or "Unknown"
        stage = p["stage"] or "unknown"
        tech = ", ".join(p["tech_stack"][:6]) or "—"

        lines.extend([
            f"## {i}. {company} — {role}  ·  **{score:.0f}/100**",
            "",
            f"**Location:** {loc}  ·  **Stage:** {stage}  ·  **Source:** {p['source']}",
            f"**Tech:** {tech}",
            "",
            p["summary"],
            "",
            f"**Why it matched:** {p['score_reasoning']}",
            "",
            f"[→ View posting]({p['source_url']})",
            "",
            "---",
            "",
        ])

    return "\n".join(lines)

def summarize_node(state: dict) -> dict:
    summarized = summarize_postings(state["scored"], top_n=10)
    digest = build_digest(summarized)
    return {"scored": summarized, "digest": digest}