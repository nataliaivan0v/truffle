from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    name: str
    current_role: str = Field(description="e.g. 'CS student at Northeastern'")
    years_experience: float
    desired_roles: list[str]
    desired_stages: list[str] = ["seed", "series-a", "series-b"]
    locations: list[str] = ["remote", "SF", "NYC"]
    work_arrangement: list[str] = Field(
        default_factory=lambda: ["in-person", "hybrid"],
        description="Acceptable arrangements: 'in-person', 'hybrid', 'remote'",
    )
    min_salary_usd: int = Field(
        default=0,
        description="Minimum acceptable base salary in USD. 0 = no preference."
    )
    seniority: list[str] = Field(
        default_factory=lambda: ["entry", "junior", "new-grad", "founding"],
        description="Acceptable seniority levels — used to filter out senior/staff/principal roles"
    )
    skills: list[str]
    interests: list[str] = []
    deal_breakers: list[str] = []

DEFAULT_PROFILE = CandidateProfile(
    name="Natalia Ivanov",
    current_role="CS graduate from Northeastern",
    years_experience=1.0,
    desired_roles=[
        "full-stack engineer",
        "AI engineer",
        "agentic engineer",
        "software engineer",
    ],
    desired_stages=["seed", "series-a", "series-b"],
    locations=["NYC", "New York", "Manhattan", "Brooklyn"],
    work_arrangement=["in-person", "hybrid"],
    min_salary_usd=125_000,
    seniority=["entry", "junior", "new-grad", "associate"],
    skills=[
        "Python",
        "JavaScript", "TypeScript",
        "React", "Next.js",
        "Node.js",
        "LangGraph", "Anthropic API", "LLM agents",
        "PostgreSQL",
        "Git",
    ],
    interests=[
        "AI tooling",
        "agentic systems",
        "developer tools",
        "consumer AI",
        "early-stage startups",
    ],
    deal_breakers=[
        "fully remote only",
        "outside NYC metro",
        "senior-only role",
        "staff/principal level",
        "below $125k base salary",
        "crypto",
        "defense",
    ],
)