# Second Brain Agent - System Architecture

## High-Level Architecture Diagram

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                          USER INTERFACE LAYER                          ┃
┃                                                                         ┃
┃  ┌─────────────────────────────────────────────────────────────────┐  ┃
┃  │  main.py - Interactive CLI                                      │  ┃
┃  │  • Chat loop with exit handling                                 │  ┃
┃  │  • Retry logic (3 attempts)                                     │  ┃
┃  │  • Error handling & user feedback                               │  ┃
┃  │  • Result formatting [source] answer                            │  ┃
┃  └─────────────────────────────────────────────────────────────────┘  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                                   ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃               ORCHESTRATOR AGENT (Agent-to-Agent Hub)                  ┃
┃            Model: groq:llama-3.3-70b-versatile                         ┃
┃                                                                         ┃
┃  ┌─────────────────────────────────────────────────────────────────┐  ┃
┃  │  Intelligent Routing Logic                                      │  ┃
┃  │                                                                  │  ┃
┃  │  IF query about food/diet/nutrition/meal/recipe:                │  ┃
┃  │      → call ask_health(question)                                │  ┃
┃  │  ELSE:                                                           │  ┃
┃  │      → call ask_rag(question)                                   │  ┃
┃  │                                                                  │  ┃
┃  │  Output: {answer: str, source: "rag"|"health"}                  │  ┃
┃  └─────────────────────────────────────────────────────────────────┘  ┃
┗━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┛
                      ▼                        ▼
        ┏━━━━━━━━━━━━━━━━━━━━━━┓  ┏━━━━━━━━━━━━━━━━━━━━━━┓
        ┃   RAG AGENT          ┃  ┃   HEALTH AGENT       ┃
        ┃   (Documentation)    ┃  ┃   (Nutrition)        ┃
        ┃   llama-3.1-8b       ┃  ┃   llama-3.1-8b       ┃
        ┗━━━━━━━━━━━━━━━━━━━━━━┛  ┗━━━━━━━━━━━━━━━━━━━━━━┛
                ┃                            ┃
                ┃                            ┃
       ┌────────┴────────┐                   ┃
       ▼                 ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌────────────────┐
│ LOCAL DOCS   │  │ WEB SEARCH   │  │ USER PROFILE   │
│ Vector Store │  │ (DuckDuckGo) │  │ (JSON)         │
└──────────────┘  └──────────────┘  └────────────────┘
```

---

## Detailed Component Architecture

### 1. User Interface Layer

```
┌─────────────────────────────────────────────────────────────────┐
│  main.py                                                        │
│                                                                 │
│  def main():                                                    │
│      # Initialize system                                       │
│      docs = load_and_split_markdown("data/docs.md")           │
│      vector_db = create_vectorstore(docs)                     │
│      deps = OrchestratorDeps(vector_db, profile_file)         │
│                                                                 │
│      # Chat loop                                               │
│      while True:                                               │
│          question = input("You: ")                            │
│          if exit_condition:                                    │
│              break                                             │
│                                                                 │
│          # Retry logic                                         │
│          for attempt in range(3):                             │
│              try:                                              │
│                  result = orchestrator_agent.run_sync(...)    │
│                  print(f"[{result.source}] {result.answer}")  │
│                  break                                         │
│              except: retry                                     │
└─────────────────────────────────────────────────────────────────┘
```

**Responsibilities:**
- User interaction and input/output
- System initialization
- Error handling and retries
- Result formatting

---

### 2. Orchestrator Agent (A2A Router)

```
┌─────────────────────────────────────────────────────────────────┐
│  orchestrator.py                                                │
│                                                                 │
│  orchestrator_agent = Agent[OrchestratorDeps, OrchestratorAnswer](
│      "groq:llama-3.3-70b-versatile",                          │
│      output_type=OrchestratorAnswer,                           │
│      instructions="Route food/diet → health, else → rag"      │
│  )                                                              │
│                                                                 │
│  @orchestrator_agent.tool(name="ask_rag")                     │
│  def ask_rag(ctx, question: str) -> str:                      │
│      res = rag_agent.run_sync(question, RAGDeps(...))         │
│      return res.answer                                         │
│                                                                 │
│  @orchestrator_agent.tool(name="ask_health")                  │
│  def ask_health(ctx, question: str) -> str:                   │
│      res = health_agent.run_sync(question, HealthDeps(...))   │
│      return res.answer                                         │
│                                                                 │
│  Output: OrchestratorAnswer(answer, source)                    │
└─────────────────────────────────────────────────────────────────┘
```

**Decision Flow:**
1. Receive user question
2. Analyze intent (food/diet vs technical)
3. Call appropriate child agent via tool
4. Aggregate response
5. Return unified answer with source attribution

**Key Features:**
- Intelligent intent classification
- Tool-based A2A communication
- Structured output with Pydantic models
- Temperature: 0.1 for consistent routing

---

### 3. RAG Agent (Documentation Expert)

```
┌─────────────────────────────────────────────────────────────────┐
│  rag_agent.py                                                   │
│                                                                 │
│  rag_agent = Agent[RAGDeps, RAGAnswer](                        │
│      "groq:llama-3.1-8b-instant",                             │
│      output_type=RAGAnswer,                                    │
│      instructions="Use search_docs, fallback to web_search"   │
│  )                                                              │
│                                                                 │
│  @rag_agent.tool(name="search_docs")                          │
│  def search_docs(ctx, query: str) -> List[DocChunk]:          │
│      # FAISS similarity search                                 │
│      results = ctx.deps.vector_db.similarity_search(query, k=3)
│      return [DocChunk(id=..., text=...) for doc in results]   │
│                                                                 │
│  @rag_agent.tool(name="web_search")                           │
│  def web_search(ctx, query: str) -> List[DocChunk]:           │
│      # DuckDuckGo fallback                                     │
│      with DDGS() as ddgs:                                      │
│          results = ddgs.text(query, max_results=3)            │
│      return [DocChunk(id=url, text=snippet) ...]              │
│                                                                 │
│  Output: RAGAnswer(answer, used_doc_ids)                       │
└─────────────────────────────────────────────────────────────────┘
```

**Tool Pipeline:**
1. **search_docs**: Query local vector store (FAISS)
   - Embedding: nomic-ai/nomic-embed-text-v1.5
   - Returns top 3 most relevant chunks
2. **web_search**: Fallback for missing docs
   - Uses DuckDuckGo search API
   - Returns top 3 web results

**Data Flow:**
```
User Query
    ↓
Orchestrator routes to RAG
    ↓
RAG agent invokes search_docs
    ↓
FAISS vector similarity search
    ↓
Chunks found? → Yes → Generate answer from docs
              ↓ No
         web_search fallback
              ↓
         Generate answer from web results
```

---

### 4. Health Agent (Nutrition Advisor)

```
┌─────────────────────────────────────────────────────────────────┐
│  health.py                                                      │
│                                                                 │
│  health_agent = Agent[HealthDeps, HealthAnswer](               │
│      "groq:llama-3.1-8b-instant",                             │
│      output_type=HealthAnswer,                                 │
│      instructions="Suggest meals, avoid allergens"            │
│  )                                                              │
│                                                                 │
│  @health_agent.tool(name="get_profile")                       │
│  def get_profile(ctx) -> UserProfile:                          │
│      # Load user profile from JSON                             │
│      return UserProfile(diet, allergies, calories, ...)       │
│                                                                 │
│  @health_agent.tool(name="update_profile")                    │
│  def update_profile(ctx, diet=None, allergies=None, ...) ->   │
│      UserProfile:                                              │
│      # Update and persist profile                              │
│      profile = _load_profile(ctx.deps.profile_file)           │
│      if diet: profile.diet = diet                             │
│      _save_profile(ctx.deps.profile_file, profile)            │
│      return profile                                            │
│                                                                 │
│  Output: HealthAnswer(answer)                                  │
└─────────────────────────────────────────────────────────────────┘
```

**User Profile Schema:**
```json
{
  "diet": "balanced",
  "allergies": [],
  "dislikes": [],
  "calories_target": 1500,
  "weight": 70,
  "height": 175
}
```

**Tool Pipeline:**
1. **get_profile**: Read user preferences from JSON
2. **update_profile**: Modify and persist profile changes

**Safety-Critical Feature:**
- **Allergen Avoidance**: MUST check profile and exclude allergens
- Example: User has gluten allergy → Only suggest gluten-free options

---

## Data Processing Pipeline

### Document Loading & Chunking

```
┌─────────────────────────────────────────────────────────────────┐
│  rag_loader.py                                                  │
│                                                                 │
│  def load_and_split_markdown(file_path: str) -> List[Document]:│
│      # 1. Load markdown file                                    │
│      loader = TextLoader(file_path)                            │
│      docs = loader.load()                                      │
│                                                                 │
│      # 2. Split into chunks                                     │
│      splitter = RecursiveCharacterTextSplitter(               │
│          chunk_size=300,                                       │
│          chunk_overlap=50                                      │
│      )                                                          │
│      chunks = splitter.split_documents(docs)                   │
│      return chunks                                             │
└─────────────────────────────────────────────────────────────────┘
```

**Chunking Strategy:**
- **Chunk size**: 300 characters
- **Overlap**: 50 characters
- **Method**: Recursive character splitting
- **Purpose**: Balance context vs. precision

---

### Vector Store Creation

```
┌─────────────────────────────────────────────────────────────────┐
│  vector_store.py                                                │
│                                                                 │
│  def create_vectorstore(docs) -> FAISS:                        │
│      # 1. Initialize embeddings model                           │
│      embeddings = HuggingFaceEmbeddings(                       │
│          model_name="nomic-ai/nomic-embed-text-v1.5",         │
│          model_kwargs={"trust_remote_code": True}             │
│      )                                                          │
│                                                                 │
│      # 2. Create FAISS index                                    │
│      vector_db = FAISS.from_documents(docs, embeddings)        │
│      return vector_db                                          │
└─────────────────────────────────────────────────────────────────┘
```

**Embedding Model:**
- **Model**: nomic-ai/nomic-embed-text-v1.5
- **Dimension**: 768
- **Provider**: HuggingFace Transformers
- **Trust remote code**: Required for Nomic models

**FAISS Index:**
- **Type**: In-memory vector database
- **Similarity**: Cosine similarity
- **Query**: Returns top-k most similar chunks

---

## Technology Stack

### AI/ML Layer
- **Pydantic AI**: Agent framework
- **Groq**: LLM provider (llama models)
- **HuggingFace**: Embedding models

### Document Processing
- **LangChain**: Document loaders & text splitters
- **FAISS**: Vector similarity search

### External APIs
- **DuckDuckGo Search**: Web fallback

### Data Storage
- **JSON**: User profiles
- **Markdown**: Documentation
- **In-memory**: FAISS vector index

### Configuration
- **python-dotenv**: Environment variables

---

## Agent Communication Pattern (A2A)

### Orchestrator → Child Agent Flow

```
1. USER QUERY
   └→ Orchestrator receives question

2. INTENT ANALYSIS
   └→ LLM analyzes: Is this food/diet related?
      ├→ YES: Route to Health Agent
      └→ NO:  Route to RAG Agent

3. TOOL INVOCATION
   └→ Orchestrator calls ask_health() or ask_rag()
      └→ Child agent receives question as tool parameter

4. CHILD AGENT PROCESSING
   └→ Child agent uses its own tools:
      • RAG: search_docs() → web_search()
      • Health: get_profile() → generate recommendations

5. RESPONSE AGGREGATION
   └→ Child agent returns answer string
      └→ Orchestrator wraps in OrchestratorAnswer
         └→ {answer: str, source: "rag"|"health"}

6. USER OUTPUT
   └→ Format: [source] answer
```

### Key A2A Features

1. **Hierarchical Structure**
   - Parent: Orchestrator (routing)
   - Children: RAG, Health (specialists)

2. **Tool-Based Communication**
   - Orchestrator calls children via `@agent.tool` functions
   - Clean separation of concerns

3. **Type Safety**
   - Pydantic models ensure structured I/O
   - Type hints throughout

4. **Independence**
   - Each agent has its own model, tools, instructions
   - Can be tested/deployed separately

5. **Extensibility**
   - Easy to add new specialist agents
   - Just add new tool to orchestrator

---

## Security & Configuration

### Environment Variables
```bash
# .env file
GROQ_API_KEY=gsk_...

# Optional (for other providers)
OPENAI_API_KEY=sk-...
```

### Data Security
- ✅ API keys in .env (gitignored)
- ✅ User profiles stored locally (no cloud)
- ✅ No sensitive data in vector store
- ⚠️ Future: Encrypt user profiles at rest

### API Rate Limiting
- **Groq Free Tier**: 14,400 requests/day
- **Retry Logic**: 3 attempts with exponential backoff
- **Error Handling**: Graceful degradation

---

## Performance Characteristics

### Latency Breakdown

```
Total Response Time: ~2-5 seconds

┌─────────────────────────────────────┐
│ Component            │ Time         │
├─────────────────────────────────────┤
│ Orchestrator LLM     │ 0.5-1.0s    │
│ Child Agent LLM      │ 1.0-2.0s    │
│ Vector Search        │ 0.1-0.3s    │
│ Web Search (fallback)│ 1.0-2.0s    │
│ Profile I/O          │ <0.1s       │
└─────────────────────────────────────┘
```

### Token Usage (Approximate)

```
Per Query:
- Orchestrator: 100-300 tokens
- Child Agent:  500-1500 tokens
- Total:        600-1800 tokens/query

Daily Limits (Groq Free):
- Requests: 14,400
- Queries: ~10,000-14,000 (with retries)
```

### Memory Footprint

```
- FAISS Index: ~50-100 MB (for typical docs)
- Embedding Model: ~1 GB (HuggingFace)
- Total RAM: ~1.5-2 GB
```

---

## Deployment Considerations

### Production Readiness

✅ **Ready:**
- Single-turn queries
- Intelligent routing
- RAG retrieval
- Health personalization
- Error handling

⏳ **Needs Work:**
- Multi-turn conversation memory
- Concurrent request handling
- Caching layer
- Logging/monitoring
- A/B testing framework

### Scaling Strategy

```
Current: Monolithic (single process)
    ↓
Phase 1: Microservices
- Orchestrator service
- RAG service  
- Health service
    ↓
Phase 2: Load Balancing
- API Gateway
- Multiple agent instances
- Redis cache
    ↓
Phase 3: Distributed
- Kafka for async messaging
- Distributed vector store
- Horizontal scaling
```

---

## Conclusion

The Second Brain Agent implements a robust **multi-agent orchestration system** with:

✅ Intelligent A2A routing  
✅ Specialized RAG and Health agents  
✅ Hybrid information sourcing (local + web)  
✅ Personalized user profiles  
✅ Safety-critical allergen handling  
✅ Graceful error recovery  

**Architecture Strengths:**
- Clean separation of concerns
- Type-safe Pydantic models
- Extensible tool-based design
- Resilient retry logic

**Status**: Production-ready for single-turn use cases with strong routing and personalization.

---

*Last Updated: December 10, 2025*  
*Architecture Version: 1.0*
