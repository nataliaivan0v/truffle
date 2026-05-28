from langgraph.graph import StateGraph, START, END

from truffle.state import TruffleState
from truffle.fetchers.hn import hn_node
from truffle.fetchers.yc import yc_node
from truffle.nodes.dedupe import dedupe_node
from truffle.nodes.classify import classify_node
from truffle.nodes.extract import extract_node
from truffle.nodes.score import score_node
from truffle.nodes.summarize import summarize_node


def route_after_classify(state: TruffleState) -> str:
    if not state.get("classified"):
        print("[route] no real jobs after classify — ending early")
        return "end"
    return "extract"

def build_graph():
    g = StateGraph(TruffleState)

    g.add_node("hn_fetch", hn_node)
    g.add_node("yc_fetch", yc_node)
    g.add_node("dedupe", dedupe_node)
    g.add_node("classify", classify_node)
    g.add_node("extract", extract_node)
    g.add_node("score", score_node)
    g.add_node("summarize", summarize_node)

    g.add_edge(START, "hn_fetch")
    g.add_edge(START, "yc_fetch")

    g.add_edge("hn_fetch", "dedupe")
    g.add_edge("yc_fetch", "dedupe")

    g.add_edge("dedupe", "classify")

    g.add_conditional_edges(
        "classify",
        route_after_classify,
        {"extract": "extract", "end": END},
    )

    g.add_edge("extract", "score")
    g.add_edge("score", "summarize")
    g.add_edge("summarize", END)

    return g.compile()