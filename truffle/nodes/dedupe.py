from truffle.state import JobPosting

def _fingerprint(p: JobPosting) -> str:
    return (p["raw_text"] or "")[:120].lower().strip()

def dedupe_postings(postings: list[JobPosting]) -> list[JobPosting]:
    seen: set[str] = set()
    out: list[JobPosting] = []
    for p in postings:
        fp = _fingerprint(p)
        if fp in seen:
            continue
        seen.add(fp)
        out.append(p)
    print(f"[dedupe] kept {len(out)}/{len(postings)} after dedupe")
    return out

def dedupe_node(state: dict) -> dict:
    deduped = dedupe_postings(state["raw_postings"])
    return {"raw_postings_deduped": deduped}