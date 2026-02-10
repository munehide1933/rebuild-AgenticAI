#!/usr/bin/env python3
"""
一键安装脚本 - Meta-Agent Development System
支持 Windows 和 Linux
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def run_command(command, cwd=None, shell=False):
    """执行命令"""
    try:
        # Windows 上使用 shell=True 来查找 npm
        if platform.system() == "Windows" and command[0] in ["npm", "node"]:
            shell = True
            command = " ".join(command)
        
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=shell,
            check=True,
            capture_output=True,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except FileNotFoundError as e:
        return False, f"Command not found: {command[0] if isinstance(command, list) else command}"

def check_python():
    """检查Python版本"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ Python 3.10+ is required, but found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_node():
    """检查Node.js"""
    print("🔍 Checking Node.js...")
    
    # 尝试多种方式查找 node
    node_commands = ["node", "node.exe"]
    node_found = False
    
    for cmd in node_commands:
        if shutil.which(cmd):
            node_found = True
            break
    
    if not node_found:
        print("❌ Node.js is not installed or not in PATH")
        print("\n📥 Please install Node.js:")
        print("   1. Download from: https://nodejs.org/")
        print("   2. Install with default options")
        print("   3. Restart your terminal/command prompt")
        print("   4. Run this script again")
        return False
    
    success, output = run_command(["node", "--version"])
    if not success:
        print(f"❌ Failed to check Node.js version: {output}")
        return False
    
    print(f"✅ Node.js {output.strip()}")
    return True

def check_npm():
    """检查npm"""
    print("🔍 Checking npm...")
    
    # 尝试查找 npm
    if not shutil.which("npm") and not shutil.which("npm.cmd"):
        print("❌ npm is not installed or not in PATH")
        print("\n📥 npm should come with Node.js installation")
        print("   Please reinstall Node.js from: https://nodejs.org/")
        return False
    
    success, output = run_command(["npm", "--version"])
    if not success:
        print(f"❌ Failed to check npm version: {output}")
        return False
    
    print(f"✅ npm {output.strip()}")
    return True

def setup_backend():
    """设置后端"""
    print("\n📦 Setting up backend...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print(f"❌ Backend directory not found: {backend_dir}")
        return False
    
    venv_dir = backend_dir / "venv"
    
    # 创建虚拟环境
    if not venv_dir.exists():
        print("Creating virtual environment...")
        if platform.system() == "Windows":
            success, output = run_command(["python", "-m", "venv", "venv"], cwd=backend_dir)
        else:
            success, output = run_command(["python3", "-m", "venv", "venv"], cwd=backend_dir)
        
        if not success:
            print(f"❌ Failed to create virtual environment: {output}")
            return False
    
    # 激活虚拟环境并安装依赖
    print("Installing Python dependencies...")
    if platform.system() == "Windows":
        pip_path = venv_dir / "Scripts" / "pip.exe"
    else:
        pip_path = venv_dir / "bin" / "pip"
    
    if not pip_path.exists():
        print(f"❌ pip not found at: {pip_path}")
        return False
    
    success, output = run_command(
        [str(pip_path), "install", "-r", "requirements.txt"],
        cwd=backend_dir
    )
    
    if not success:
        print(f"❌ Failed to install Python dependencies: {output}")
        return False
    
    print("✅ Backend setup complete")
    return True

def setup_frontend():
    """设置前端"""
    print("\n📦 Setting up frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print(f"❌ Frontend directory not found: {frontend_dir}")
        return False
    
    print("Installing Node.js dependencies (this may take a few minutes)...")
    
    # 使用 shell=True 在 Windows 上执行
    if platform.system() == "Windows":
        success, output = run_command(
            "npm install",
            cwd=frontend_dir,
            shell=True
        )
    else:
        success, output = run_command(
            ["npm", "install"],
            cwd=frontend_dir
        )
    
    if not success:
        print(f"❌ Failed to install Node.js dependencies")
        print(f"Error: {output}")
        print("\n🔧 Try manually:")
        print(f"   cd {frontend_dir}")
        print("   npm install")
        return False
    
    print("✅ Frontend setup complete")
    return True

def setup_env():
    """设置环境变量文件"""
    print("\n📝 Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ Created .env from template")
            print("\n⚠️  IMPORTANT: Please edit .env and add your Azure OpenAI credentials!")
        else:
            print("❌ .env.example not found")
            return False
    else:
        print("✅ .env file already exists")
    
    return True

def create_directories():
    """创建必要的目录"""
    print("\n📁 Creating data directories...")
    
    directories = [
        "data/qdrant",
        "data/sqlite",
        "data/uploads"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Data directories created")
    return True

def print_next_steps():
    """打印后续步骤"""
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("=" * 50)
    print()
    print("📋 Next steps:")
    print()
    print("1. Configure Azure OpenAI credentials:")
    print("   - Open .env file in a text editor")
    print("   - Add your Azure OpenAI endpoint and API key")
    print()
    print("2. Start the application:")
    if platform.system() == "Windows":
        print("   - Run: run_windows.bat")
    else:
        print("   - Run: ./run_linux.sh")
    print()
    print("3. Access the application:")
    print("   - Frontend: http://localhost:3000")
    print("   - Backend:  http://localhost:8000")
    print("   - API Docs: http://localhost:8000/docs")
    print()

def main():
    """主函数"""
    print("=" * 50)
    print("Meta-Agent Development System - Setup")
    print("=" * 50)
    print()
    
    # 检查前置条件
    if not check_python():
        return 1
    
    if not check_node():
        input("\nPress Enter to exit...")
        return 1
    
    if not check_npm():
        input("\nPress Enter to exit...")
        return 1
    
    print("\n✅ All prerequisites are installed")
    
    # 设置环境
    if not setup_env():
        return 1
    
    # 创建目录
    if not create_directories():
        return 1
    
    # 设置后端
    if not setup_backend():
        return 1
    
    # 设置前端
    if not setup_frontend():
        print("\n⚠️  Frontend setup failed, but you can try manually:")
        print("   cd frontend")
        print("   npm install")
        input("\nPress Enter to continue...")
    
    print_next_steps()
    
    if platform.system() == "Windows":
        input("\nPress Enter to exit...")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
