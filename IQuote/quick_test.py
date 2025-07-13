#!/usr/bin/env python3
"""
Quick Test Script for IQuote System
This script performs basic validation of the IQuote system components
"""

import asyncio
import sys
import os
import httpx
from datetime import datetime

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def test_local_data_agent():
    """Test the Local Data Agent (A2A)"""
    print("🧪 Testing Local Data Agent (A2A Protocol)")
    print("-" * 50)
    
    agent_url = "http://localhost:8003"
    
    try:
        # Test agent discovery
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{agent_url}/.well-known/agent.json", timeout=5)
            
            if response.status_code == 200:
                print("✅ Agent discovery successful")
                agent_info = response.json()
                print(f"   Agent: {agent_info.get('name', 'Unknown')}")
                print(f"   Skills: {len(agent_info.get('skills', []))}")
            else:
                print(f"❌ Agent discovery failed: {response.status_code}")
                return False
        
        # Test message sending
        test_message = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "parts": [{"kind": "text", "text": "Test message for networking solution"}],
                    "role": "user"
                }
            },
            "id": f"test_{datetime.now().timestamp()}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(agent_url, json=test_message, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    print("✅ Message processing successful")
                    print(f"   Task ID: {result['result'].get('task_id', 'Unknown')}")
                    print(f"   Status: {result['result'].get('status', 'Unknown')}")
                    return True
                else:
                    print(f"❌ Message processing failed: {result}")
                    return False
            else:
                print(f"❌ Message sending failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing Local Data Agent: {e}")
        return False

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing Module Imports")
    print("-" * 50)
    
    try:
        # Test product catalog import
        from product_catalog import PRODUCTS, USE_CASE_MAPPING
        print(f"✅ Product catalog loaded ({len(PRODUCTS)} products)")
        
        # Test solution architect agent import
        from solution_architect_agent import SolutionRequest, SolutionResponse
        print("✅ Solution architect agent models imported")
        
        # Test adapter import
        from adapter.a2a_to_uagent_adapter import A2AToUAgentAdapter
        print("✅ Adapter imported")
        
        # Test API keys
        from api_keys import Config
        config = Config()
        print("✅ API configuration loaded")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 IQuote System Quick Test")
    print("=" * 60)
    
    # Test 1: Module imports
    imports_ok = test_imports()
    
    if not imports_ok:
        print("\n❌ Import tests failed. Please check dependencies.")
        return
    
    print("\n" + "=" * 60)
    
    # Test 2: Local Data Agent (if running)
    agent_ok = await test_local_data_agent()
    
    if agent_ok:
        print("\n✅ All tests passed! System is ready for demo.")
    else:
        print("\n⚠️  Agent tests failed. Make sure to start the Local Data Agent:")
        print("   python IQuote/local_data_agent.py")
    
    print("\n" + "=" * 60)
    print("🎯 Next Steps:")
    print("1. Start Solution Architect Agent: python IQuote/solution_architect_agent.py")
    print("2. Start Local Data Agent: python IQuote/local_data_agent.py")
    print("3. Run full demo: python IQuote/demo_system.py")

if __name__ == "__main__":
    asyncio.run(main()) 