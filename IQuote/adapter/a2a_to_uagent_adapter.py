#!/usr/bin/env python3
"""
A2A to uAgent Adapter for IQuote System
This adapter bridges the A2A protocol Local Data Agent with the uAgent Solution Architect Agent
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
import uuid

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from uagents import Agent, Context, Model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Message models for communication with Solution Architect Agent
class SolutionRequest(Model):
    """Request model for solution architecture"""
    requirements: str
    branch_count: int = 10
    budget: Optional[float] = None
    request_id: str

class SolutionResponse(Model):
    """Response model for solution architecture"""
    recommended_products: list
    total_cost_per_branch: float
    total_cost_all_branches: float
    use_case_bundles: list
    request_id: str
    response_timestamp: str

class A2AToUAgentAdapter:
    """
    Adapter that bridges A2A protocol messages to uAgent protocol
    """
    
    def __init__(self, solution_architect_address: str, port: int = 8004):
        self.solution_architect_address = solution_architect_address
        self.port = port
        
        # Create the adapter agent
        self.adapter_agent = Agent(
            name="a2a_to_uagent_adapter",
            port=port,
            seed="a2a_to_uagent_adapter_secret_seed",
            endpoint=[f"http://localhost:{port}/submit"]
        )
        
        # Store pending requests
        self.pending_requests = {}
        
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup message handlers for the adapter"""
        
        @self.adapter_agent.on_event("startup")
        async def startup_handler(ctx: Context):
            """Handle adapter startup"""
            ctx.logger.info("🔗 A2A to uAgent Adapter started")
            ctx.logger.info(f"Adapter address: {self.adapter_agent.address}")
            ctx.logger.info(f"Connected to Solution Architect: {self.solution_architect_address}")
        
        @self.adapter_agent.on_message(model=SolutionResponse)
        async def handle_solution_response(ctx: Context, sender: str, msg: SolutionResponse):
            """Handle response from Solution Architect Agent"""
            ctx.logger.info(f"📥 Received solution response for request: {msg.request_id}")
            
            # Store the response for the pending request
            if msg.request_id in self.pending_requests:
                self.pending_requests[msg.request_id]["response"] = msg
                self.pending_requests[msg.request_id]["status"] = "completed"
                ctx.logger.info(f"✅ Response stored for request: {msg.request_id}")
    
    async def process_a2a_request(self, a2a_message: str) -> Dict[str, Any]:
        """
        Process an A2A message and get response from uAgent
        """
        request_id = str(uuid.uuid4())
        
        # Parse the A2A message to extract requirements
        requirements = a2a_message
        branch_count = 10  # Default, could be parsed from message
        
        # Create uAgent request
        solution_request = SolutionRequest(
            requirements=requirements,
            branch_count=branch_count,
            request_id=request_id
        )
        
        # Store pending request
        self.pending_requests[request_id] = {
            "status": "pending",
            "request": solution_request,
            "response": None,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send request to Solution Architect Agent
        logger.info(f"📤 Sending request to Solution Architect: {request_id}")
        
        # Create a context for sending the message
        # Note: In a real implementation, this would be handled differently
        # For demo purposes, we'll simulate the response
        
        # Simulate sending to uAgent and getting response
        await self.simulate_uagent_interaction(solution_request)
        
        # Wait for response (with timeout)
        max_wait = 30  # seconds
        wait_time = 0
        while wait_time < max_wait:
            if (request_id in self.pending_requests and 
                self.pending_requests[request_id]["status"] == "completed"):
                
                response = self.pending_requests[request_id]["response"]
                
                # Convert uAgent response to A2A format
                a2a_response = self.convert_uagent_to_a2a_response(response)
                
                # Clean up
                del self.pending_requests[request_id]
                
                return a2a_response
            
            await asyncio.sleep(0.1)
            wait_time += 0.1
        
        # Timeout
        logger.error(f"⏰ Timeout waiting for response to request: {request_id}")
        return {
            "error": "Timeout waiting for solution architect response",
            "request_id": request_id
        }
    
    async def simulate_uagent_interaction(self, request: SolutionRequest):
        """
        Simulate interaction with uAgent Solution Architect
        In real implementation, this would use the actual uAgent messaging
        """
        logger.info(f"🔄 Simulating uAgent interaction for request: {request.request_id}")
        
        # Simulate processing delay
        await asyncio.sleep(1)
        
        # Create mock response based on the request
        mock_products = [
            {
                "sku": "SDW-2000",
                "name": "CloudConnect SD-WAN M",
                "price": 3500,
                "use_cases": ["SD-WAN", "Network Security", "Access Security"]
            },
            {
                "sku": "SW-48",
                "name": "NetSwitch 48-Port L3",
                "price": 1500,
                "use_cases": ["Switching"]
            },
            {
                "sku": "AP-W6-PRO",
                "name": "AirWave Wi-Fi 6 Pro AP",
                "price": 600,
                "use_cases": ["Wireless"]
            },
            {
                "sku": "SEC-FW-100",
                "name": "SecureWall Firewall 100",
                "price": 2000,
                "use_cases": ["Network Security"]
            }
        ]
        
        total_cost_per_branch = sum(p["price"] for p in mock_products)
        total_cost_all_branches = total_cost_per_branch * request.branch_count
        
        mock_response = SolutionResponse(
            recommended_products=mock_products,
            total_cost_per_branch=total_cost_per_branch,
            total_cost_all_branches=total_cost_all_branches,
            use_case_bundles=[
                {
                    "bundle_id": "sdwan_switching",
                    "name": "SD-WAN and Switching Bundle",
                    "description": "A core bundle for reliable branch connectivity"
                }
            ],
            request_id=request.request_id,
            response_timestamp=datetime.now().isoformat()
        )
        
        # Store the response
        self.pending_requests[request.request_id]["response"] = mock_response
        self.pending_requests[request.request_id]["status"] = "completed"
        
        logger.info(f"✅ Mock response generated for request: {request.request_id}")
    
    def convert_uagent_to_a2a_response(self, uagent_response: SolutionResponse) -> Dict[str, Any]:
        """
        Convert uAgent response to A2A format
        """
        # Format the response as a readable solution text
        solution_text = f"""
Based on your requirements for {uagent_response.recommended_products and len(uagent_response.recommended_products) or 0} products, here is a proposed solution:

Recommended Products:
"""
        
        for product in uagent_response.recommended_products:
            solution_text += f"- {product['name']} ({product['sku']}): ${product['price']:,.2f}/unit\n"
            solution_text += f"  - Use cases: {', '.join(product['use_cases'])}\n"
        
        solution_text += f"""
Estimated Cost per Branch: ${uagent_response.total_cost_per_branch:,.2f}
Estimated Total for All Branches: ${uagent_response.total_cost_all_branches:,.2f}

Use Case Bundles:
"""
        
        for bundle in uagent_response.use_case_bundles:
            solution_text += f"- {bundle['name']}: {bundle['description']}\n"
        
        solution_text += "\nThis is a preliminary recommendation. We can refine this based on more specific details about your business needs and budget."
        
        return {
            "proposal_type": "technical_solution",
            "content": solution_text,
            "raw_data": {
                "recommended_products": uagent_response.recommended_products,
                "total_cost_per_branch": uagent_response.total_cost_per_branch,
                "total_cost_all_branches": uagent_response.total_cost_all_branches,
                "use_case_bundles": uagent_response.use_case_bundles
            },
            "request_id": uagent_response.request_id,
            "timestamp": uagent_response.response_timestamp
        }
    
    async def run(self):
        """Run the adapter"""
        logger.info("🚀 Starting A2A to uAgent Adapter")
        await self.adapter_agent.run()

# HTTP Client for A2A interaction
class A2AAdapterClient:
    """
    Client to interact with the A2A to uAgent adapter
    """
    
    def __init__(self, adapter_port: int = 8004):
        self.adapter_port = adapter_port
        self.adapter = None
    
    async def start_adapter(self, solution_architect_address: str):
        """Start the adapter"""
        self.adapter = A2AToUAgentAdapter(solution_architect_address, self.adapter_port)
        # In a real implementation, this would start the adapter in a separate process
        logger.info(f"🔗 Adapter client initialized for port {self.adapter_port}")
    
    async def send_a2a_message(self, message: str) -> Dict[str, Any]:
        """Send an A2A message through the adapter"""
        if not self.adapter:
            raise RuntimeError("Adapter not started")
        
        logger.info(f"📨 Processing A2A message through adapter: {message[:100]}...")
        response = await self.adapter.process_a2a_request(message)
        return response

# Demo function
async def demo_adapter():
    """Demo the A2A to uAgent adapter"""
    print("🧪 Testing A2A to uAgent Adapter")
    print("=" * 60)
    
    # Mock solution architect address
    solution_architect_address = "agent1qw2e3r4t5y6u7i8o9p0a1s2d3f4g5h6j7k8l9m0n1b2v3c4x5z6"
    
    # Create adapter client
    client = A2AAdapterClient()
    await client.start_adapter(solution_architect_address)
    
    # Test message
    test_message = "I am a solution architect at a retail store, I want to purchase networking solutions to set up 10 new branches to expand my business. The solution should include SD-WAN, switching, wireless, network security, and access security features."
    
    try:
        response = await client.send_a2a_message(test_message)
        print("✅ Adapter response received:")
        print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        asyncio.run(demo_adapter())
    else:
        # Run the adapter
        adapter = A2AToUAgentAdapter("agent1qw2e3r4t5y6u7i8o9p0a1s2d3f4g5h6j7k8l9m0n1b2v3c4x5z6")
        asyncio.run(adapter.run()) 