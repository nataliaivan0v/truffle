from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from truffle.graph import build_graph
from truffle.profile import DEFAULT_PROFILE


def main():
    graph = build_graph()

    initial_state = {
        "profile": DEFAULT_PROFILE.model_dump(),
        "raw_postings": [],
    }

    print("🍄 Truffle starting...\n")
    final_state = graph.invoke(initial_state)

    digest = final_state.get("digest", "")
    if digest:
        out = Path("digest.md")
        out.write_text(digest)
        print(f"\n✓ Wrote {out} ({len(digest)} chars)")
        print("\n" + "=" * 60, "\nPREVIEW\n", "=" * 60)
        print(digest[:1500])
    else:
        print("\nNo digest produced (no qualifying postings).")


if __name__ == "__main__":
    main()