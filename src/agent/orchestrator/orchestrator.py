from dataclasses import dataclass
from typing import Literal, List
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from langchain_community.vectorstores import FAISS

# Child agents
from agent.rag.rag_agent import rag_agent, RAGDeps
from agent.health.health import health_agent, HealthDeps

class DocChunk(BaseModel):
    id: str
    text: str

@dataclass
class OrchestratorDeps:
    vector_db: FAISS
    profile_file: str # e.g., "data/user_profile.json"

class OrchestratorAnswer(BaseModel):
    answer: str
    source: Literal["rag","health"] # "rag" or "health"

orchestrator_agent = Agent[OrchestratorDeps, OrchestratorAnswer](
    "groq:llama-3.3-70b-versatile",
    deps_type=OrchestratorDeps,
    output_type=OrchestratorAnswer,
    instructions="""
    You are a question router. Your job is to route questions to the right agent.
    
    Rules:
    - Food/diet/nutrition/meal/recipe questions → use ask_health tool
    - All other questions → use ask_rag tool
    
    Process:
    1. Read the user question
    2. Decide which tool to call based on the topic
    3. Call the appropriate tool with the question parameter
    4. The tool returns an answer string
    5. Return the final result with answer and source fields
    
    Example:
    User: "What should I eat for dinner?"
    Action: ask_health(question="What should I eat for dinner?")
    Result: {"answer": "...", "source": "health"}
    
    User: "Explain the architecture"
    Action: ask_rag(question="Explain the architecture")
    Result: {"answer": "...", "source": "rag"}
    
    Important: source MUST be exactly "rag" or "health" (lowercase).
    """,
    model_settings={"tool_choice": "auto", "temperature": 0.1},
)

@orchestrator_agent.tool(name="ask_rag")
def ask_rag(ctx: RunContext[OrchestratorDeps], question: str) -> str:
    """Query the RAG documentation agent."""
    res = rag_agent.run_sync(question, deps=RAGDeps(vector_db=ctx.deps.vector_db))
    return getattr(res, "answer", str(res))

@orchestrator_agent.tool(name="ask_health")
def ask_health(ctx: RunContext[OrchestratorDeps], question: str) -> str:
    """Query the health/nutrition agent."""
    res = health_agent.run_sync(question, deps=HealthDeps(profile_file=ctx.deps.profile_file))
    return getattr(res, "answer", str(res))