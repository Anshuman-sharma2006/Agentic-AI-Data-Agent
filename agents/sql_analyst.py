import os
import sys
import re

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from utils.llm_pick import pick_llm
from utils.database import DatabaseUtil
from Models.schema import AgentSchema, JudgeSchema

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END


# ============================================================
# Helper Functions
# ============================================================

def clean_sql(sql: str) -> str:
    """
    Clean accidental Markdown/code fences from LLM-generated SQL.
    """

    if not sql:
        return ""

    sql = sql.strip()

    # Remove ```sql / ```SQL
    sql = re.sub(
        r"^```(?:sql|postgresql)?\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    # Remove closing ```
    sql = re.sub(
        r"\s*```$",
        "",
        sql
    )

    return sql.strip()


def is_select_only(sql: str) -> bool:
    """
    Basic deterministic safety check.

    Allows only SELECT / WITH queries.
    Blocks common destructive SQL commands.
    """

    if not sql:
        return False

    normalized = sql.strip().lower()

    # Remove trailing semicolon
    normalized = normalized.rstrip(";").strip()

    # Only SELECT or WITH queries are allowed
    if not (
        normalized.startswith("select ")
        or normalized.startswith("select\n")
        or normalized.startswith("with ")
        or normalized.startswith("with\n")
    ):
        return False

    dangerous_commands = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "grant",
        "revoke",
        "replace",
        "merge",
        "call",
        "do ",
    ]

    # Check SQL tokens
    for command in dangerous_commands:
        pattern = rf"\b{re.escape(command)}\b"

        if re.search(pattern, normalized):
            return False

    return True


# ============================================================
# 1. CURATE QUESTION
# ============================================================

def curate_ques(state: AgentSchema) -> AgentSchema:

    user_question = state.user_question

    llm = pick_llm("low")

    prompt = f"""
You are a query clarification agent.

Your ONLY task is to rewrite the user's request into one clear,
concise natural-language question that can be given to a PostgreSQL
SQL generation agent.

IMPORTANT RULES:

1. Preserve the user's original intent.
2. Return ONLY the rewritten natural-language question.
3. Do NOT generate SQL.
4. Do NOT include SQL code.
5. Do NOT include Markdown.
6. Do NOT include Python code.
7. Do NOT include REST API examples.
8. Do NOT include implementation notes.
9. Do NOT explain your changes.
10. Do NOT answer the question.
11. Do NOT invent requirements.
12. Keep the question concise.

Examples:

Input:
Show me active users from Vancouver BC

Output:
Show me all active users located in Vancouver, British Columbia.

Input:
How many completed rides happened in 2026?

Output:
How many completed rides occurred in 2026?

USER REQUEST:
{user_question}

Return ONLY the cleaned natural-language question.
"""

    response = llm.invoke(prompt)

    curated_question = response.content.strip()

    state.curated_ques = curated_question

    # Append curated question to messages
    state.messages = state.messages + [
        HumanMessage(content=curated_question)
    ]

    return state


# ============================================================
# 2. BUILD SQL PROMPT
# ============================================================

def prompt_query_context(state: AgentSchema) -> AgentSchema:

    curated_question = state.curated_ques

    conn_details = os.environ["DATABASE_URL"]

    obj = DatabaseUtil(conn_details)

    schema_info = obj.schema_details("public")

    prompt = f"""
You are a PostgreSQL SQL generation agent.

Your ONLY task is to convert the user's natural-language question
into ONE executable PostgreSQL SQL query.

DATABASE SCHEMA:

{schema_info}

IMPORTANT RULES:

1. Return ONLY the raw SQL query.
2. Do NOT use Markdown.
3. Do NOT use ```sql.
4. Do NOT use ``` fences.
5. Do NOT provide explanations.
6. Do NOT provide comments.
7. Do NOT provide Python.
8. Do NOT provide REST API code.
9. Do NOT provide natural-language text.
10. The result must be directly executable by PostgreSQL.
11. Only generate SELECT queries.
12. WITH queries are allowed when necessary.
13. Never generate INSERT.
14. Never generate UPDATE.
15. Never generate DELETE.
16. Never generate DROP.
17. Never generate ALTER.
18. Never generate TRUNCATE.
19. Never generate CREATE.
20. Never generate GRANT.
21. Never generate REVOKE.
22. Use only tables and columns present in the schema.
23. Do not invent tables or columns.
24. Use appropriate JOINs when required.
25. Unless the user explicitly requests a number of rows,
    add LIMIT 10.
26. For aggregate questions such as COUNT, SUM, AVG, MIN, or MAX,
    do not add LIMIT unless it is logically necessary.
27. PostgreSQL syntax must be used.

USER QUESTION:

{curated_question}

Return ONLY the executable PostgreSQL SQL query.
"""

    state.prompt_query_context = prompt

    return state


# ============================================================
# 3. GENERATE SQL
# ============================================================

def generate_sql(state: AgentSchema) -> AgentSchema:

    prompt = state.prompt_query_context

    llm = pick_llm("medium")

    response = llm.invoke(prompt)

    generated_sql = response.content

    # Clean accidental Markdown fences
    generated_sql = clean_sql(generated_sql)

    state.generated_sql_query = generated_sql

    return state


# ============================================================
# 4. CHECK SQL SAFETY
# ============================================================

def is_safe_sql(state: AgentSchema) -> AgentSchema:

    sql_query = state.generated_sql_query

    # --------------------------------------------------------
    # First perform deterministic validation
    # --------------------------------------------------------

    if not is_select_only(sql_query):

        state.is_safe = "No"
        state.comments = (
            "The generated query is not a SELECT-only query "
            "or contains a potentially destructive SQL command."
        )

        return state

    # --------------------------------------------------------
    # Then use LLM judge
    # --------------------------------------------------------

    llm = pick_llm("medium")

    llm_judge = llm.with_structured_output(JudgeSchema)

    prompt = f"""
You are an SQL security judge.

Determine whether the following PostgreSQL query is safe
to execute for read-only data retrieval.

SAFE queries:
- SELECT
- WITH ... SELECT

UNSAFE queries:
- INSERT
- UPDATE
- DELETE
- DROP
- ALTER
- TRUNCATE
- CREATE
- GRANT
- REVOKE
- MERGE
- CALL
- DO
- Any query that modifies database data or structure.

SQL QUERY:

{sql_query}

Return:
answer = "Yes" if safe
answer = "No" if unsafe

Also provide a short explanation.
"""

    try:

        response = llm_judge.invoke(prompt)

        result = response.model_dump()

        state.is_safe = result["answer"]
        state.comments = result["comments"]

    except Exception as e:

        # Fail closed
        state.is_safe = "No"
        state.comments = (
            f"SQL safety validation failed: {str(e)}"
        )

    return state


# ============================================================
# 5. CANCEL UNSAFE SQL
# ============================================================

def canceled_sql(state: AgentSchema) -> AgentSchema:

    comments = state.comments

    state.final_answer = (
        "I couldn't execute the requested database operation "
        "because the generated query was not considered safe. "
        f"Reason: {comments}"
    )

    state.messages = state.messages + [
        AIMessage(content=state.final_answer)
    ]

    return state


# ============================================================
# 6. EXECUTE SQL
# ============================================================

def execute_sql(state: AgentSchema) -> AgentSchema:

    sql_query = state.generated_sql_query

    # --------------------------------------------------------
    # Final deterministic safety check before database
    # --------------------------------------------------------

    if not is_select_only(sql_query):

        state.sql_query_execution_result = (
            "SQL execution blocked: query failed the final "
            "read-only safety check."
        )

        return state

    conn_details = os.getenv("DATABASE_URL")

    if not conn_details:

        state.sql_query_execution_result = (
            "DATABASE_URL environment variable is not configured."
        )

        return state

    try:

        obj = DatabaseUtil(conn_details)

        execution_result = obj.execute_sql(sql_query)

        state.sql_query_execution_result = execution_result

    except Exception as e:

        state.sql_query_execution_result = (
            f"Error executing query: {str(e)}"
        )

    return state


# ============================================================
# 7. REPRESENT FINAL ANSWER
# ============================================================

def represent_final_answer(state: AgentSchema) -> AgentSchema:

    execution_result = state.sql_query_execution_result
    curated_question = state.curated_ques

    llm = pick_llm("low")

    prompt = f"""
You are the final response agent for a PostgreSQL data analysis system.

Your task is to answer the user's question using the SQL execution
result provided below.

USER QUESTION:

{curated_question}

DATABASE RESULT:

{execution_result}

IMPORTANT RULES:

1. Answer the user's question directly.
2. Be concise and easy to understand.
3. Do NOT generate SQL.
4. Do NOT show SQL.
5. Do NOT mention SQL syntax.
6. Do NOT mention prompts.
7. Do NOT mention agents.
8. Do NOT mention database implementation details.
9. Do NOT invent information.
10. Use ONLY the information present in the database result.
11. If records were found, summarize them clearly.
12. If there are no records, say that no matching records were found.
13. If the database execution failed, explain that the data could
    not be retrieved.
14. Do not expose raw technical errors unless necessary.
15. If the result contains an aggregate such as COUNT, SUM, AVG,
    MIN, or MAX, clearly explain the value.
16. If the result contains a small number of rows, present the
    important information in a readable bullet list.
17. Return ONLY the final answer.

"""

    response = llm.invoke(prompt)

    final_answer = response.content.strip()

    state.final_answer = final_answer

    state.messages = state.messages + [
        AIMessage(content=final_answer)
    ]

    return state


# ============================================================
# GRAPH BUILDING
# ============================================================

sql_agent_graph = StateGraph(AgentSchema)


# ------------------------------------------------------------
# Nodes
# ------------------------------------------------------------

sql_agent_graph.add_node(
    "curate_ques",
    curate_ques
)

sql_agent_graph.add_node(
    "prompt_query_context",
    prompt_query_context
)

sql_agent_graph.add_node(
    "generate_sql",
    generate_sql
)

sql_agent_graph.add_node(
    "is_safe_sql",
    is_safe_sql
)

sql_agent_graph.add_node(
    "canceled_sql",
    canceled_sql
)

sql_agent_graph.add_node(
    "execute_sql",
    execute_sql
)

sql_agent_graph.add_node(
    "represent_final_answer",
    represent_final_answer
)


# ------------------------------------------------------------
# Edges
# ------------------------------------------------------------

sql_agent_graph.add_edge(
    START,
    "curate_ques"
)

sql_agent_graph.add_edge(
    "curate_ques",
    "prompt_query_context"
)

sql_agent_graph.add_edge(
    "prompt_query_context",
    "generate_sql"
)

sql_agent_graph.add_edge(
    "generate_sql",
    "is_safe_sql"
)


# ------------------------------------------------------------
# Conditional Safety Edge
# ------------------------------------------------------------

def is_safe_sql_edge(state: AgentSchema) -> str:

    is_safe = state.is_safe

    if is_safe and is_safe.lower() == "yes":
        return "execute_sql"

    return "canceled_sql"


sql_agent_graph.add_conditional_edges(
    "is_safe_sql",
    is_safe_sql_edge,
    {
        "execute_sql": "execute_sql",
        "canceled_sql": "canceled_sql"
    }
)


# ------------------------------------------------------------
# Remaining Edges
# ------------------------------------------------------------

sql_agent_graph.add_edge(
    "canceled_sql",
    END
)

sql_agent_graph.add_edge(
    "execute_sql",
    "represent_final_answer"
)

sql_agent_graph.add_edge(
    "represent_final_answer",
    END
)


# ============================================================
# COMPILE GRAPH
# ============================================================

sql_analyst = sql_agent_graph.compile()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Generate Graph Image
    # --------------------------------------------------------

    from IPython.display import Image

    img = Image(
        sql_analyst.get_graph().draw_mermaid_png()
    )

    with open(
        "sql_analyst_graph.png",
        "wb"
    ) as f:

        f.write(img.data)


    # --------------------------------------------------------
    # Initial State
    # --------------------------------------------------------

    input_schema = {

        "messages": [],

        "user_question":
            "Show me all active users from Vancouver."
            "city = Vancouver, province = BC, is_active = True",

        "curated_ques": "",

        "prompt_query_context": "",

        "generated_sql_query": "",

        "is_safe": "No",

        "comments": "",

        "sql_query_execution_result": "",

        "final_answer": ""
    }


    # --------------------------------------------------------
    # Run Graph
    # --------------------------------------------------------

    sql_analyst_response = sql_analyst.invoke(
        input_schema
    )


    # ========================================================
    # OUTPUT
    # ========================================================

    print("\n========== FINAL ANSWER ==========")

    print(
        sql_analyst_response["final_answer"]
    )


    print("\n========== CURATED QUESTION ==========")

    print(
        sql_analyst_response["curated_ques"]
    )


    print("\n========== GENERATED SQL ==========")

    print(
        sql_analyst_response["generated_sql_query"]
    )


    print("\n========== SQL SAFETY ==========")

    print(
        sql_analyst_response["is_safe"]
    )

    print(
        sql_analyst_response["comments"]
    )


    print("\n========== SQL RESULT ==========")

    print(
        sql_analyst_response[
            "sql_query_execution_result"
        ]
    )


    print("\n========== MESSAGES ==========")

    for message in sql_analyst_response["messages"]:

        print(
            f"{message.__class__.__name__}: "
            f"{message.content}"
        )


    print("\n********************************")