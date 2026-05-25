# 🤖 Agentic SQL Advanced: Semantic RAG & Review Engine (LlamaIndex & PGVector)

An advanced reasoning agent utilizing LlamaIndex to bridge the gap between structured relational data (PostgreSQL) and unstructured semantic text (Customer Reviews). This repository demonstrates how to implement a ReAct Agent that autonomously chains disparate tools to satisfy complex analytical queries and perform vector-based sentiment searches.

## 🏗️ The "Why": Architectural Design Choices

When dealing with a combination of structural queries ("How many orders") and unstructured semantic queries ("Find reviews complaining about battery life"), static pipelines become too rigid. I explicitly chose the **LlamaIndex ReActAgent framework** for this advanced engine because of its **autonomous reasoning and seamless tool abstraction**.

Instead of explicitly coding the routing logic (as done in LangGraph), the ReAct (Reasoning + Acting) Agent operates in an autonomous loop:
- **Observation**: It analyzes the user request against the descriptions of its available tools.
- **Action**: It decides to invoke `SQLTool` to fetch numeric data, and `VectorSearchTool` to fetch semantic context from ChromaDB.
- **Synthesis**: It holds the output of the tools in memory and formulates a final analytical response, allowing for highly complex, multi-turn conversational workflows without rigid coding.

### Comparative Approach: LlamaIndex vs. LangGraph
*(See my complementary repository: **[Agentic SQL Core: Structural Query Engine](https://github.com/2001anshkaushik/Agentic_SQL_Core_LangGraph)**)*

While my LangGraph implementation provides absolute deterministic control—vital for strict structural operations—it requires heavy boilerplate to define every possible routing edge. **LlamaIndex**, by contrast, provides incredible development velocity and flexibility. 

By abstracting the tools (Code Interpreter, Vector Store, SQL Database), the ReAct Agent can autonomously decide *how* to solve a problem. It effortlessly combines relational Postgres lookups with ChromaDB semantic search without me having to hard-code the cross-reference logic, making it vastly superior for hybrid RAG and Text-to-SQL environments.

---

## 🔍 Technical Deep-Dive: CodeInterpreter & Semantic Search

The core strength of this system lies in the unified interface over heterogenous data formats.

### The ReAct CodeInterpreter Workflow
When a query requires visualization:
1. **Tool 1 (`SQLTool`)**: Generates Postgres-compliant SQL and executes it, dumping the returned rows into the session memory as a Pandas DataFrame.
2. **Tool 2 (`VisualizerTool`)**: Recognizing that data needs to be plotted, the agent writes Python Plotly code. Using a sanitized Python `CodeInterpreter` environment, it injects the previously saved DataFrame, evaluates the Plotly objects, and serializes the resulting figure to JSON.
3. **Streamlit UI**: Intercepts the generated JSON payloads and renders the interactive graphs alongside the LLM's natural language summary.

### Hybrid RAG (PGVector / ChromaDB)
Standard SQL `LIKE '%battery%'` queries fail to capture sentiment or synonyms (like "no power" or "won't charge"). I implemented a parallel **ChromaDB Vector Store** that embeds all `ReviewText` columns using `text-embedding-3-small`. When an intent is semantic, the agent bypasses Postgres and queries the multidimensional vector space, providing near-human semantic retrieval.

---

## 🚀 Deployment & Local Execution

**Prerequisites**: Python 3.11+, PostgreSQL instance running locally.

```bash
# 1. Install dependencies
uv venv
uv pip install -r src/requirements.txt

# 2. Configure Environment
cp src/env.example src/.env
# Edit .env to add OPENAI_API_KEY and POSTGRES_PASSWORD

# 3. Setup Postgres DB and ChromaDB Vector Store
python src/db_setup.py

# 4. Launch the Agentic UI
streamlit run src/app.py
```

## 📂 Project Structure

```
Agentic_SQL_Advanced_LlamaIndex/
├── doc/
│   └── README.md (this file)
├── src/
│   ├── .env (environment variables - not in git)
│   ├── requirements.txt (Python dependencies)
│   ├── app.py (Streamlit UI)
│   ├── db_setup.py (database and vector store setup)
│   ├── data/
│   │   ├── RobotVacuumDepot_MasterData_v125.csv (source data)
│   │   └── chroma_db/ (ChromaDB vector store)
│   ├── agent/
│   │   └── agent_factory.py, prompts.py
│   ├── config/
│   │   └── database.py, llm.py
│   ├── tools/
│   │   └── sql_tool.py, vector_search_tool.py, visualizer_tool.py, shared_state.py
│   ├── ui/
│   │   └── components.py, styles.py
│   └── utils/
│       └── parsing.py
```

## 🔄 Application Flow

### Runtime Query Processing Flow

1. **User Query**: Processed via Streamlit UI.
2. **ReAct Agent**: Analyzes the query to define reasoning intent.
3. **Tool Dispatcher**: 
   - Uses `SQLTool` to construct and execute PG-compliant SQL logic.
   - Uses `VectorSearchTool` to locate semantically similar text points in Chroma.
   - Uses `VisualizerTool` to convert LLM python strings to Plotly visuals.
4. **Synthesis**: Agent renders a multimodal markdown, chart, and dataframe interface.

### Database Setup Flow (One-Time Setup)

```
┌─────────────────────────────┐
│  RobotVacuumDepot_          │
│  MasterData_v125.csv        │
│  (Raw CSV Data)             │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  db_setup.py                │
│  • Polars CSV reading       │
│  • Data type preparation    │
│  • PostgreSQL connection    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  PostgreSQL Database        │
│  • Create/recreate table    │
│  • Bulk insert data         │
│  • robot_vacuum_orders      │
│    (flat table structure)   │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  ChromaDB Vector Store      │
│  • Extract ReviewText       │
│  • Generate embeddings      │
│    (text-embedding-3-small) │
│  • Persist to chroma_db/    │
└─────────────────────────────┘
```

### Runtime Query Processing Flow

```
┌─────────────────────────────┐
│  User Query                 │
│  (Natural Language)         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Streamlit UI (app.py)      │
│  • Initializes ReAct Agent  │
│  • Manages chat history     │
│  • Renders UI components    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  ReAct Agent                │
│  (agent_factory.py)         │
│  • Reasons about query      │
│  • Chooses tools to use     │
│  • Chains tool calls        │
│  • Generates responses      │
└──────────────┬──────────────┘
               │
       ┌───────┴───────┐
       │               │
       ▼               ▼
┌──────────┐   ┌─────────────────────┐
│  SQL     │   │  Vector Search      │
│  Tool    │   │  Tool               │
│          │   │  (semantic search   │
│  • Exec  │   │   on ReviewText)    │
│    SQL   │   │                     │
│  • Return│   │  • Find similar     │
│    JSON  │   │    reviews          │
└────┬─────┘   │  • Return metadata  │
     │         └──────────┬──────────┘
     │                    │
     └──────────┬─────────┘
                │
                ▼
     ┌─────────────────────┐
     │  Visualizer Tool    │
     │  (optional)         │
     │  • Receives data    │
     │  • Executes Python  │
     │  • Generates Plotly │
     │    charts           │
     └──────────┬──────────┘
                │
                ▼
     ┌─────────────────────┐
     │  Results            │
     │  • Tables/DataFrames│
     │  • Plotly charts    │
     │  • SQL metadata     │
     │  • Review results   │
     └──────────┬──────────┘
                │
                ▼
     ┌─────────────────────┐
     │  Streamlit UI       │
     │  • Renders visuals  │
     │  • Shows tables     │
     │  • "View Logic"     │
     │    expander         │
     └─────────────────────┘
```

## 🧠 Logic and Features

I implemented a ReAct (Reasoning + Acting) agent using LlamaIndex:

- **ReAct Agent** (`agent/agent_factory.py`):
  - Maintains conversation context via ChatMemoryBuffer.
  - Supports up to 20 iterations for complex multi-step reasoning.
  - Receives comprehensive system prompt with database schema.

### Key Tools
1. **SQL Tool**: Executes SQL queries generated by the LLM against PostgreSQL, storing results in shared state for visualization.
2. **Vector Search Tool**: Performs semantic search on ReviewText using ChromaDB finding reviews based on meaning.
3. **Visualizer Tool**: Executes Python code generated by the LLM to create iterative Plotly charts dynamically.

### Key Design Principles

1. **No Hard-Coding**: All SQL and Python code is generated dynamically by the LLM. 
2. **Semantic Search**: Standard SQL `LIKE '%battery%'` queries fail to capture sentiment or synonyms (like "no power" or "won't charge"). I implemented a parallel **ChromaDB Vector Store** that embeds all `ReviewText` columns using `text-embedding-3-small`. When an intent is semantic, the agent bypasses Postgres and queries the multidimensional vector space, providing near-human semantic retrieval.
3. **Tool Chaining**: The agent intelligently chains tools together (SQL → Visualizer) to answer complex queries that require both data retrieval and visualization.

### UI Features
**"View Logic" Expander**: I implemented a traceability feature exposing the underlying code and data used to generate results for every message so developers can debug the semantic routing in real-time.

## ✅ Types of Supported Queries

The system allows users to input queries written in natural language and produces output in textual/tabular format or visual/graphical/chart format. Here are the types of queries I support:

### Simple Queries (Direct SQL)

These queries are answered with direct SQL execution:

- **Count queries**: "How many orders are there?"
- **Aggregation**: "What is the average shipping cost?"
- **Direct lookups**: "List all manufacturers"
- **Filtered counts**: "How many orders have a status of 'Delivered'?"

### Analytical Queries (Full Pipeline with Charts)

These queries trigger the tool chaining pipeline and generate visualizations:

- **Time Series**: "Show me monthly revenue trends" → Line chart
- **Distributions**: "What is the distribution of delivery statuses?" → Pie chart
- **Comparisons**: "Compare average shipping costs by carrier" → Bar chart
- **Ratings**: "Show me average review ratings by manufacturer" → Bar chart

### Data Exploration Queries (Tables)

These queries return detailed tabular data:

- **Filtered Lists**: "Which warehouses have products below restock threshold?"
- **Rankings**: "Show me the top 5 zip codes with highest delayed deliveries"
- **Detailed Analysis**: "List 5 orders where the delivery status is 'Delayed' and show the Expected vs Actual delivery dates"

### Semantic Search Queries (Vector Search)

These queries use the vector search tool to find semantically similar reviews:

- **Complaint Analysis**: "Which product has the most frequent complaints?"
- **Sentiment Search**: "Find reviews complaining about battery life"
- **Topic Discovery**: "What are customers saying about shipping delays?"
- **Review Mining**: "Show me reviews that mention quality issues"

The vector search tool finds reviews based on meaning, so queries like "find complaints about battery" will match reviews mentioning "power issues", "short battery life", "needs frequent charging", etc.

## Verification

To verify the system works correctly the "View Logic" expander allows you to inspect the generated SQL, Python code, and data for full traceability of how natural language queries are translated into database operations and visualizations.

**Author**: Ansh Kaushik
