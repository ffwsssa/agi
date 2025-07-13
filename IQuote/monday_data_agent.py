#!/usr/bin/env python3
"""
Monday Data Agent - A2A Protocol Implementation
This agent acts as an A2A protocol agent that connects to Monday.com API
to retrieve project data, boards, items, and other information.
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

# LLM Prompt Template for Monday.com data processing
LLM_PROMPT_TEMPLATE = """
You are an expert sales and product catalog assistant specializing in Monday.com data analysis for networking products and services.

**Monday.com Product Catalog Data:**
---
{monday_data}
---

**User Query:**
---
{user_query}
---

**Product Data Context:**
The data comes from a "Products & Services" board containing networking products with these key fields:
- Product_ID: Unique identifier
- Category: Product category (SD-WAN, Customer Success, etc.)
- Product_Name: Full product name
- Tier: Size tier (Small, Large, Both)
- Unit_Price: One-time purchase price
- Recurring_Monthly: Monthly subscription fee
- License_Term: Contract term
- Required_Services: Mandatory services
- Optional_Services: Optional add-ons
- Min_Quantity & Max_Quantity: Quantity limits

**Your Task:**
Analyze the product catalog data and respond to the user's query. Focus on:
- Providing clear product recommendations based on requirements
- Calculating accurate pricing (one-time + monthly costs)
- Highlighting relevant tiers and categories
- Suggesting complementary services and add-ons
- Identifying volume discounts and multi-product bundles
- Present information in a sales-friendly format suitable for quotations

**Response Format:**
- Start with a brief summary of findings
- List relevant products with clear pricing
- Highlight key benefits and features
- Suggest next steps for the customer
- Make recommendations that match their business needs

Make sure to reference specific product IDs and pricing when possible.
"""

class MondayDataAgent:
    """
    Monday Data Agent implementing A2A protocol
    Connects to Monday.com API to retrieve and analyze project data
    """
    
    def __init__(self, port: int = 8005):
        self.port = port
        self.base_url = f"http://localhost:{port}"
        
        # Initialize LLM client
        self.llm = self.get_llm_client()
        
        # Initialize Monday.com API client
        self.monday_config = self.get_monday_config()
        
        # Define A2A skills
        self.skills = [
            A2ASkill(
                id="query_product_catalog",
                name="Query Product Catalog",
                description="Retrieve and analyze networking products and services from Monday.com catalog",
                tags=["products", "catalog", "networking", "pricing"],
                examples=[
                    "Show me all SD-WAN products",
                    "Find products under $5000",
                    "List all Customer Success services",
                    "What are the available tiers for SD-WAN?"
                ]
            ),
            A2ASkill(
                id="generate_quotes",
                name="Generate Product Quotes",
                description="Generate pricing quotes and recommendations based on customer requirements",
                tags=["quotes", "pricing", "recommendations", "sales"],
                examples=[
                    "Generate quote for small business SD-WAN setup",
                    "Calculate pricing for 10 branch offices",
                    "Recommend products for enterprise networking",
                    "Create bundle pricing for SD-WAN + Support"
                ]
            ),
            A2ASkill(
                id="analyze_pricing",
                name="Analyze Pricing & Bundles",
                description="Analyze product pricing, identify discounts, and suggest optimal bundles",
                tags=["pricing", "bundles", "discounts", "analysis"],
                examples=[
                    "Find the most cost-effective SD-WAN solution",
                    "Compare pricing between different tiers",
                    "Suggest complementary services",
                    "Calculate total cost of ownership"
                ]
            ),
            A2ASkill(
                id="product_recommendations",
                name="Product Recommendations",
                description="Provide intelligent product recommendations based on customer needs",
                tags=["recommendations", "matching", "requirements", "consulting"],
                examples=[
                    "Recommend products for retail chain expansion",
                    "What services are required for SD-WAN deployment?",
                    "Suggest products for medium-sized business",
                    "Find alternatives to expensive solutions"
                ]
            )
        ]
        
        # Create A2A agent card
        self.agent_card = A2AAgentCard(
            name="Monday Data Agent - Project Management Assistant",
            description="Connects to Monday.com API to retrieve and analyze project data, boards, items, and team workload",
            url=self.base_url,
            version="1.0.0",
            default_input_modes=["text"],
            default_output_modes=["text", "json"],
            skills=self.skills,
            authentication={"schemes": ["api_key"]},
            capabilities={"streaming": False, "async": True, "monday_integration": True}
        )
        
        # Task tracking
        self.active_tasks = {}
        
        # Setup FastAPI app
        self.app = FastAPI(title="Monday Data Agent", version="1.0.0")
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
    
    def get_monday_config(self):
        """Get Monday.com configuration"""
        try:
            config = Config()
            return config.get_monday_config()
        except Exception as e:
            logger.error(f"Failed to get Monday.com config: {e}")
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
        
        logger.info(f"Processing Monday.com query: {text_content}")
        
        # Process the Monday.com query
        result = await self.process_monday_query(text_content)
        
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
    
    async def process_monday_query(self, query: str) -> Dict[str, Any]:
        """Process Monday.com query and return analyzed data"""
        logger.info(f"Processing Monday.com query: {query}")
        
        try:
            # Get data from Monday.com based on query
            monday_data = await self.get_monday_data(query)
            
            if monday_data.get("error"):
                logger.error(f"Error getting Monday.com data: {monday_data['error']}")
                return {
                    "error": monday_data["error"],
                    "fallback_message": "Unable to retrieve Monday.com data at this time.",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Use LLM to analyze the data if available
            if self.llm and monday_data.get("data"):
                try:
                    prompt = LLM_PROMPT_TEMPLATE.format(
                        monday_data=json.dumps(monday_data["data"], indent=2),
                        user_query=query
                    )
                    
                    analysis = await self.llm.ainvoke(prompt)
                    
                    return {
                        "analysis": analysis.content,
                        "raw_data": monday_data["data"],
                        "query": query,
                        "processed_by": "llm_enhanced",
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error(f"LLM processing failed: {e}")
                    return {
                        "raw_data": monday_data["data"],
                        "query": query,
                        "error": f"LLM processing failed: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                return {
                    "raw_data": monday_data.get("data", {}),
                    "query": query,
                    "processed_by": "raw_data_only",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error processing Monday.com query: {e}")
            return {
                "error": str(e),
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_monday_data(self, query: str) -> Dict[str, Any]:
        """Get data from Monday.com API based on query"""
        if not self.monday_config:
            return {"error": "Monday.com configuration not available"}
        
        try:
            # Analyze query to determine what data to fetch
            query_lower = query.lower()
            
            # Your specific board ID from the URL
            your_board_id = 9576452065
            
            # Build GraphQL query based on user intent
            if "board" in query_lower or "product" in query_lower or "service" in query_lower:
                # Query for your specific products/services board
                graphql_query = f"""
                query {{
                    boards(ids: {your_board_id}) {{
                        id
                        name
                        description
                        state
                        items_count
                        updated_at
                        groups {{
                            id
                            title
                            color
                        }}
                        columns {{
                            id
                            title
                            type
                            settings_str
                        }}
                        items_page {{
                            items {{
                                id
                                name
                                created_at
                                updated_at
                                group {{
                                    id
                                    title
                                }}
                                column_values {{
                                    id
                                    text
                                    value
                                    type
                                }}
                            }}
                        }}
                    }}
                }}
                """
            elif "item" in query_lower or "task" in query_lower:
                # Query for specific items/tasks in your board
                graphql_query = f"""
                query {{
                    boards(ids: {your_board_id}) {{
                        id
                        name
                        items_page(limit: 50) {{
                            items {{
                                id
                                name
                                state
                                created_at
                                updated_at
                                creator {{
                                    id
                                    name
                                    email
                                }}
                                group {{
                                    id
                                    title
                                }}
                                column_values {{
                                    id
                                    text
                                    value
                                    type
                                }}
                            }}
                        }}
                    }}
                }}
                """
            elif "workspace" in query_lower:
                # Query for workspaces
                graphql_query = """
                query {
                    workspaces {
                        id
                        name
                        description
                        created_at
                        users {
                            id
                            name
                            email
                        }
                    }
                }
                """
            else:
                # Default query - get your specific board overview
                graphql_query = f"""
                query {{
                    boards(ids: {your_board_id}) {{
                        id
                        name
                        description
                        state
                        items_count
                        updated_at
                        columns {{
                            id
                            title
                            type
                        }}
                        groups {{
                            id
                            title
                        }}
                    }}
                }}
                """
            
            # Make API request to Monday.com
            headers = {
                "Authorization": self.monday_config["api_key"],
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": graphql_query
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.monday_config["api_url"],
                    headers=headers,
                    json=payload,
                    timeout=self.monday_config.get("timeout", 30)
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    if "errors" in response_data:
                        logger.error(f"Monday.com API errors: {response_data['errors']}")
                        return {"error": f"Monday.com API errors: {response_data['errors']}"}
                    
                    return {"data": response_data.get("data", {})}
                else:
                    logger.error(f"Monday.com API error: {response.status_code} - {response.text}")
                    return {"error": f"Monday.com API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Error calling Monday.com API: {e}")
            return {"error": str(e)}
    
    def run(self, host: str = "0.0.0.0", port: int = None):
        """Run the A2A agent"""
        if port is None:
            port = self.port
        
        logger.info(f"🚀 Starting Monday Data Agent (A2A) on {host}:{port}")
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

async def demo_monday_data_agent():
    """Demo function to test the Monday Data Agent"""
    print("🧪 Testing Monday Data Agent (A2A Protocol)")
    print("=" * 60)
    
    # Test queries based on actual product catalog
    test_queries = [
        "Show me all SD-WAN products in our catalog",
        "Find products suitable for small businesses under $5000",
        "Generate a quote for a retail chain needing 10 branch offices with SD-WAN",
        "What are the monthly costs for Customer Success services?",
        "Compare SD-WAN Essential vs SD-WAN Enterprise pricing",
        "Recommend a complete networking solution for a medium-sized business"
    ]
    
    client = A2AClient("http://localhost:8005")
    
    for query in test_queries:
        try:
            print(f"\n🔍 Query: {query}")
            response = await client.send_message(query)
            
            # Extract the analysis from the response
            if "result" in response and "response" in response["result"]:
                analysis = response["result"]["response"].get("analysis", "No analysis available")
                print("✅ Analysis:")
                print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
            else:
                print("✅ Response received:")
                print(json.dumps(response, indent=2)[:500] + "...")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        asyncio.run(demo_monday_data_agent())
    else:
        agent = MondayDataAgent()
        agent.run() 