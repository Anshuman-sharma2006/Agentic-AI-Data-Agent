# 🤖 Agentic AI Data Agent

> A multi-agent AI system that understands natural-language data requests and routes them to specialized **SQL** or **ETL** agents using **LangGraph**.

The project combines LLM-powered reasoning, PostgreSQL querying, API extraction, Pandas transformations, and safety validation into a single agentic workflow.

---

## ✨ What It Does

Instead of manually writing SQL or ETL scripts, you can describe what you want in natural language.

```text
"Show me the top 5 users with the highest ratings"
```

The system determines that this is a **SQL task**, sends it to the SQL Analyst Agent, generates a safe query, executes it against PostgreSQL, and returns the result.

Or:

```text
"Extract data from an API and save it as CSV"
```

The system identifies it as an **ETL task** and sends it to the ETL Analyst Agent.

---

## 🧠 Architecture

```text
                         ┌───────────────────────┐
                         │      User Query       │
                         │   Natural Language    │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │     Data Agent        │
                         │       Router          │
                         └───────────┬───────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    ▼                                 ▼
          ┌──────────────────┐              ┌──────────────────┐
          │  SQL Analyst     │              │  ETL Analyst     │
          │     Agent        │              │     Agent        │
          └────────┬─────────┘              └────────┬─────────┘
                   │                                 │
          ┌────────┴─────────┐              ┌────────┴─────────┐
          │ Schema Context   │              │ API Extraction   │
          │ SQL Generation   │              │ Pandas Transform │
          │ Safety Check     │              │ Format Handling  │
          │ Query Execution  │              │ Safe Execution   │
          └────────┬─────────┘              └────────┬─────────┘
                   │                                 │
                   └────────────────┬────────────────┘
                                    ▼
                           ┌──────────────────┐
                           │   Final Result   │
                           └──────────────────┘
```

### 🔄 Request Flow

1. **User Input** — receives a natural-language request.
2. **Router** — classifies the request as `sql` or `etl`.
3. **Agent Dispatch** — sends the request to the appropriate specialist.
4. **Processing** — the selected agent performs its workflow.
5. **Validation** — generated SQL/code is checked before execution.
6. **Result** — returns the processed result to the user.

---

## 🚀 Features

### 🧭 Intelligent Routing

- Automatically classifies requests as SQL or ETL.
- Uses structured output for routing decisions.
- Orchestrates the workflow with LangGraph.

### 🗄️ SQL Analyst Agent

- Converts natural language into SQL.
- Gathers PostgreSQL schema context.
- Curates/refines user questions.
- Validates generated SQL before execution.
- Executes validated queries.
- Generates a user-friendly final answer.
- Limits results to 10 rows unless otherwise requested.

### 🔄 ETL Analyst Agent

- Extracts data from APIs.
- Normalizes JSON responses.
- Uses Pandas for transformations.
- Supports CSV, JSON, and Parquet.
- Generates transformation code based on user requirements.
- Executes generated code in a controlled environment.

### 🛡️ Safety

- Blocks destructive SQL operations such as:
  - `INSERT`
  - `UPDATE`
  - `DELETE`
  - `DROP`
  - `ALTER`
- Validates generated SQL before execution.
- Validates inputs and structured outputs.
- Keeps credentials in environment variables instead of source code.

---

## 🧰 Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.12+** | Application runtime |
| **LangGraph** | Multi-agent orchestration |
| **LangChain** | LLM and tool integration |
| **Groq** | LLM provider |
| **PostgreSQL** | Database for SQL operations |
| **Pandas** | Data transformation |
| **Pydantic** | State/data validation |
| **python-dotenv** | Environment configuration |
| **uv** | Dependency and project management |

---

## 📋 Prerequisites

Before running the project, make sure you have:

- Python **3.12+**
- `uv`
- A PostgreSQL database
- A Groq API key

---

## ⚡ Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Data_Agent
```

### 2. Install dependencies with `uv`

This project uses **uv**, not `pip`.

```bash
uv sync
```

`uv sync` creates/updates the project's environment and installs the dependencies defined by the project.

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=your_postgres_database_url_here
```

> ⚠️ Never commit your real `.env` file or API keys to Git.

A typical PostgreSQL connection URL looks like:

```text
postgresql://username:password@host:5432/database_name
```

---

## ▶️ Usage

### Run the main application

```bash
uv run main.py
```

### Run a Python file

For a file in the project root:

```bash
uv run file_name.py
```

For a file inside a folder:

```bash
uv run folder/file_name.py
```

Examples:

```bash
uv run main.py
uv run agents/sql_analyst.py
uv run agents/etl_analyst.py
```

---

## 💬 Example Requests

### SQL Query

```text
Show me the average rating for each vehicle type.
```

### SQL Query

```text
Show me the top 5 users with the highest ratings.
```

### API Extraction

```text
Extract the data from
https://pokeapi.co/api/v2/pokemon
and save it as CSV.
```

### Data Transformation

```text
Transform rides.csv by filtering rides
with rating greater than 4.0 and save the result as JSON.
```

---

## 🤖 Agents

### 1. Data Agent — Router

**File:** `agents/data_agent.py`

The main entry point for the agentic workflow.

Responsibilities:

- Receives the user's natural-language request.
- Determines the request type.
- Routes the request to the SQL or ETL agent.
- Coordinates the LangGraph workflow.
- Returns the final result.

---

### 2. SQL Analyst Agent

**File:** `agents/sql_analyst.py`

Handles database-related requests.

#### Workflow

```text
User Question
      ↓
Query Curation
      ↓
Schema Context
      ↓
Prompt Construction
      ↓
SQL Generation
      ↓
Safety Validation
      ↓
Query Execution
      ↓
Answer Generation
```

The SQL agent is designed for read-oriented database analysis and validates generated queries before execution.

---

### 3. ETL Analyst Agent

**File:** `agents/etl_analyst.py`

Handles extraction and transformation workflows.

#### Workflow

```text
User Request
      ↓
Intent Understanding
      ↓
Tool Selection
      ↓
Code Generation
      ↓
Safe Execution
      ↓
Result Reporting
```

Supported ETL operations include:

- API → structured data
- Data transformation with Pandas
- Saving processed data
- CSV
- JSON
- Parquet

---

## 📁 Project Structure

```text
Data_Agent/
│
├── agents/
│   ├── __init__.py
│   ├── data_agent.py
│   ├── sql_analyst.py
│   └── etl_analyst.py
│
├── Models/
│   ├── __init__.py
│   └── schema.py
│
├── utils/
│   ├── __init__.py
│   ├── database.py
│   ├── etl_tools.py
│   └── llm_pick.py
│
├── data/
│   ├── extract/
│   ├── transform/
│   ├── payments.csv
│   ├── ratings.csv
│   ├── rides.csv
│   ├── users.csv
│   └── vehicles.csv
│
├── main.py
├── feed_db.py
├── test_db.py
├── pyproject.toml
├── uv.lock
├── .env
├── .gitignore
└── README.md
```

---

## 🧩 State Models

The agents use structured state models to keep the workflow predictable.

### `AgentSchema`

Used by the SQL Analyst Agent.

```python
class AgentSchema(BaseModel):
    messages: List
    user_question: str
    curated_ques: str
    prompt_query_context: str
    generated_sql_query: str
    is_safe: Literal["Yes", "No"]
    comments: str
    sql_query_execution_result: str
    final_answer: str
```

### `ETLAgentSchema`

Used by the ETL Analyst Agent.

```python
class ETLAgentSchema(BaseModel):
    messages: List
```

### `RouterSchema`

Used to classify the user's request.

```python
class RouterSchema(BaseModel):
    answer: Literal["sql", "etl"]
    comments: str
```

### `DataAgentSchema`

Stores the state of the main routing agent.

```python
class DataAgentSchema(BaseModel):
    messages: List
    route_response: str
```

---

## 🔐 Environment Variables

| Variable | Required | Description |
|---|---:|---|
| `GROQ_API_KEY` | ✅ | API key used for Groq LLM access |
| `DATABASE_URL` | ✅ | PostgreSQL connection URL |

Example:

```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=your_postgres_database_url_here
```

Keep `.env` private and add it to `.gitignore`.

---

## 🗃️ Database

The SQL Agent uses PostgreSQL for database analysis.

Make sure your `DATABASE_URL` points to a reachable PostgreSQL instance before running SQL requests.

Example format:

```text
postgresql://username:password@localhost:5432/data_agent_db
```

If the project includes the database initialization script, run it with:

```bash
uv run feed_db.py
```

---

## 🧪 Development

### Add a dependency

```bash
uv add package_name
```

### Add a development dependency

```bash
uv add --dev package_name
```

### Remove a dependency

```bash
uv remove package_name
```

### Update the lock file

```bash
uv lock
```

### Sync the environment

```bash
uv sync
```

### Run Python through the project environment

```bash
uv run python
```

### Run a script

```bash
uv run main.py
```

---

## ➕ Adding a New Agent

To add another specialized agent:

1. Create the agent inside `agents/`.
2. Define its state schema in `Models/schema.py`.
3. Implement its LangGraph nodes.
4. Add the new route to `agents/data_agent.py`.
5. Add tools required by the agent.
6. Update the README.

The goal is to keep each agent focused on one type of task.

---

## 🔧 Extending ETL Tools

ETL tools can be added in:

```text
utils/etl_tools.py
```

Example:

```python
@tool
def new_tool(param: str) -> str:
    """Tool description."""
    # Implementation
    pass
```

After adding a tool, bind it to the appropriate ETL workflow and update the documentation.

---

## 🛡️ Security Notes

### API Keys

Store credentials only in `.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=your_postgres_database_url_here
```

Never hard-code secrets into Python files.

### SQL Safety

Generated SQL should be validated before execution. Destructive database operations are blocked by the SQL safety layer.

### Generated Code

ETL transformations use generated Python/Pandas code. Treat generated code execution as a security-sensitive operation and keep execution appropriately restricted.

---

## 🚨 Troubleshooting

### `GROQ_API_KEY` not found

Check that:

```text
.env
```

exists in the project root and contains:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### Database connection failed

Verify:

- PostgreSQL is running.
- `DATABASE_URL` is correct.
- The database is reachable.
- Username/password are valid.

### Module not found

Make sure dependencies are synchronized:

```bash
uv sync
```

Then run the script through uv:

```bash
uv run main.py
```

### SQL query rejected

If the generated query is considered unsafe, rewrite the request as a read-only analytical query.

---

## 📊 Example Workflow

Given:

```text
Show me the average rating for each vehicle type.
```

The system performs:

```text
Natural Language Request
          ↓
     Data Agent
          ↓
   Query Classification
          ↓
     SQL Agent
          ↓
   Fetch DB Schema
          ↓
    Generate SQL
          ↓
   Safety Validation
          ↓
    Execute Query
          ↓
    Final Answer
```

For an ETL request:

```text
API / File Input
      ↓
  Data Agent
      ↓
  ETL Agent
      ↓
 Extract / Transform
      ↓
 Safe Execution
      ↓
 Save Output
```

---

## 🎯 Why This Project?

This project demonstrates practical **agentic AI engineering** concepts:

- Multi-agent systems
- LangGraph stateful workflows
- LLM-based routing
- Tool calling
- Natural-language SQL
- SQL safety validation
- API-based data extraction
- Pandas-based ETL
- Structured outputs
- Environment-based configuration

It is designed as a practical example of how an LLM can coordinate specialized tools and agents instead of trying to perform every task inside a single prompt.

---

## 🤝 Contributing

Contributions are welcome.

When contributing:

1. Keep agents modular.
2. Follow the existing project structure.
3. Add/update state schemas when required.
4. Consider security implications of new tools.
5. Update documentation for new functionality.
6. Keep `uv.lock` synchronized with dependency changes.

---

## 📄 License

This project is an AI engineering demonstration project.

---

## 📚 Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/)
- [Groq Documentation](https://console.groq.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## 👨‍💻 Author

**Anshuman Sharma**

Built as a practical exploration of multi-agent AI systems, data engineering, and LangGraph.

---

<p align="center">
  Built with 🧠 LangGraph · ⚡ Groq · 🐘 PostgreSQL · 🐼 Pandas · 🐍 Python · 📦 uv
</p>
