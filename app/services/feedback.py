from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from app.services import llm


# 1. State Definition
class QueryState(TypedDict):
    query: str
    team_id: str
    end_user_id: str
    classification: Optional[str]  # Will store 'complaint' or 'question'
    response: Optional[str]        # Will store the final LLM response


# 2. Graph Nodes
async def classify_node(state: QueryState) -> dict:
    classification = await llm.classify_query(
        state["query"],
        state["team_id"],
        state["end_user_id"]
    )
    # Return updates to merge into state
    return {"classification": classification}


async def handle_complaint_node(state: QueryState) -> dict:
    response = await llm.generate_complaint_response(
        state["query"],
        state["team_id"],
        state["end_user_id"]
    )
    return {"response": response}


async def handle_question_node(state: QueryState) -> dict:
    response = await llm.generate_question_response(
        state["query"],
        state["team_id"],
        state["end_user_id"]
    )
    return {"response": response}


# 3. Conditional Routing Edge function
def route_query(state: QueryState) -> str:
    classification = state.get("classification")
    if classification == "complaint":
        return "complaint"
    # Fallback to question (handles 'question' and edge cases)
    return "question"


# 4. Building the Graph
workflow = StateGraph(QueryState)

# Register nodes
workflow.add_node("classify", classify_node)
workflow.add_node("handle_complaint", handle_complaint_node)
workflow.add_node("handle_question", handle_question_node)

# Set the Entry Point
workflow.set_entry_point("classify")

# Link node with conditional routing edges
workflow.add_conditional_edges(
    "classify",
    route_query,
    {
        "complaint": "handle_complaint",
        "question": "handle_question"
    }
)

# Connect processing nodes to END
workflow.add_edge("handle_complaint", END)
workflow.add_edge("handle_question", END)

# Compile graph into a runnable
app_graph = workflow.compile()


# 5. Graph Invocation Interface
async def run_feedback_flow(
    query: str,
    team_id: str,
    end_user_id: str
) -> dict:
    initial_state = {
        "query": query,
        "team_id": team_id,
        "end_user_id": end_user_id,
        "classification": None,
        "response": None
    }
    # Invoke the compiled graph asynchronously
    final_state = await app_graph.ainvoke(initial_state)
    return final_state