# Initial Repository State Summary

This document captures the initial state of the **Agentic AI Data Agent** project. It provides an inventory of the codebase components, their schemas, workflows, and outstanding integration/security issues.

---

## 📂 Current Directory Structure

The workspace is organized as follows:

```text
Ai Orchastration/
├── Models/
│   ├── __init__.py
│   └── schema.py                 # Pydantic schemas for LangGraph states
├── agents/
│   ├── __init__.py
│   ├── data_agent.py             # Router agent coordinating SQL vs ETL
│   ├── sql_analyst.py            # SQL analyst graph (curate, generate, safety judge, execute)
│   └── etl_analyst.py            # ETL analyst graph with tool calling
├── app/
│   ├── AGENT.md                  # Engineering requirements/rules
│   ├── Architecture.md           # Architecture overview
│   ├── FASTAPI_STRUCTURE.md      # FastAPI design blueprint
│   ├── PHASES.md                 # Development phases roadmap
│   ├── main.py                   # FastAPI application entry (basic endpoints only)
│   └── api/
│       ├── Routes/               # Empty directory for API endpoints
│       └── schemas/              # Empty directory for API request/response models
├── utils/
│   ├── __init__.py
│   ├── database.py               # Psycopg2 helper for schema introspection & SQL execution
│   ├── etl_tools.py              # pandas API request/save & local CSV context parser
│   └── llm_pick.py               # ChatGroq model configurations based on level
├── data/
│   ├── extract/                  # Directory for extracted ETL files
│   └── transform/                # Directory for transformed ETL files
├── pyproject.toml                # Project configurations & dependencies
├── requirements.txt              # pip dependencies
└── uv.lock                       # Lockfile managed by uv
```

---

## 🤖 Graph Architecture & Component Inventory

### 1. Data Agent (Router)
* **File:** [`agents/data_agent.py`](file:///c:/Users/AMAN/OneDrive/Desktop/Ai%20Orchastration/agents/data_agent.py)
* **State Schema:** `DataAgentSchema` ([`Models/schema.py`](file:///c:/Users/AMAN/OneDrive/Desktop/Ai%20Orchastration/Models/schema.py))
* **Flow:**
  ```mermaid
  graph TD
      START([START]) --> RouterNode[router_node]
      RouterNode --> |conditional: sql| SqlNode[sql_node]
      RouterNode --> |conditional: etl| EtlNode[etl_node]
      SqlNode --> END([END])
      EtlNode --> END
  ```
* **Status:** Compiles independently. Under the hood, it invokes the sub-graphs (`sql_analyst` and `etl_analyst`).

---

### 2. SQL Analyst Agent
* **File:** [`agents/sql_analyst.py`](file:///c:/Users/AMAN/OneDrive/Desktop/Ai%20Orchastration/agents/sql_analyst.py)
* **State Schema:** `AgentSchema` ([`Models/schema.py`](file:///c:/Users/AMAN/OneDrive/Desktop/Ai%20Orchastration/Models/schema.py))
* **Flow:**
  ```mermaid
  graph TD
      START([START]) --> Curate[curate_ques]
      Curate --> Context[prompt_query_context]
      Context --> GenSQL[generate_sql]
      GenSQL --> CheckSafe[is_safe_sql]
      CheckSafe --> |conditional: Yes| Execute[execute_sql]
      CheckSafe --> |conditional: No| Cancel[canceled_sql]
      Execute --> Format[represent_final_answer]
      Cancel --> END([END])
      Format --> END
  ```
* **Safety Mechanism:** 
  1. *Deterministic check*: Rejects queries that don't start with `SELECT` / `WITH` or contain blocklisted keywords (e.g. `INSERT`, `UPDATE`, `DROP`, `DO `).
  2. *LLM security judge*: Uses `JudgeSchema` validation.
  3. *Post-generation check*: Re-validates right before running the query against the database using `is_select_only()`.

---

### 3. ETL Analyst Agent
* **File:** [`agents/etl_analyst.py`](file:///c:/Users/AMAN/OneDrive/Desktop/Ai%20Orchastration/agents/etl_analyst.py)
* **State Schema:** `ETLAgentSchema` ([`Models/schema.py`](file:///c:/Users/AMAN/OneDrive/Desktop/Ai%20Orchastration/Models/schema.py))
* **Flow:**
  ```mermaid
  graph TD
      START([START]) --> LLMNode[llm_node]
      LLMNode --> |conditional: has tool calls| ToolNode[tool_node]
      LLMNode --> |conditional: no tool calls| END([END])
      ToolNode --> LLMNode
  ```
* **Tools Available:**
  * `extract_load_tool`: Downloads from API endpoints and loads to local path as CSV/JSON/Parquet.
  * `transform_load_tool`: Inspects local files, prompts high-level LLM to write Pandas code, and executes it using python's `exec`.

---

### 4. Utilities
* **Database Utility** ([`utils/database.py`](file:///c:/Users/AMAN/OneDrive/Desktop/Ai%20Orchastration/utils/database.py)): Manages PostgreSQL connection, retrieves schema definition (tables, columns, types, sample data), and executes raw queries.
* **ETL Tools** ([`utils/etl_tools.py`](file:///c:/Users/AMAN/OneDrive/Desktop/Ai%20Orchastration/utils/etl_tools.py)): Direct API queries, saving files using Pandas, and running code dynamically.
* **LLM Picker** ([`utils/llm_pick.py`](file:///c:/Users/AMAN/OneDrive/Desktop/Ai%20Orchastration/utils/llm_pick.py)): Picks Groq models dynamically:
  * `"low"`: `qwen/qwen3.6-27b`
  * `"medium"`: `qwen/qwen3.8-27b`
  * `"high"`: `openai/gpt-oss-120b`

---

## ⚡ Current FastAPI State

* **Entry point:** [`app/main.py`](file:///c:/Users/AMAN/OneDrive/Desktop/Ai%20Orchastration/app/main.py)
* **Endpoints:**
  * `GET /`: Returns basic running message.
  * `GET /health`: Returns basic healthy status.
* **Status:** Boilderplate only. No route integration with the service layer or LangGraph agents exists.

---

## ⚠️ Security Vulnerabilities & Critical Issues

> [!CAUTION]
> **Dynamic Code Execution (`exec`)**
> Inside `transform_load_tool` (in [`agents/etl_analyst.py`](file:///c:/Users/AMAN/OneDrive/Desktop/Ai%20Orchastration/agents/etl_analyst.py#L79)), code generated by the LLM is executed directly in the main runtime thread using Python's `exec()`. If an attacker compromises the context or prompts, this allows arbitrary remote code execution (RCE) on the server.

> [!WARNING]
> **Hardcoded Connection Validation**
> The PostgreSQL agent executes queries directly. Safe operations depend on the `DATABASE_URL` user having strict read-only permissions inside the actual DB cluster. If the credentials mapped to `DATABASE_URL` have write/admin privileges, any SQL injection bypassing the safety nodes could destroy/alter database data.
