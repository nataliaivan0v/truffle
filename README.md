# 🍄 Truffle

An open-source AI agent that sniffs out unposted and early-stage startup job opportunities, the kind that never make it to LinkedIn or Indeed.

Truffle ingests hiring signals from Hacker News' monthly "Who is hiring?" thread and the Y Combinator jobs feed, classifies real openings from noise, scores them against your candidate profile, and produces a daily markdown digest of the best matches.

## Architecture

An 8-node LangGraph flow with parallel source fetchers and conditional routing across classification, extraction, scoring, and summarization LLM calls.

```
       START
         │
    ┌────┴────┐         ← parallel fan-out
    ▼         ▼
 hn_fetch  yc_fetch
    │         │
    └────┬────┘         ← merged via list-concat reducer
         ▼
       dedupe
         │
         ▼
      classify          ← Haiku: real job vs noise
         │
         ▼
   route_after_classify ← conditional routing
    ┌────┴────┐
    ▼         ▼
  END      extract      ← Sonnet: structured fields
              │
              ▼
            score       ← Haiku: rank 0–100 vs profile
              │
              ▼
         summarize      ← Haiku + markdown digest
              │
              ▼
             END
```

## How it works

**1. Fetch (parallel).** Two fetchers run concurrently: one pulls top-level comments from the latest monthly HN "Who is hiring?" thread via the official Hacker News API, the other pulls current YC-funded company postings from `news.ycombinator.com/jobs`. LangGraph merges their outputs using an `Annotated[list, add]` reducer.

**2. Dedupe.** A lightweight fingerprint removes duplicates before any LLM costs are paid (companies sometimes post in both sources).

**3. Classify.** Each posting gets a binary "real job opening vs noise" call. Noise includes job-seeker self-promotion, reply threads, recruiter spam dumps, and malformed posts. Returns structured Pydantic output.

**4. Conditional routing.** If the classifier kept zero postings, the graph short-circuits to END before any expensive Sonnet calls are made.

**5. Extract.** Sonnet parses the messy posting text into typed fields: company, role, location, stage, tech stack.

**6. Score.** Each posting is scored 0–100 against the candidate profile, with reasoning. The prompt enforces hard constraints (location, seniority, salary, deal-breakers) that cap scores when violated.

**7. Summarize.** The top 10 postings become tight 2–3 sentence blurbs.

**8. Digest.** A pure-Python step assembles the final `digest.md` with all scored postings above a configurable threshold.

## Model selection

| Node | Model | Why |
|------|-------|-----|
| Classify | Haiku 4.5 | Binary call, runs on every posting — cost matters |
| Extract | Sonnet 4.5 | Structured parsing of unstructured prose needs the better model |
| Score | Haiku 4.5 | Constrained reasoning over a known criteria list |
| Summarize | Haiku 4.5 | Short, formulaic prose output |

Sonnet is reserved for the one node where output quality genuinely matters; everything else runs on Haiku.

## Setup

Requires Python 3.10+ (3.12 recommended).

```bash
git clone https://github.com/<your-username>/truffle.git
cd truffle
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Get a key at [console.anthropic.com](https://console.anthropic.com).

## Configure your profile

Edit `truffle/profile.py` and update `DEFAULT_PROFILE` to match what you're looking for: desired roles, startup stages, locations, work arrangement, minimum salary, seniority levels, skills, interests, and deal-breakers.

```python
DEFAULT_PROFILE = CandidateProfile(
    name="Your Name",
    desired_roles=["full-stack engineer", "AI engineer"],
    locations=["NYC", "Brooklyn"],
    work_arrangement=["in-person", "hybrid"],
    min_salary_usd=125_000,
    # ...
)
```

The scorer reads this and ranks every posting against it.

## Run

```bash
python run.py
```

Writes `digest.md` to the project root. Open it in any markdown viewer (VS Code: Cmd+Shift+V for live preview).

## Project structure

```
truffle/
├── run.py                # entry point
├── digest.md             # output
├── requirements.txt
├── .env                  # API keys (gitignored)
└── truffle/
    ├── state.py          # shared LangGraph state
    ├── profile.py        # candidate profile schema
    ├── graph.py          # graph wiring
    ├── fetchers/
    │   ├── hn.py
    │   └── wellfound.py  # (YC jobs — filename is legacy)
    └── nodes/
        ├── dedupe.py
        ├── classify.py
        ├── extract.py
        ├── score.py
        └── summarize.py
```

## Rate limiting

The extract and score nodes run in chunks with inter-chunk pauses to stay within Anthropic's free-tier TPM limits (30k for Sonnet, 50k for Haiku). Chunk sizes and pauses are tunable in `truffle/nodes/extract.py` and `truffle/nodes/score.py`. On a paid tier, these can be cranked up and the full pipeline runs in ~90 seconds instead of ~7 minutes.

## Roadmap

- Email delivery via a transactional email service
- GitHub Actions cron job that commits new digests daily
- Additional sources (Reddit r/forhire, Show HN, Pallet)
- Embedding-based dedupe to catch paraphrased reposts
- Persistent state so previously-seen postings can be filtered out

## License

MIT