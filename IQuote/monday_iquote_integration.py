#!/usr/bin/env python3
"""
Monday.com IQuote Integration Example
This example shows how to integrate Monday Data Agent with IQuote system
to generate intelligent quotes based on Monday.com product catalog.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any, List

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api_keys import Config
import httpx

class MondayIQuoteIntegration:
    """Integration between Monday.com Data Agent and IQuote system"""
    
    def __init__(self):
        self.monday_agent_url = "http://localhost:8005"
        self.local_agent_url = "http://localhost:8003"
        self.config = Config()
    
    async def process_customer_request(self, customer_request: str) -> Dict[str, Any]:
        """Process customer request using Monday.com data and IQuote system"""
        print(f"🎯 Processing customer request: {customer_request}")
        
        # Step 1: Get product recommendations from Monday Data Agent
        print("\n1️⃣ Querying Monday.com product catalog...")
        monday_response = await self.query_monday_agent(customer_request)
        
        # Step 2: Generate customer-friendly proposal using Local Data Agent
        print("\n2️⃣ Generating customer-friendly proposal...")
        if monday_response and "analysis" in monday_response:
            proposal_response = await self.generate_customer_proposal(
                customer_request, monday_response["analysis"]
            )
        else:
            proposal_response = await self.generate_customer_proposal(customer_request, "")
        
        # Step 3: Combine responses for final output
        print("\n3️⃣ Combining responses...")
        return self.combine_responses(customer_request, monday_response, proposal_response)
    
    async def query_monday_agent(self, query: str) -> Dict[str, Any]:
        """Query Monday Data Agent for product information"""
        try:
            message = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": {
                    "message": {
                        "parts": [{"kind": "text", "text": query}],
                        "role": "user"
                    }
                },
                "id": "monday_query"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.monday_agent_url, 
                    json=message, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "result" in result and "response" in result["result"]:
                        return result["result"]["response"]
                    else:
                        return {"error": "Invalid response format"}
                else:
                    return {"error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"error": str(e)}
    
    async def generate_customer_proposal(self, original_request: str, monday_analysis: str) -> Dict[str, Any]:
        """Generate customer-friendly proposal using Local Data Agent"""
        # Combine original request with Monday analysis
        enhanced_request = f"""
        Original Customer Request: {original_request}
        
        Monday.com Product Analysis: {monday_analysis}
        
        Please generate a comprehensive customer-friendly proposal that combines both the technical solution and the specific products from our Monday.com catalog. Include pricing details, implementation timeline, and next steps.
        """
        
        try:
            message = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": {
                    "message": {
                        "parts": [{"kind": "text", "text": enhanced_request}],
                        "role": "user"
                    }
                },
                "id": "proposal_query"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.local_agent_url, 
                    json=message, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "result" in result and "response" in result["result"]:
                        return result["result"]["response"]
                    else:
                        return {"error": "Invalid response format"}
                else:
                    return {"error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"error": str(e)}
    
    def combine_responses(self, request: str, monday_response: Dict[str, Any], proposal_response: Dict[str, Any]) -> Dict[str, Any]:
        """Combine Monday.com data and IQuote proposal into final response"""
        return {
            "customer_request": request,
            "monday_analysis": monday_response,
            "customer_proposal": proposal_response,
            "integration_status": "completed",
            "timestamp": "2025-01-13T12:00:00Z"
        }

async def demo_integration():
    """Demo the Monday.com IQuote integration"""
    print("🚀 Monday.com IQuote Integration Demo")
    print("=" * 60)
    
    integration = MondayIQuoteIntegration()
    
    # Test scenarios based on your actual product catalog
    scenarios = [
        {
            "name": "Small Business SD-WAN",
            "request": "I need a complete SD-WAN solution for a small retail business with 3 locations. Budget is around $10,000 for setup and willing to pay up to $500/month for ongoing services."
        },
        {
            "name": "Enterprise Networking",
            "request": "Large enterprise customer needs SD-WAN for 50 branch offices with premium support. They want the best available solutions with 24/7 support."
        },
        {
            "name": "Budget-Conscious Quote",
            "request": "Medium-sized business looking for cost-effective networking solution. Need SD-WAN for 10 locations but want to minimize monthly costs."
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print(f"📝 Request: {scenario['request']}")
        print("-" * 50)
        
        try:
            result = await integration.process_customer_request(scenario['request'])
            
            # Display Monday.com analysis
            if "monday_analysis" in result and "analysis" in result["monday_analysis"]:
                print(f"🔍 Monday.com Analysis:")
                analysis = result["monday_analysis"]["analysis"]
                print(analysis[:300] + "..." if len(analysis) > 300 else analysis)
            
            # Display customer proposal
            if "customer_proposal" in result and "content" in result["customer_proposal"]:
                print(f"\n💼 Customer Proposal:")
                proposal = result["customer_proposal"]["content"]
                print(proposal[:400] + "..." if len(proposal) > 400 else proposal)
            
            print("\n" + "=" * 60)
            
        except Exception as e:
            print(f"❌ Error processing scenario: {e}")

async def quick_test():
    """Quick test to verify both agents are running"""
    print("🔍 Quick Integration Test")
    print("=" * 30)
    
    integration = MondayIQuoteIntegration()
    
    # Test Monday Data Agent
    print("Testing Monday Data Agent...")
    monday_result = await integration.query_monday_agent("Show me all SD-WAN products")
    
    if "error" in monday_result:
        print(f"❌ Monday Agent Error: {monday_result['error']}")
        print("💡 Make sure Monday Data Agent is running on port 8005")
        print("   Command: python IQuote/monday_data_agent.py")
    else:
        print("✅ Monday Data Agent is working")
    
    # Test Local Data Agent
    print("\nTesting Local Data Agent...")
    local_result = await integration.generate_customer_proposal("Test request", "Test analysis")
    
    if "error" in local_result:
        print(f"❌ Local Agent Error: {local_result['error']}")
        print("💡 Make sure Local Data Agent is running on port 8003")
        print("   Command: python IQuote/local_data_agent.py")
    else:
        print("✅ Local Data Agent is working")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        asyncio.run(quick_test())
    else:
        asyncio.run(demo_integration()) 