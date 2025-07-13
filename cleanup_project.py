#!/usr/bin/env python3
"""
IQuote Project Cleanup Script
自动清理项目中不必要的文件和目录
"""

import os
import shutil
import glob

def cleanup_project():
    """清理项目中的测试文件和不必要的文件"""
    
    print("🧹 开始清理 IQuote 项目...")
    print("=" * 50)
    
    # 需要删除的文件模式
    files_to_remove = [
        # 测试文件
        "test_*.py",
        "*_test_*.py",
        "retail_store_test_client.py",
        "simple_test_client.py",
        "test_solution_architect_client.py",
        "test_coordination.py",
        "run_tests.py",
        
        # 文档文件（除了 SETUP_README.md）
        "README.md",
        "README_Agent_Access.md", 
        "QUICK_START_GUIDE.md",
        "RUN_A2A_SYSTEM.md",
        "TEST_CLIENTS_README.md",
        "solution_architect_agent_readme.md",
        "*.md",  # 会在后面特殊处理
        
        # 注册和演示脚本
        "register_*.py",
        "run_demo.*",
        "quick_start_agent.py",
        "run_quote_system.py",
        "quote_client.py",
        
        # 旧系统文件
        "trip_*.py",
        "verify_*.py", 
        "setup_*.py",
        "working_mcp_example.py",
        "test_explorer.py",
        "ping_asi_one.py",
        "main_*.py",
        "client_*.py",
        "enhanced_agent_with_ui.py",
        "demo_coordinator.py",
        "check_agent_status.py",
        "complete_agent_setup.py",
        "integrated_mcp_demo.py",
        "pricing_agent.py",
        "agentverse_*.py",
        "a2a_weather_agent.py",
        "agent_explorer.py",
        
        # 其他
        "run_demo.bat",
        "agentverse-mcp-integration.zip",
        "*.zip",
    ]
    
    # 需要删除的目录
    dirs_to_remove = [
        "doc/",
        "__pycache__/",
        "coordinator/", 
        "agentverse-mcp-integration-main/",
        "venv/",  # 保留 .venv，删除 venv
    ]
    
    removed_files = []
    removed_dirs = []
    
    # 删除文件
    for pattern in files_to_remove:
        if pattern == "*.md":
            # 特殊处理 .md 文件，保留 SETUP_README.md
            md_files = glob.glob("*.md")
            for md_file in md_files:
                if md_file != "SETUP_README.md":
                    try:
                        os.remove(md_file)
                        removed_files.append(md_file)
                        print(f"✅ 删除文件: {md_file}")
                    except Exception as e:
                        print(f"❌ 删除失败: {md_file} - {e}")
        else:
            files = glob.glob(pattern)
            for file in files:
                try:
                    os.remove(file)
                    removed_files.append(file)
                    print(f"✅ 删除文件: {file}")
                except Exception as e:
                    print(f"❌ 删除失败: {file} - {e}")
    
    # 删除目录
    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                removed_dirs.append(dir_path)
                print(f"✅ 删除目录: {dir_path}")
            except Exception as e:
                print(f"❌ 删除失败: {dir_path} - {e}")
    
    print("\n" + "=" * 50)
    print("📊 清理结果:")
    print(f"🗑️  删除文件: {len(removed_files)} 个")
    print(f"📁 删除目录: {len(removed_dirs)} 个")
    
    if removed_files:
        print(f"\n删除的文件:")
        for file in removed_files:
            print(f"  - {file}")
    
    if removed_dirs:
        print(f"\n删除的目录:")
        for dir_path in removed_dirs:
            print(f"  - {dir_path}")
    
    print("\n✅ 清理完成！")
    
    # 显示保留的核心文件
    print("\n📋 保留的核心文件:")
    core_files = [
        "IQuote/",
        "requirements.txt",
        "pyproject.toml", 
        "uv.lock",
        "api_keys.py",
        ".env",
        ".gitignore",
        ".python-version",
        ".venv/",
        "SETUP_README.md",
    ]
    
    for core_file in core_files:
        if os.path.exists(core_file):
            print(f"  ✅ {core_file}")
        else:
            print(f"  ⚠️  {core_file} (不存在)")
    
    print("\n🎯 现在可以使用以下命令启动系统:")
    print("cd IQuote && python solution_architect_agent.py")

if __name__ == "__main__":
    # 询问用户确认
    print("⚠️  这个脚本将删除项目中的测试文件和不必要的文件")
    print("📋 将保留以下核心文件:")
    print("  - IQuote/ (核心系统目录)")
    print("  - requirements.txt")
    print("  - pyproject.toml")
    print("  - uv.lock")
    print("  - api_keys.py")
    print("  - .env")
    print("  - .gitignore")
    print("  - .python-version")
    print("  - .venv/")
    print("  - SETUP_README.md")
    
    confirm = input("\n是否确认清理？(y/N): ")
    if confirm.lower() in ['y', 'yes']:
        cleanup_project()
    else:
        print("❌ 取消清理操作") 