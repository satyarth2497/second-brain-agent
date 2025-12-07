from typing import TypedDict
from .rag_agent import rag_agent, RAGDeps

class RAGOutput(TypedDict):
    answer: str
    used_doc_ids: list[str]

def rag_task(question: str, deps: RAGDeps) -> RAGOutput:
    result = rag_agent.run_sync(question, deps=deps)
    out = result.output
    return {"answer": out.answer, "used_doc_ids": out.used_doc_ids}
