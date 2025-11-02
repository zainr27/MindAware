"""
FastAPI server for agent API endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.agent import CognitivePolicy, DroneTools, DecisionLogger, AgentMemory, LLMAgent
from src.api.websocket import setup_websocket_routes
from src.api.eeg_ingestion import router as eeg_router

app = FastAPI(title="MindAware Agent API", version="1.0.0")

# Setup WebSocket routes
setup_websocket_routes(app)

# Include EEG ingestion routes
app.include_router(eeg_router, tags=["EEG"])

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent components
policy = CognitivePolicy()
tools = DroneTools()
logger = DecisionLogger()
memory = AgentMemory()

# Initialize LLM agent (requires OPENAI_API_KEY)
try:
    llm_agent = LLMAgent(tools, memory)
    print("[API] LLM agent initialized successfully")
except ValueError as e:
    print(f"[API] Warning: Could not initialize LLM agent: {e}")
    print("[API] The /agent endpoint will fail without a valid OPENAI_API_KEY")
    llm_agent = None


# Request/Response models
class CognitiveStateRequest(BaseModel):
    focus: float
    fatigue: float
    overload: float
    stress: float
    metadata: Optional[Dict[str, Any]] = None


class AgentDecisionResponse(BaseModel):
    cognitive_state: Dict[str, Any]
    policy_recommendations: List[Dict[str, Any]]
    llm_reasoning: str
    actions_taken: List[Dict[str, Any]]
    timestamp: str


class StatusResponse(BaseModel):
    status: str
    components: Dict[str, str]
    version: str


@app.get("/", response_model=StatusResponse)
async def root():
    """Root endpoint with API status."""
    return {
        "status": "operational",
        "components": {
            "llm_agent": "ready" if llm_agent else "unavailable (OPENAI_API_KEY not set)",
            "policy": "ready",
            "tools": "ready",
            "logger": "ready"
        },
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/agent", response_model=AgentDecisionResponse)
async def process_cognitive_state(request: CognitiveStateRequest):
    """
    Process a cognitive state and return agent decision.
    
    This is the main endpoint for the agent loop.
    Requires OPENAI_API_KEY to be set for LLM reasoning.
    """
    try:
        # Check if LLM agent is available
        if llm_agent is None:
            raise HTTPException(
                status_code=503,
                detail="LLM agent not initialized. OPENAI_API_KEY must be set."
            )
        
        # Convert to dict
        cognitive_state = {
            "focus": request.focus,
            "fatigue": request.fatigue,
            "overload": request.overload,
            "stress": request.stress
        }
        
        # Add to memory
        memory.add_cognitive_state(cognitive_state)
        
        # Get policy recommendations
        policy_result = policy.evaluate(cognitive_state)
        
        # Get LLM decision
        decision = llm_agent.reason_about_state(
            cognitive_state,
            policy_result["recommendations"]
        )
        
        # Log decision
        logger.log_decision(decision)
        
        # Add to memory
        memory.add_decision(decision)
        
        return decision
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs")
async def get_logs(count: int = 10):
    """Get recent decision logs."""
    try:
        logs = logger.get_recent_decisions(count)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory")
async def get_memory():
    """Get agent memory summary."""
    try:
        context = memory.get_context_summary()
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools/status")
async def get_tools_status():
    """Get current tool states."""
    return {
        "current_mode": tools.current_mode,
        "current_pattern": tools.current_pattern,
        "alert_level": tools.alert_level,
        "action_count": len(tools.action_history)
    }


@app.post("/tools/execute")
async def execute_tool(tool_name: str, arguments: Dict[str, Any]):
    """Manually execute a tool."""
    try:
        result = tools.execute_tool(tool_name, arguments)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/logs")
async def clear_logs():
    """Clear decision logs."""
    try:
        logger.clear_log()
        return {"status": "logs cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memory")
async def clear_memory():
    """Clear agent memory."""
    try:
        memory.clear()
        return {"status": "memory cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

