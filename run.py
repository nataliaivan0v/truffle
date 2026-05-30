from dotenv import load_dotenv
load_dotenv()

import os
print(f"[debug] PARENT_ID={os.getenv('PROVIRAS_PARENT_ID')!r}")
print(f"[debug] PLATFORM={os.getenv('PROVIRAS_PLATFORM')!r}")

import logging
import http.client

http.client.HTTPConnection.debuglevel = 1
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logging.getLogger("urllib3").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("requests").setLevel(logging.DEBUG)
logging.getLogger("proviras_sdk").setLevel(logging.DEBUG)

from pathlib import Path
from proviras_sdk import ProvirasSdk
from truffle.graph import build_graph
from truffle.profile import DEFAULT_PROFILE


def main():
    sdk = ProvirasSdk()
    tracer = sdk.trace("Truffle daily job digest")

    graph = build_graph()

    initial_state = {
        "profile": DEFAULT_PROFILE.model_dump(),
        "raw_postings": [],
    }

    print("🍄 Truffle starting...\n")
    final_state = graph.invoke(
        initial_state,
        config={"callbacks": [tracer]},
    )

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