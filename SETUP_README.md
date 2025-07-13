# IQuote - 智能网络解决方案架构师系统

## 📋 项目概述

IQuote 是一个基于 ASI:One 集成的智能网络解决方案架构师系统，包含以下核心组件：

- **Solution Architect Agent** - 主要的 ASI:One 兼容代理
- **Local Data Agent** - 本地数据增强代理 (A2A协议)
- **Monday Data Agent** - Monday.com 数据集成代理 (A2A协议)

## 🚀 快速启动

### 1. 环境准备

```bash
# 激活虚拟环境
source .venv/bin/activate  # 或者 source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API 密钥

确保你有 `api_keys.py` 文件，包含以下配置：

```python
class Config:
    def get_asi_one_config(self):
        return {
            'base_url': 'https://api.asi1.ai/v1',
            'api_key': 'your-asi-one-api-key'
        }
    
    def get_gemini_config(self):
        return {
            'api_key': 'your-gemini-api-key'
        }
```

### 3. 启动系统

#### 方式一：完整系统启动（推荐）

```bash
# 1. 启动 Local Data Agent (端口 8003)
cd IQuote
python local_data_agent.py &

# 2. 启动 Monday Data Agent (端口 8005)  
python monday_data_agent.py &

# 3. 启动 Solution Architect Agent (端口 8002)
python solution_architect_agent.py
```

#### 方式二：仅启动核心代理

```bash
# 只启动 Solution Architect Agent
cd IQuote
python solution_architect_agent.py
```

## 📊 系统架构

```
ASI:One Orchestrator
        ↓
Solution Architect Agent (Port 8002)
        ├─→ Local Data Agent (Port 8003) [A2A Protocol]
        ├─→ Monday Data Agent (Port 8005) [A2A Protocol]  
        └─→ ASI:One API (asi1-mini model)
```

## 🔧 功能特性

- **ASI:One 兼容** - 实现 Chat Protocol 协议
- **多代理协调** - 与 Local Data Agent 和 Monday Data Agent 协作
- **智能分析** - 使用 ASI:One asi1-mini 模型进行需求分析
- **产品推荐** - 基于网络基础设施产品目录的智能推荐
- **成本计算** - 自动计算多分支部署的成本和折扣
- **自然语言处理** - 支持中英文需求理解

## 📝 日志管理

系统会自动生成带时间戳的日志文件：
- 格式：`agent_logs_YYYYMMDD_HHMMSS.txt`
- 位置：IQuote/ 目录下
- 内容：包含所有代理通信和协调的详细日志

## 🧪 测试

如需测试系统功能，可以使用：

```bash
# 简单测试
python test_coordination.py

# 完整测试套件
python run_tests.py
```

## 📁 项目结构

```
agi/
├── IQuote/                    # 核心系统目录
│   ├── solution_architect_agent.py    # 主代理
│   ├── local_data_agent.py            # 本地数据代理
│   ├── monday_data_agent.py           # Monday.com 代理
│   └── agent_logs_*.txt               # 日志文件
├── requirements.txt           # Python 依赖
├── pyproject.toml            # 项目配置
├── uv.lock                   # 依赖锁文件
├── api_keys.py               # API 密钥配置
├── .env                      # 环境变量
├── .gitignore               # Git 忽略文件
├── .python-version          # Python 版本
└── .venv/                   # 虚拟环境
```

## 🗑️ 清理建议

### 可以删除的文件（测试和演示文件）：

```bash
# 测试文件
rm test_*.py
rm *_test_*.py

# 文档文件（除了此README）
rm *.md (除了 SETUP_README.md)

# 注册和演示脚本
rm register_*.py
rm run_demo.*
rm quick_start_agent.py
rm run_quote_system.py
rm quote_client.py

# 旧系统文件
rm trip_*.py
rm verify_*.py
rm setup_*.py
rm working_mcp_example.py

# 其他目录
rm -rf doc/
rm -rf __pycache__/
rm -rf coordinator/
rm -rf agentverse-mcp-integration-main/
```

### 必须保留的文件：

```bash
# 核心系统
IQuote/                    # 整个目录
requirements.txt           # 依赖文件
pyproject.toml            # 项目配置
uv.lock                   # 依赖锁文件
api_keys.py               # API密钥
.env                      # 环境变量
.gitignore               # Git忽略
.python-version          # Python版本
.venv/                   # 虚拟环境 (或 venv/)
```

## 🎯 使用示例

启动系统后，Solution Architect Agent 会：

1. **监听 ASI:One 消息** - 通过 Mailbox 模式接收来自 ASI:One 的请求
2. **解析需求** - 使用 ASI:One asi1-mini 模型分析客户需求
3. **协调代理** - 与 Local Data Agent 和 Monday Data Agent 协作
4. **生成方案** - 返回综合的网络解决方案建议

### 示例对话：

```
用户: "我需要为20个分支建立SD-WAN网络，包含安全和无线功能，预算100万"

系统: [分析需求] → [调用ASI:One] → [协调其他代理] → [生成综合方案]

响应: 详细的产品推荐、成本分析、技术规格和实施建议
```

## 💬 支持

如有问题，请检查：
1. 日志文件中的详细错误信息
2. API 密钥配置是否正确
3. 所有代理是否正常启动
4. 网络连接是否正常

---

✅ **系统已准备就绪，可以开始使用！** 