from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from app.services.agent import agent_app

router = APIRouter(
    prefix="/agent",
    tags=["Agent"]
)

class AgentChatRequest(BaseModel):
    message: str = Field(..., examples=["Is shipment 1 delayed?"])
    thread_id: str = Field(..., examples=["thread-1"])
    team_id: str = Field(..., examples=["internship-team"])
    end_user_id: str = Field(..., examples=["prana"])

class AgentChatResponse(BaseModel):
    response: str
    history: list[dict]

@router.post("/chat", response_model=AgentChatResponse)
async def chat_with_agent(req: AgentChatRequest):
    # WHY: The configurable parameter thread_id tells the checkpointer where to load/save state.
    config = {"configurable": {"thread_id": req.thread_id}}
    
    input_state = {
        "messages": [HumanMessage(content=req.message)],
        "steps": 0
    }
    
    try:
        final_state = await agent_app.ainvoke(input_state, config=config)
        messages = final_state["messages"]
        last_message = messages[-1]
        
        # Format message history to return in the API response
        formatted_history = []
        for msg in messages:
            role = "user"
            if msg.type == "human":
                role = "user"
            elif msg.type == "ai":
                role = "assistant"
            elif msg.type == "tool":
                role = "tool"
                
            formatted_history.append({
                "role": role,
                "content": msg.content,
                "name": getattr(msg, "name", None)
            })
            
        return AgentChatResponse(
            response=last_message.content,
            history=formatted_history
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent invocation failed: {str(e)}")