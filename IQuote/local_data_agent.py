#!/usr/bin/env python3
"""
Local Data Agent - A2A Protocol Implementation
This agent acts as an A2A protocol agent that processes business requirements,
uses LLM to refine solutions, and provides customer-friendly proposals.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn
import httpx
from langchain_openai import ChatOpenAI

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import configuration
try:
    from api_keys import Config
except ImportError:
    print("❌ Error: `api_keys.py` not found or `Config` class is missing.")
    print("Please ensure the file exists and is correctly structured.")
    exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A2A Protocol Data Models
@dataclass
class A2ASkill:
    """A2A Skill definition"""
    id: str
    name: str
    description: str
    tags: List[str]
    examples: List[str]

@dataclass
class A2AAgentCard:
    """A2A Agent Card for discovering capabilities"""
    name: str
    description: str
    url: str
    version: str
    default_input_modes: List[str]
    default_output_modes: List[str]
    skills: List[A2ASkill]
    authentication: Dict[str, Any]
    capabilities: Dict[str, Any]

@dataclass
class A2AMessagePart:
    """A2A Message Part"""
    kind: str
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

@dataclass
class A2AMessage:
    """A2A Message"""
    role: str
    parts: List[A2AMessagePart]
    message_id: str
    timestamp: str

# LLM Prompt Template
LLM_PROMPT_TEMPLATE = """
You are an expert sales assistant. Your task is to rephrase a technical solution into a compelling, customer-friendly proposal.

**Original Technical Solution:**
---
{solution_text}
---

**Your Task:**
Rewrite the solution above. Focus on the business value and benefits.
- Start with a friendly and professional opening.
- Clearly explain what each part of the solution does for the customer's business.
- Emphasize the cost-effectiveness and scalability.
- **Crucially, highlight the volume discounts.** Explain that the displayed price is an estimate and purchasing for all branches at once will lead to significant savings. Make this a clear call to action.
- End with a call to action, encouraging the customer to discuss further details.
"""

class LocalDataAgent:
    """
    Local Data Agent implementing A2A protocol
    Processes business requirements and provides customer-friendly proposals
    """
    
    def __init__(self, port: int = 8003):
        self.port = port
        self.base_url = f"http://localhost:{port}"
        
        # Initialize LLM client
        self.llm = self.get_llm_client()
        
        # Define A2A skills
        self.skills = [
            A2ASkill(
                id="analyze_requirements",
                name="Analyze Business Requirements",
                description="Analyze business requirements and provide customer-friendly solutions",
                tags=["business", "analysis", "solutions", "networking"],
                examples=[
                    "I need networking solutions for 10 new retail branches",
                    "Analyze requirements for SD-WAN and wireless setup",
                    "Provide solution for branch expansion"
                ]
            ),
            A2ASkill(
                id="generate_proposal",
                name="Generate Customer Proposal",
                description="Generate customer-friendly proposals with pricing and recommendations",
                tags=["proposal", "pricing", "recommendations", "sales"],
                examples=[
                    "Generate proposal for networking solution",
                    "Create customer-friendly pricing proposal",
                    "Provide detailed solution recommendations"
                ]
            )
        ]
        
        # Create A2A agent card
        self.agent_card = A2AAgentCard(
            name="Local Data Agent - Business Solution Advisor",
            description="Analyzes business requirements and provides customer-friendly networking solutions with LLM-enhanced proposals",
            url=self.base_url,
            version="1.0.0",
            default_input_modes=["text"],
            default_output_modes=["text", "json"],
            skills=self.skills,
            authentication={"schemes": ["public"]},
            capabilities={"streaming": False, "async": True, "llm_enhanced": True}
        )
        
        # Task tracking
        self.active_tasks = {}
        
        # Setup FastAPI app
        self.app = FastAPI(title="Local Data Agent", version="1.0.0")
        self.setup_routes()
    
    def get_llm_client(self):
        """Initialize LLM client"""
        try:
            config = Config()
            asi_config = config.get_asi_one_config()
            return ChatOpenAI(
                model=asi_config['model'],
                api_key=asi_config['api_key'],
                base_url=asi_config['base_url'],
                temperature=asi_config.get('temperature', 0.7),
                max_tokens=asi_config.get('max_tokens', 1024),
                timeout=asi_config.get('timeout', 30)
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            return None
    
    def setup_routes(self):
        """Setup FastAPI routes for A2A protocol"""
        
        @self.app.get("/.well-known/agent.json")
        async def get_agent_card():
            """Return the A2A agent card"""
            logger.info("A2A Agent card requested")
            return asdict(self.agent_card)
        
        @self.app.post("/")
        async def handle_a2a_message(request: Request):
            """Handle A2A protocol messages"""
            try:
                data = await request.json()
                logger.info(f"Received A2A message: {data}")
                
                # Validate JSON-RPC 2.0 format
                if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
                    raise HTTPException(status_code=400, detail="Invalid JSON-RPC version")
                
                if "method" not in data:
                    raise HTTPException(status_code=400, detail="Missing method")
                
                method = data["method"]
                params = data.get("params", {})
                request_id = data.get("id")
                
                # Handle different A2A methods
                if method == "message/send":
                    response = await self.handle_message_send(params, request_id)
                elif method == "tasks/get":
                    response = await self.handle_task_get(params, request_id)
                elif method == "agent/capabilities":
                    response = await self.handle_capabilities_request(request_id)
                else:
                    raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
                
                return JSONResponse(content=response)
                
            except Exception as e:
                logger.error(f"Error handling A2A message: {e}")
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "error": {"code": -32603, "message": str(e)},
                        "id": data.get("id")
                    },
                    status_code=500
                )
    
    async def handle_message_send(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Handle A2A message/send method"""
        logger.info(f"Handling message/send with params: {params}")
        
        message = params.get("message", {})
        parts = message.get("parts", [])
        
        # Extract text content from A2A message parts
        text_content = ""
        for part in parts:
            if part.get("kind") == "text":
                text_content += part.get("text", "")
        
        logger.info(f"Processing business requirement: {text_content}")
        
        # Process the business requirement
        result = await self.process_business_requirement(text_content)
        
        # Create task ID for tracking
        task_id = f"task_{datetime.now().timestamp()}"
        self.active_tasks[task_id] = {
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "task_id": task_id,
                "status": "completed",
                "response": result
            },
            "id": request_id
        }
    
    async def handle_task_get(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Handle A2A task status requests"""
        task_id = params.get("id")
        
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "jsonrpc": "2.0",
                "result": task,
                "id": request_id
            }
        else:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": f"Task {task_id} not found"},
                "id": request_id
            }
    
    async def handle_capabilities_request(self, request_id: str) -> Dict[str, Any]:
        """Handle capabilities request"""
        return {
            "jsonrpc": "2.0",
            "result": asdict(self.agent_card),
            "id": request_id
        }
    
    async def process_business_requirement(self, requirement: str) -> Dict[str, Any]:
        """Process business requirement and generate customer-friendly proposal"""
        logger.info(f"Processing requirement: {requirement}")
        
        # Get technical solution from Solution Architect Agent via adapter
        technical_solution = await self.get_technical_solution(requirement)
        
        if technical_solution.get("error"):
            logger.error(f"Error getting technical solution: {technical_solution['error']}")
            # Fallback to mock solution
            technical_solution_text = self.get_mock_solution()
        else:
            technical_solution_text = technical_solution.get("content", "No solution provided")
        
        # Use LLM to refine the solution
        if self.llm:
            try:
                prompt = LLM_PROMPT_TEMPLATE.format(solution_text=technical_solution_text)
                refined_response = await self.llm.ainvoke(prompt)
                
                return {
                    "proposal_type": "customer_friendly",
                    "content": refined_response.content,
                    "original_technical_solution": technical_solution_text,
                    "processed_by": "llm_enhanced",
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"LLM processing failed: {e}")
                return {
                    "proposal_type": "technical_fallback",
                    "content": technical_solution_text,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        else:
            return {
                "proposal_type": "technical_only",
                "content": technical_solution_text,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_technical_solution(self, requirement: str) -> Dict[str, Any]:
        """Get technical solution from Solution Architect Agent via adapter"""
        try:
            # Import the adapter client
            from adapter.a2a_to_uagent_adapter import A2AAdapterClient
            
            # Create adapter client
            adapter_client = A2AAdapterClient(adapter_port=8004)
            
            # Start the adapter (this would be running separately in production)
            solution_architect_address = "agent1qw2e3r4t5y6u7i8o9p0a1s2d3f4g5h6j7k8l9m0n1b2v3c4x5z6"
            await adapter_client.start_adapter(solution_architect_address)
            
            # Send the requirement through the adapter
            response = await adapter_client.send_a2a_message(requirement)
            
            logger.info("✅ Received technical solution from adapter")
            return response
            
        except Exception as e:
            logger.error(f"Error communicating with adapter: {e}")
            return {"error": str(e)}
    
    def get_mock_solution(self) -> str:
        """Get mock solution as fallback"""
        return """
        Based on your requirements for 10 new branches, here is a proposed solution:

        Recommended Products:
        - CloudConnect SD-WAN M (SDW-2000): $3,500.00/unit
          - Use cases: SD-WAN, Network Security, Access Security
        - NetSwitch 48-Port L3 (SW-48): $1,500.00/unit
          - Use cases: Switching
        - AirWave Wi-Fi 6 Pro AP (AP-W6-PRO): $600.00/unit
          - Use cases: Wireless
        - SecureWall Firewall 100 (SEC-FW-100): $2,000.00/unit
          - Use cases: Network Security

        Estimated Cost per Branch: $7,600.00
        Estimated Total for 10 Branches: $76,000.00

        This is a preliminary recommendation for your networking solution requirements.
        """
    
    def run(self, host: str = "0.0.0.0", port: int = None):
        """Run the A2A agent"""
        if port is None:
            port = self.port
        
        logger.info(f"🚀 Starting Local Data Agent (A2A) on {host}:{port}")
        logger.info(f"Agent card available at: http://{host}:{port}/.well-known/agent.json")
        
        uvicorn.run(self.app, host=host, port=port, log_level="info")

# Demo client for testing
class A2AClient:
    """Simple A2A client for testing"""
    
    def __init__(self, agent_url: str):
        self.agent_url = agent_url
    
    async def send_message(self, text: str) -> Dict[str, Any]:
        """Send a message to the A2A agent"""
        message = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "parts": [{"kind": "text", "text": text}],
                    "role": "user"
                }
            },
            "id": f"req_{datetime.now().timestamp()}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.agent_url, json=message, timeout=30)
            return response.json()

async def demo_local_data_agent():
    """Demo function to test the Local Data Agent"""
    print("🧪 Testing Local Data Agent (A2A Protocol)")
    print("=" * 60)
    
    # Test message
    test_requirement = "I am a solution architect at a retail store, I want to purchase networking solutions to set up 10 new branches to expand my business. The solution should include SD-WAN, switching, wireless, network security, and access security features."
    
    client = A2AClient("http://localhost:8003")
    
    try:
        response = await client.send_message(test_requirement)
        print("✅ Response received:")
        print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        asyncio.run(demo_local_data_agent())
    else:
        agent = LocalDataAgent()
        agent.run() 