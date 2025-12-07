from dataclasses import dataclass
from typing import List
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from duckduckgo_search import DDGS 

# PydanticAI chunk format
class DocChunk(BaseModel):
    id: str
    text: str

@dataclass
class RAGDeps:
    vector_db: FAISS


class RAGAnswer(BaseModel):
    answer: str
    used_doc_ids: List[str]



# Create agent
rag_agent = Agent[RAGDeps, RAGAnswer](
    "groq:llama-3.1-8b-instant",
    deps_type=RAGDeps,
    output_type=RAGAnswer,
    instructions="""
    You are a documentation assistant.
    First try `search_docs`. If no relevant context is found, use `web_search`.
    Use ONLY retrieved context to answer; if nothing is found, say "I don't know".
    Return the chunk IDs (doc sources or URLs).
    """,
    model_settings={"tool_choice": "auto"},
)


# Retrieval tool using FAISS similarity search
@rag_agent.tool
def search_docs(ctx: RunContext[RAGDeps], query: str) -> List[DocChunk]:
    results = ctx.deps.vector_db.similarity_search_with_score(query, k=3)

    chunks = []
    for doc, score in results:
        chunks.append(
            DocChunk(
                id=doc.metadata.get("source", "unknown"),
                text=doc.page_content,
            )
        )
    return chunks

# Web search tool using DuckDuckGo
@rag_agent.tool(name="web_search")
def web_search(ctx: RunContext[RAGDeps], query: str) -> List[DocChunk]:
    chunks: List[DocChunk] = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=3):
            url = r.get("href") or r.get("url") or "unknown"
            snippet = r.get("body") or r.get("snippet") or r.get("title") or ""
            chunks.append(DocChunk(id=url, text=snippet))
    return chunks
