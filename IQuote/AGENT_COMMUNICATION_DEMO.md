# 🤖 Agent Communication Demo

展示Agent之间详细通信过程的演示系统

## 📋 概述

此演示系统展示了以下Agent通信模式：

1. **ASI:One → Solution Architect Agent** (Chat Protocol)
2. **Solution Architect Agent → ASI:One API** (HTTPS调用)
3. **Solution Architect Agent → Local Data Agent** (A2A Protocol)
4. **Solution Architect Agent → Monday Data Agent** (A2A Protocol)
5. **Agent → Agent** (uAgent Protocol)

## 🚀 启动步骤

### 1. 启动Solution Architect Agent
```bash
cd IQuote
python solution_architect_agent.py
```

### 2. 启动支持的Agent（可选）
```bash
# 另一个终端启动Local Data Agent
python local_data_agent.py

# 另一个终端启动Monday Data Agent  
python monday_data_agent.py
```

### 3. 运行通信演示
```bash
python demo_agent_communication.py
```

## 📊 日志内容详解

### 📩 接收消息日志
```
================================================================================
📩 INCOMING CHAT MESSAGE
👤 From: agent1q0fqhwsas60vn9v2x2caq3jqjll7xse7er3kgnjzsq7206ey4ujgxq66ltg
🆔 Message ID: 12345678-1234-1234-1234-123456789012
🕐 Timestamp: 2024-01-15 10:30:00
📝 Message Content: I need SD-WAN solutions for 10 branch offices
```

### 🤖 ASI:One API调用日志
```
🤖 CALLING ASI:One API
🔗 Model: asi1-mini
📤 User Query: I need SD-WAN solutions for 10 branch offices
📥 ASI:One API RESPONSE
📝 Response Length: 1500 characters
💡 Response Preview: Based on your requirements for 10 branch offices...
```

### 🔗 Agent协调日志
```
🔗 COORDINATING WITH OTHER AGENTS
🔄 Attempting coordination with Local Data Agent...
🔍 LOCAL DATA AGENT REQUEST
🌐 URL: http://localhost:8003
📤 Request Payload:
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "parts": [{"kind": "text", "text": "Enhance this solution..."}],
      "role": "user"
    }
  },
  "id": "local_query_abcd-1234"
}
📥 Response Status: 200
📄 Response Data: {...}
```

### 📤 发送响应日志
```
📤 OUTGOING CHAT RESPONSE
👤 To: agent1q0fqhwsas60vn9v2x2caq3jqjll7xse7er3kgnjzsq7206ey4ujgxq66ltg
🆔 Response ID: 87654321-4321-4321-4321-210987654321
📝 Response Length: 2000 characters
💡 Response Preview: Based on your requirements for 10 branch offices, I recommend...
🔚 Session Ended: True
```

## 🎯 通信协议说明

### 1. Chat Protocol (ASI:One)
- **用途**: ASI:One平台与Agent通信
- **传输**: AgentVerse Mailbox
- **格式**: ChatMessage + ChatAcknowledgement

### 2. A2A Protocol (Agent-to-Agent)
- **用途**: 本地Agent之间通信
- **传输**: HTTP POST (JSON-RPC 2.0)
- **端口**: 8002, 8003, 8005

### 3. uAgent Protocol
- **用途**: uAgent框架内部通信
- **传输**: 直接消息传递
- **格式**: SolutionRequest + SolutionResponse

## 📈 演示场景

### 场景1: 简单查询
```
用户: "Hello, I need help with network infrastructure"
流程: Chat → ASI:One → 响应
```

### 场景2: 复杂需求
```
用户: "I need SD-WAN solutions for 10 branch offices with budget $100,000"
流程: Chat → ASI:One → Local Agent → Monday Agent → 集成响应
```

### 场景3: 产品推荐
```
用户: "What wireless products do you recommend?"
流程: Chat → ASI:One → 产品匹配 → 成本计算 → 响应
```

## 🔧 故障排除

### Agent无响应
1. 检查Agent是否在正确端口运行
2. 确认ASI:One API密钥配置正确
3. 查看日志中的错误信息

### 协调失败
1. 确认支持Agent正在运行
2. 检查网络连接
3. 验证A2A协议格式

## 📚 技术栈

- **uAgents**: Agent框架
- **ASI:One**: LLM推理
- **aiohttp**: HTTP客户端
- **JSON-RPC 2.0**: 消息协议
- **AgentVerse**: 消息中转

## 💡 扩展建议

1. 添加消息重试机制
2. 实现负载均衡
3. 增加安全认证
4. 添加性能监控
5. 实现消息队列

---

🎉 **享受Agent通信的魅力！** 