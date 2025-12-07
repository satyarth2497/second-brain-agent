import os, sys
sys.path.append(os.path.dirname(__file__))  # add ./src
from dotenv import load_dotenv
load_dotenv()
from agent.rag.rag_loader import load_and_split_markdown
from agent.rag.vector_store import create_vectorstore
from agent.rag.rag_agent import RAGDeps
from agent.rag.task import rag_task

def main():
    # Load markdown file
    docs = load_and_split_markdown("data/docs.md")

    # Build FAISS vector DB
    vector_db = create_vectorstore(docs)

    deps = RAGDeps(vector_db=vector_db)
    # Chat loop
    print("RAG chat ready. Type 'exit' or press Ctrl+C to quit.")
    try:
        while True:
            question = input("You: ").strip()
            if not question or question.lower() in {"exit", "quit", "q"}:
                print("Bye.")
                break
            result = rag_task(question, deps)
            print(f"Assistant: {result['answer']}\n")
    except KeyboardInterrupt:
        print("\nBye.")

if __name__ == "__main__":
    main()
