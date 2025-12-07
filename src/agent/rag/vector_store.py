# ...existing code...
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

def create_vectorstore(docs):
    # Use an open-source embedding model instead of OpenAI
    embeddings = HuggingFaceEmbeddings(model_name="nomic-ai/nomic-embed-text-v1.5",
                                        model_kwargs={"trust_remote_code": True})
    return FAISS.from_documents(docs, embeddings)
# ...existing code...