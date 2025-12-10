import os, sys
sys.path.append(os.path.dirname(__file__))  # add ./src
from dotenv import load_dotenv
load_dotenv()
from agent.rag.rag_loader import load_and_split_markdown
from agent.rag.vector_store import create_vectorstore
from agent.rag.rag_agent import RAGDeps
from agent.rag.task import rag_task
from agent.orchestrator.orchestrator import orchestrator_agent, OrchestratorDeps

def main():
    # Load markdown file
    docs = load_and_split_markdown("data/docs.md")

    # Build FAISS vector DB
    vector_db = create_vectorstore(docs)

    deps = OrchestratorDeps(
        vector_db=vector_db,
        profile_file="data/user_profile.json",
    )

    # Chat loop
    print("RAG + Health chat ready. Type 'exit' or press Ctrl+C to quit.")
    try:
        while True:
            question = input("You: ").strip()
            if not question or question.lower() in {"exit", "quit", "q"}:
                print("Bye.")
                break
            
            # Retry logic for intermittent Groq API issues
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    run_result = orchestrator_agent.run_sync(question, deps=deps)
                    # The result is the OrchestratorAnswer object itself
                    result = run_result.output if hasattr(run_result, 'output') else run_result
                    print(f"[{result.source}] {result.answer}\n")
                    break  # Success, exit retry loop
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Retrying... (attempt {attempt + 2}/{max_retries})")
                    else:
                        print(f"Error: {e}")
                        print("Please try rephrasing your question.\n")
    except KeyboardInterrupt:
        print("\nBye.")

if __name__ == "__main__": 
    main()
