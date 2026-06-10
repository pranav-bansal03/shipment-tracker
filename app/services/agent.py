from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
from app.services.tools import get_shipment_status, list_delayed_shipments

# 1. State Definition
# WHY: 'messages' uses the add_messages reducer so new messages (user, assistant, tool) append.
# 'steps' tracks the number of loop iterations for our max-step guard.
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    steps: int

# 2. LLM Setup
# WHY: We configure ChatOpenAI with the custom model server credentials.
# HOW: We bind our tools so the model knows they are available.
llm = ChatOpenAI(
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
    model=LLM_MODEL,
    temperature=0.0
)

tools = [get_shipment_status, list_delayed_shipments]
llm_with_tools = llm.bind_tools(tools)

# 3. Model Node
# WHY: Invokes the LLM and increments our step counter.
async def call_model(state: AgentState) -> dict:
    steps = state.get("steps", 0)
    response = await llm_with_tools.ainvoke(state["messages"])
    return {
        "messages": [response],
        "steps": steps + 1
    }

# 4. Tool Execution Node (By Hand)
# WHY: Instead of a prebuilt node, we implement the execution logic ourselves to learn how it works.
# HOW: Read the requested 'tool_calls' from the last message, execute the python function, and return a ToolMessage.
async def execute_tools(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    tool_messages = []
    tool_map = {t.name: t for t in tools}
    
    for tool_call in last_message.tool_calls:
        name = tool_call["name"]
        args = tool_call["args"]
        call_id = tool_call["id"]
        
        if name in tool_map:
            tool = tool_map[name]
            try:
                result = await tool.ainvoke(args)
            except Exception as e:
                result = f"Error: {e}"
        else:
            result = f"Tool '{name}' not found."
            
        tool_messages.append(
            ToolMessage(
                content=str(result),
                name=name,
                tool_call_id=call_id
            )
        )
    return {"messages": tool_messages}

# 5. Conditional Routing Edge
# WHY: Decides whether to continue looping (call tool) or end execution (return final answer).
# Max-steps guard (here, capped at 5 steps) prevents runaway infinite loops.
def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    steps = state.get("steps", 0)
    
    # Runaway loop protection
    if steps >= 5:
        return "end"
        
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
        
    return "end"

# 6. Graph Compilation
# WHY: Connecting our nodes, conditional edges, and compiling with memory.
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("action", execute_tools)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action",
        "end": END
    }
)

workflow.add_edge("action", "agent")

# MemorySaver provides conversation memory using thread_id checkpointing
memory = MemorySaver()
agent_app = workflow.compile(checkpointer=memory)