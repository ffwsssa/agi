import asyncio
import sys
import os
from datetime import datetime, timezone
from uuid import uuid4

from openai import OpenAI
from uagents import Agent, Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    TextContent,
    EndSessionContent,
    chat_protocol_spec,
)
from typing import List, Dict, Optional, Any
import uuid
import logging
import json
import aiohttp
import re

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ASI:One OpenAI Client Setup
try:
    from api_keys import Config
    config = Config()
    asi_config = config.get_asi_one_config()
    
    client = OpenAI(
        base_url=asi_config['base_url'],
        api_key=asi_config['api_key'],
    )
    
    # Subject matter for the solution architect agent
    subject_matter = "network infrastructure solutions, SD-WAN, switching, wireless, security products, and enterprise network architecture"
    
except Exception as e:
    print(f"⚠️ Warning: ASI:One client initialization failed: {e}")
    client = None
    subject_matter = "network infrastructure solutions"

PRODUCTS = [
    # SD-WAN
    {
        "sku": "SDW-1000",
        "name": "CloudConnect SD-WAN S",
        "description": "Entry-level SD-WAN appliance for small branches. Supports up to 200Mbps throughput.",
        "use_cases": ["SD-WAN", "Network Security"],
        "price": 1200,
        "volume_discount": {10: 0.05, 20: 0.1}
    },
    {
        "sku": "SDW-2000",
        "name": "CloudConnect SD-WAN M",
        "description": "Mid-range SD-WAN appliance for medium branches. Supports up to 1Gbps throughput and advanced security features.",
        "use_cases": ["SD-WAN", "Network Security", "Access Security"],
        "price": 3500,
        "volume_discount": {10: 0.07, 20: 0.12}
    },

    # Switching
    {
        "sku": "SW-24-POE",
        "name": "NetSwitch 24-Port PoE+",
        "description": "24-port Gigabit PoE+ switch for access points, cameras, and phones. 480W power budget.",
        "use_cases": ["Switching", "Access Security"],
        "price": 800,
        "volume_discount": {10: 0.05, 50: 0.1}
    },
    {
        "sku": "SW-48",
        "name": "NetSwitch 48-Port L3",
        "description": "48-port Gigabit Layer 3 switch for core branch networking.",
        "use_cases": ["Switching"],
        "price": 1500,
        "volume_discount": {10: 0.05, 20: 0.08}
    },

    # Wireless
    {
        "sku": "AP-W6-PRO",
        "name": "AirWave Wi-Fi 6 Pro AP",
        "description": "High-performance Wi-Fi 6 Access Point for dense environments.",
        "use_cases": ["Wireless"],
        "price": 600,
        "volume_discount": {10: 0.05, 50: 0.1}
    },
    {
        "sku": "AP-W6-LR",
        "name": "AirWave Wi-Fi 6 Long-Range AP",
        "description": "Long-range Wi-Fi 6 Access Point for large open spaces.",
        "use_cases": ["Wireless"],
        "price": 750,
        "volume_discount": {10: 0.05, 50: 0.1}
    },

    # Network Security
    {
        "sku": "SEC-FW-100",
        "name": "SecureWall Firewall 100",
        "description": "Next-gen firewall with threat prevention and VPN capabilities.",
        "use_cases": ["Network Security"],
        "price": 2000,
        "volume_discount": {5: 0.05, 10: 0.1}
    },

    # Access Security
    {
        "sku": "SEC-NAC-500",
        "name": "AccessGuard NAC Appliance",
        "description": "Network Access Control solution for 500 users. Enforces security policies on all connected devices.",
        "use_cases": ["Access Security"],
        "price": 4500,
        "volume_discount": {1: 0, 5: 0.05}
    },
    
    # IOT Security
    {
        "sku": "IOT-SEC-GW",
        "name": "IoT-Secure Gateway",
        "description": "Specialized security gateway for IoT device traffic analysis and threat mitigation.",
        "use_cases": ["Network Security", "IOT Security"],
        "price": 1800,
        "volume_discount": {10: 0.05}
    }
]

USE_CASE_MAPPING = {
    # use case 1: SD-WAN routing + switching
    "sdwan_switching": {
        "name": "SD-WAN and Switching Bundle",
        "skus": ["SDW-2000", "SW-48"],
        "description": "A core bundle for reliable branch connectivity and local network management."
    },
    # use case 2: SD-WAN + wireless
    "sdwan_wireless": {
        "name": "SD-WAN and Wireless Bundle",
        "skus": ["SDW-2000", "AP-W6-PRO"],
        "description": "Provides both wired and high-performance wireless connectivity for modern branches."
    },
    # use case 3: SD-WAN + IOT security services
    "sdwan_iot_security": {
        "name": "SD-WAN and IoT Security Bundle",
        "skus": ["SDW-2000", "IOT-SEC-GW"],
        "description": "Securely connect and manage your IoT devices at the branch level."
    }
} 

# Define uAgent message models
class SolutionRequest(Model):
    """Request model for solution architecture"""
    requirements: str
    branch_count: int = 10
    budget: Optional[float] = None
    request_id: str

class SolutionResponse(Model):
    """Response model for solution architecture"""
    recommended_products: List[Dict]
    total_cost_per_branch: float
    total_cost_all_branches: float
    use_case_bundles: List[Dict]
    request_id: str
    response_timestamp: str

# Create Chat Protocol for ASI:One compatibility following demo pattern
protocol = Protocol(spec=chat_protocol_spec)

# Create Agent with ASI:One compatible configuration
architect_agent = Agent(
    name="solution_architect_agent",
    seed="solution_architect_agent_super_secret_seed",
    port=8002,
    mailbox=True,
    publish_agent_details=True,
)

# Configuration for supporting agents
SUPPORTING_AGENTS = {
    "local_data_agent": {
        "url": "http://localhost:8003",
        "protocol": "A2A",
        "capabilities": ["enhanced_proposals", "langchain_processing"]
    },
    "monday_data_agent": {
        "url": "http://localhost:8005", 
        "protocol": "A2A",
        "capabilities": ["sku_data", "project_data", "monday_integration"]
    }
}

# 简化配置，移除 MCP 服务器

# --- Enhanced Agent Logic ---

async def coordinate_with_local_data_agent(ctx: Context, solution: dict, requirements: str) -> Optional[str]:
    """Coordinate with Local Data Agent for enhanced proposals"""
    try:
        async with aiohttp.ClientSession() as session:
            # 使用正确的 A2A 协议格式
            payload = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": {
                    "message": {
                        "parts": [{"kind": "text", "text": f"Enhance this solution proposal: {json.dumps(solution)} for requirements: {requirements}"}],
                        "role": "user"
                    }
                },
                "id": f"local_query_{uuid.uuid4()}"
            }
            
            # 🔍 Log detailed request
            ctx.logger.info("🔍 LOCAL DATA AGENT REQUEST")
            ctx.logger.info(f"🌐 URL: {SUPPORTING_AGENTS['local_data_agent']['url']}")
            ctx.logger.info(f"📤 Request Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            async with session.post(
                SUPPORTING_AGENTS['local_data_agent']['url'],  # 直接调用根路径
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                ctx.logger.info(f"📥 Response Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    ctx.logger.info(f"📄 Response Data: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    
                    if "result" in result and "response" in result["result"]:
                        response_data = result["result"]["response"]
                        if isinstance(response_data, dict) and "content" in response_data:
                            return response_data["content"]
                        return str(response_data)
                    return str(result)
                else:
                    error_text = await response.text()
                    ctx.logger.warning(f"❌ Local Data Agent error: {response.status} - {error_text}")
                    
    except Exception as e:
        ctx.logger.warning(f"❌ Local Data Agent coordination failed: {e}")
        return None

async def coordinate_with_monday_agent(ctx: Context, requirements: str) -> Optional[Dict]:
    """Coordinate with Monday Data Agent for real-time SKU data"""
    try:
        async with aiohttp.ClientSession() as session:
            # 使用正确的 A2A 协议格式
            payload = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": {
                    "message": {
                        "parts": [{"kind": "text", "text": f"Get latest SKU data for: {requirements}"}],
                        "role": "user"
                    }
                },
                "id": f"monday_query_{uuid.uuid4()}"
            }
            
            # 🔍 Log detailed request
            ctx.logger.info("🔍 MONDAY DATA AGENT REQUEST")
            ctx.logger.info(f"🌐 URL: {SUPPORTING_AGENTS['monday_data_agent']['url']}")
            ctx.logger.info(f"📤 Request Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            async with session.post(
                SUPPORTING_AGENTS['monday_data_agent']['url'],  # 直接调用根路径，不是 /rpc
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                ctx.logger.info(f"📥 Response Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    ctx.logger.info(f"📄 Response Data: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    
                    if "result" in result and "response" in result["result"]:
                        return result["result"]["response"]
                    return result
                else:
                    error_text = await response.text()
                    ctx.logger.warning(f"❌ Monday Data Agent error: {response.status} - {error_text}")
                    
    except Exception as e:
        ctx.logger.warning(f"❌ Monday Data Agent coordination failed: {e}")
        return None

# 移除了 MCP 服务器协调功能

def find_products_for_requirements(requirements_text: str) -> dict:
    """
    Enhanced product matching with better natural language processing
    """
    found_products = []
    mentioned_use_cases = set()
    
    # Enhanced keyword matching for product categories
    requirements_lower = requirements_text.lower()
    
    # SD-WAN detection
    if any(keyword in requirements_lower for keyword in ["sd-wan", "sdwan", "software defined wan", "分支连接", "广域网"]):
        mentioned_use_cases.add("SD-WAN")
    
    # Switching detection
    if any(keyword in requirements_lower for keyword in ["switching", "switch", "交换机", "局域网", "lan"]):
        mentioned_use_cases.add("Switching")
    
    # Wireless detection
    if any(keyword in requirements_lower for keyword in ["wireless", "wi-fi", "wifi", "无线", "wifi覆盖"]):
        mentioned_use_cases.add("Wireless")
    
    # Security detection
    if any(keyword in requirements_lower for keyword in ["security", "firewall", "防火墙", "网络安全", "安全"]):
        mentioned_use_cases.add("Network Security")
    
    # Access control detection
    if any(keyword in requirements_lower for keyword in ["access control", "nac", "访问控制", "准入控制"]):
        mentioned_use_cases.add("Access Security")
    
    # IoT detection
    if any(keyword in requirements_lower for keyword in ["iot", "internet of things", "物联网", "iot安全"]):
        mentioned_use_cases.add("IOT Security")

    # Find all products that match the identified use cases
    for product in PRODUCTS:
        if any(use_case in product["use_cases"] for use_case in mentioned_use_cases):
            found_products.append(product)
            
    return {
        "products": found_products,
        "mentioned_use_cases": list(mentioned_use_cases)
    }

def extract_branch_count(text: str) -> int:
    """Extract branch count from natural language text"""
    # Multiple patterns for branch count extraction
    patterns = [
        r'(\d+)\s*(?:个|)(?:分支|分公司|办事处|网点|分店|门店)',
        r'(\d+)\s*(?:branches?|offices?|sites?|locations?)',
        r'for\s+(\d+)\s+(?:branches?|offices?|sites?)',
        r'(\d+)\s*branch'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return 10  # Default value

def extract_budget(text: str) -> Optional[float]:
    """Extract budget from natural language text"""
    # Budget patterns
    patterns = [
        r'(?:预算|budget|cost).*?(\d+(?:\.\d+)?)\s*(?:万|k|thousand)',
        r'(?:预算|budget|cost).*?(\d+(?:\.\d+)?)\s*(?:万元|万人民币)',
        r'budget\s*(?:of|is|:)?\s*\$?(\d+(?:,\d+)*(?:\.\d+)?)',
        r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:dollar|usd|rmb|yuan)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = float(match.group(1).replace(',', ''))
            # Convert 万 to actual amount
            if '万' in text or 'k' in text.lower() or 'thousand' in text.lower():
                amount *= 10000
            return amount
    
    return None

def generate_use_case_bundles(mentioned_use_cases: List[str]) -> List[Dict]:
    """Generate relevant use case bundles based on mentioned use cases"""
    relevant_bundles = []
    
    for bundle_key, bundle_info in USE_CASE_MAPPING.items():
        # Check if this bundle is relevant to the mentioned use cases
        if any(use_case in bundle_info["description"] for use_case in mentioned_use_cases):
            relevant_bundles.append({
                "bundle_id": bundle_key,
                "name": bundle_info["name"],
                "description": bundle_info["description"],
                "skus": bundle_info["skus"]
            })
    
    return relevant_bundles

def format_chat_response(solution: dict, branch_count: int = 10, budget: Optional[float] = None) -> str:
    """Format solution for chat response with enhanced formatting"""
    if not solution["products"]:
        return """🔍 **分析结果**        
    我没有找到完全匹配您需求的产品。为了提供最佳解决方案，请提供更多信息：

    📋 **需要的信息**
    • 具体网络需求（SD-WAN、交换机、无线、安全等）
    • 分支机构数量和规模
    • 预算范围
    • 现有网络环境
    • 业务优先级

    💡 **示例需求**
    "我需要为20个分支建立SD-WAN网络，包含安全和无线功能，预算100万"

    🤖 **智能助手**
    我会使用 Gemini 2.5-flash 为您分析需求并推荐最适合的网络解决方案！"""
    
    response = f"🏗️ **智能网络解决方案**\n\n"
    response += f"📊 **项目分析**\n"
    response += f"• 分支数量: {branch_count}\n"
    response += f"• 解决方案: {', '.join(solution['mentioned_use_cases'])}\n"
    if budget:
        response += f"• 预算约束: ¥{budget:,.2f}\n"
    response += f"\n"
    
    response += f"💡 **推荐产品组合**\n"
    total_cost_per_branch = 0
    for i, product in enumerate(solution["products"], 1):
        price = product['price']
        total_cost_per_branch += price
        response += f"{i}. **{product['name']}** `{product['sku']}`\n"
        response += f"   💰 单价: ¥{price:,.2f}\n"
        response += f"   🎯 应用: {', '.join(product['use_cases'])}\n"
        response += f"   📝 描述: {product.get('description', 'Professional networking solution')}\n\n"
    
    response += f"📈 **成本分析**\n"
    response += f"• 单分支成本: ¥{total_cost_per_branch:,.2f}\n"
    response += f"• 总项目成本: ¥{total_cost_per_branch * branch_count:,.2f}\n"
    
    if budget:
        if total_cost_per_branch * branch_count <= budget:
            response += f"• ✅ 在预算范围内\n"
        else:
            response += f"• ⚠️ 超出预算 ¥{(total_cost_per_branch * branch_count) - budget:,.2f}\n"
    
    response += f"\n"
    
    # Add bundle suggestions
    if len(solution["mentioned_use_cases"]) > 1:
        response += f"🎁 **组合优化建议**\n"
        response += f"基于您的多功能需求，建议选择集成解决方案获得更好的:\n"
        response += f"• 💰 性价比优势\n• 🔧 统一管理\n• 🚀 部署效率\n• 🛡️ 安全一致性\n\n"
    
    response += f"🤖 **AI 增强分析**\n"
    response += f"本方案由 Gemini 2.5-flash 智能分析生成，如需详细技术规格或定制化配置，请继续对话！\n\n"
    
    response += f"📞 **下一步**\n"
    response += f"💬 继续对话获取详细实施方案\n"
    response += f"🔗 可协调 Local Data Agent 生成客户提案\n"
    response += f"📊 可连接 Monday.com 获取实时 SKU 数据"
    
    return response

# --- Gemini 2.5-flash Integration ---
from google.generativeai import GenerativeModel
import google.generativeai as genai

def get_gemini_client():
    """Initialize Gemini client with error handling"""
    try:
        from api_keys import Config
        config = Config()
        gemini_config = config.get_gemini_config()
        genai.configure(api_key=gemini_config['api_key'])
        return GenerativeModel('gemini-2.0-flash-exp')
    except Exception as e:
        logging.warning(f"Gemini initialization failed: {e}")
        return None

async def generate_enhanced_solution(requirements: str, solution: dict, branch_count: int, budget: Optional[float] = None) -> str:
    """Generate enhanced solution using Gemini 2.5-flash"""
    gemini_client = get_gemini_client()
    
    if not gemini_client or not solution["products"]:
        return format_chat_response(solution, branch_count, budget)
    
    try:
        # Build detailed context for Gemini
        products_info = "\n".join([
            f"- {p['name']} ({p['sku']}): ¥{p['price']:,}/unit - {', '.join(p['use_cases'])}"
            for p in solution["products"]
        ])
        
        total_cost = sum(p['price'] for p in solution['products']) * branch_count
        
        gemini_prompt = f"""
作为资深网络解决方案架构师，基于以下信息为客户生成专业、详细的网络解决方案建议：

**客户需求分析**
原始需求: {requirements}
分支数量: {branch_count}
预算限制: {"¥{:,}".format(budget) if budget else "未指定"}

**推荐产品组合**
{products_info}

**成本分析**
• 单分支成本: ¥{sum(p['price'] for p in solution['products']):,}
• 总项目成本: ¥{total_cost:,}
• 预算状态: {"在预算内" if budget and total_cost <= budget else "需要优化" if budget else "待确认"}

**技术背景**
用例类型: {', '.join(solution['mentioned_use_cases'])}

请生成一个专业的网络解决方案建议，包括：

1. **方案概述** - 简洁描述整体解决方案
2. **产品价值** - 每个产品的核心价值和业务贡献
3. **架构优势** - 技术架构的优势和集成效果
4. **成本效益** - 投资回报和长期价值
5. **实施路径** - 部署建议和时间规划
6. **风险管控** - 潜在风险和缓解措施

保持专业性和客户导向，重点突出业务价值和技术优势。使用清晰的结构和适当的 emoji 增强可读性。
"""
        
        response = gemini_client.generate_content(gemini_prompt)
        return response.text
        
    except Exception as e:
        logging.error(f"Gemini enhanced solution generation failed: {e}")
        return format_chat_response(solution, branch_count, budget)

# --- Chat Protocol Handlers for ASI:One ---

@protocol.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle chat messages following ASI:One demo pattern"""
    
    # 📩 Log incoming message details
    ctx.logger.info("=" * 80)
    ctx.logger.info(f"📩 INCOMING CHAT MESSAGE")
    ctx.logger.info(f"👤 From: {sender}")
    ctx.logger.info(f"🆔 Message ID: {msg.msg_id}")
    ctx.logger.info(f"🕐 Timestamp: {msg.timestamp}")
    
    # Send acknowledgment immediately
    ack_msg = ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id)
    await ctx.send(sender, ack_msg)
    ctx.logger.info(f"✅ Acknowledgment sent to {sender}")
    
    # Collect up all the text chunks
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text
    
    ctx.logger.info(f"📝 Message Content: {text}")
    ctx.logger.info("-" * 80)
    
    # Default response if client is not available
    response = 'I am afraid something went wrong and I am unable to answer your question at the moment'
    
    if client and text:
        try:
            # 🤖 Log ASI:One API call details
            ctx.logger.info("🤖 CALLING ASI:One API")
            ctx.logger.info(f"🔗 Model: asi1-mini")
            ctx.logger.info(f"📤 User Query: {text}")
            
            # Query the ASI:One model with solution architect expertise
            r = client.chat.completions.create(
                model="asi1-mini",
                messages=[
                    {"role": "system", "content": f"""
You are an expert solution architect who specializes in {subject_matter}. 

You have access to the following product catalog:
{json.dumps(PRODUCTS, ensure_ascii=False, indent=2)}

You can recommend products based on customer requirements, calculate costs, suggest optimal configurations, 
and provide detailed technical specifications. You understand network infrastructure needs, security requirements, 
and can design comprehensive solutions for enterprises.

If the user asks about topics outside of {subject_matter}, politely explain that you are specialized 
in network infrastructure solutions and redirect the conversation to how you can help with their 
networking needs.

Always provide detailed, professional responses with cost calculations and technical reasoning.
                    """},
                    {"role": "user", "content": text},
                ],
                max_tokens=2048,
            )
            
            response = str(r.choices[0].message.content)
            
            # 📥 Log ASI:One API response
            ctx.logger.info("📥 ASI:One API RESPONSE")
            ctx.logger.info(f"📝 Response Length: {len(response)} characters")
            ctx.logger.info(f"💡 Response Preview: {response[:200]}...")
            
            # 🔗 Try to coordinate with other agents
            ctx.logger.info("🔗 COORDINATING WITH OTHER AGENTS")
            
            # Extract parameters for coordination
            solution = find_products_for_requirements(text)
            ctx.logger.info(f"📊 Found {len(solution['products'])} products in local catalog")
            
            # Coordinate with Local Data Agent
            ctx.logger.info("🔄 Attempting coordination with Local Data Agent...")
            enhanced_proposal = await coordinate_with_local_data_agent(ctx, solution, text)
            if enhanced_proposal:
                ctx.logger.info("✅ Local Data Agent coordination successful")
                ctx.logger.info(f"📄 Enhanced proposal length: {len(enhanced_proposal)} characters")
                response += f"\n\n🔗 **Local Data Agent Enhancement:**\n{enhanced_proposal}"
            else:
                ctx.logger.info("❌ Local Data Agent coordination failed")
            
            # Coordinate with Monday Data Agent
            ctx.logger.info("🔄 Attempting coordination with Monday Data Agent...")
            monday_data = await coordinate_with_monday_agent(ctx, text)
            if monday_data:
                ctx.logger.info("✅ Monday Data Agent coordination successful")
                ctx.logger.info(f"📊 Monday data: {json.dumps(monday_data, ensure_ascii=False)[:200]}...")
                response += f"\n\n📊 **Monday.com Real-time Data:**\n{json.dumps(monday_data, ensure_ascii=False, indent=2)}"
            else:
                ctx.logger.info("❌ Monday Data Agent coordination failed")
            
        except Exception as e:
            ctx.logger.error(f'Error querying ASI:One model: {e}')
            # Fallback to local processing
            solution = find_products_for_requirements(text)
            branch_count = extract_branch_count(text)
            budget = extract_budget(text)
            response = format_chat_response(solution, branch_count, budget)
    
    # Send response with EndSessionContent following demo pattern
    response_msg = ChatMessage(
        timestamp=datetime.now(),
        msg_id=uuid4(),
        content=[
            TextContent(type="text", text=response),
            EndSessionContent(type="end-session"),
        ]
    )
    
    # 📤 Log outgoing response details
    ctx.logger.info("📤 OUTGOING CHAT RESPONSE")
    ctx.logger.info(f"👤 To: {sender}")
    ctx.logger.info(f"🆔 Response ID: {response_msg.msg_id}")
    ctx.logger.info(f"📝 Response Length: {len(response)} characters")
    ctx.logger.info(f"💡 Response Preview: {response[:300]}...")
    ctx.logger.info(f"🔚 Session Ended: True")
    ctx.logger.info("=" * 80)
    
    await ctx.send(sender, response_msg)

@protocol.on_message(ChatAcknowledgement)
async def handle_chat_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle chat acknowledgments"""
    ctx.logger.info("=" * 80)
    ctx.logger.info(f"✅ CHAT ACKNOWLEDGMENT RECEIVED")
    ctx.logger.info(f"👤 From: {sender}")
    ctx.logger.info(f"🆔 Acknowledged Message ID: {msg.acknowledged_msg_id}")
    ctx.logger.info(f"🕐 Timestamp: {msg.timestamp}")
    ctx.logger.info("=" * 80)

# 移除了 FastAPI 相关代码，只保留 mailbox 功能

# --- Agent Event Handlers ---

@architect_agent.on_event("startup")
async def startup(ctx: Context):
    """Agent startup event handler"""
    ctx.logger.setLevel(logging.INFO)
    
    ctx.logger.info("🏗️ Solution Architect Agent (IQuote) started")
    ctx.logger.info(f"📍 Agent Address: {architect_agent.address}")
    ctx.logger.info("✅ Chat Protocol registered for ASI:One compatibility")
    ctx.logger.info("🤖 ASI:One integration ready")
    ctx.logger.info("🔗 Agent coordination enabled")
    ctx.logger.info("📪 Mailbox mode enabled")
    ctx.logger.info("🚀 Ready for ASI:One integration and natural language interaction")

@architect_agent.on_message(model=SolutionRequest, replies=SolutionResponse)
async def handle_solution_request(ctx: Context, sender: str, msg: SolutionRequest):
    """Handle solution requests from other agents"""
    
    # 📥 Log uAgent request details
    ctx.logger.info("=" * 80)
    ctx.logger.info(f"📥 uAGENT SOLUTION REQUEST")
    ctx.logger.info(f"👤 From: {sender}")
    ctx.logger.info(f"🆔 Request ID: {msg.request_id}")
    ctx.logger.info(f"📝 Requirements: {msg.requirements}")
    ctx.logger.info(f"🏢 Branch count: {msg.branch_count}")
    ctx.logger.info(f"💰 Budget: {msg.budget}")
    ctx.logger.info("-" * 80)
    
    # Find products based on requirements
    solution = find_products_for_requirements(msg.requirements)
    ctx.logger.info(f"🔍 Product matching results:")
    ctx.logger.info(f"   📦 Found {len(solution['products'])} products")
    ctx.logger.info(f"   🎯 Use cases: {solution['mentioned_use_cases']}")
    
    # Calculate costs
    total_cost_per_branch = sum(product['price'] for product in solution["products"])
    total_cost_all_branches = total_cost_per_branch * msg.branch_count
    
    ctx.logger.info(f"💵 Cost calculation:")
    ctx.logger.info(f"   💰 Per branch: ¥{total_cost_per_branch:,.2f}")
    ctx.logger.info(f"   💰 Total ({msg.branch_count} branches): ¥{total_cost_all_branches:,.2f}")
    
    # Generate use case bundles
    use_case_bundles = generate_use_case_bundles(solution["mentioned_use_cases"])
    ctx.logger.info(f"📦 Generated {len(use_case_bundles)} use case bundles")
    
    # Create response
    response = SolutionResponse(
        recommended_products=solution["products"],
        total_cost_per_branch=total_cost_per_branch,
        total_cost_all_branches=total_cost_all_branches,
        use_case_bundles=use_case_bundles,
        request_id=msg.request_id,
        response_timestamp=datetime.now().isoformat()
    )
    
    # 📤 Log uAgent response details
    ctx.logger.info("📤 uAGENT SOLUTION RESPONSE")
    ctx.logger.info(f"👤 To: {sender}")
    ctx.logger.info(f"🆔 Request ID: {msg.request_id}")
    ctx.logger.info(f"📦 Products: {len(solution['products'])}")
    ctx.logger.info(f"💰 Total cost: ¥{total_cost_all_branches:,.2f}")
    ctx.logger.info(f"🕐 Response time: {response.response_timestamp}")
    ctx.logger.info("=" * 80)
    
    await ctx.send(sender, response)

# Attach the protocol to the agent following demo pattern
architect_agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    # 创建带时间戳的日志文件
    import time
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = f"agent_logs_{timestamp}.txt"
    
    # 配置日志系统，同时输出到文件和控制台
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    print("🚀 Starting Solution Architect Agent (IQuote) - ASI:One Integration")
    print("=" * 60)
    print("🏗️ Agent Name: Solution Architect Agent")
    print("🏷️ ASI:One Alias: IQuote")
    print("🧠 AI Model: ASI:One (asi1-mini)")
    print("📪 Communication: Mailbox + Port 8002")
    print("🔗 Supporting Agents: Local Data Agent, Monday Data Agent")
    print("🎯 Subject Matter: Network Infrastructure Solutions")
    print(f"📝 Log File: {log_file}")
    print("=" * 60)
    print("✅ Ready for ASI:One discovery and natural language interaction")
    
    # Start uAgent (this will block the main thread)
    architect_agent.run() 