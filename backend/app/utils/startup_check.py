"""启动前环境检查"""
import os
from app.config import settings

def check_environment():
    """检查环境配置"""
    errors = []
    warnings = []
    
    # 检查必需的环境变量（无配置时降级为本地占位响应）
    required_vars = [
        ("AZURE_OPENAI_ENDPOINT", settings.AZURE_OPENAI_ENDPOINT),
        ("AZURE_OPENAI_API_KEY", settings.AZURE_OPENAI_API_KEY),
        ("AZURE_OPENAI_DEPLOYMENT_NAME", settings.AZURE_OPENAI_DEPLOYMENT_NAME),
        ("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT),
    ]
    
    for var_name, var_value in required_vars:
        if not var_value or "your-" in var_value.lower() or "here" in var_value.lower():
            warnings.append(f"⚠️  {var_name} is not configured; LLM will use fallback responses")
    
    # 检查数据目录
    data_dirs = [
        "./data/qdrant",
        "./data/sqlite",
        "./data/uploads"
    ]
    
    for dir_path in data_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            warnings.append(f"✅ Created directory: {dir_path}")
    
    # 检查 SECRET_KEY
    if "your-secret" in settings.SECRET_KEY.lower() or "change" in settings.SECRET_KEY.lower():
        warnings.append("⚠️  SECRET_KEY is using default value, please change it in production")
    
    # 输出结果
    if errors:
        print("\n" + "="*50)
        print("🔴 CRITICAL ERRORS:")
        for error in errors:
            print(f"  {error}")
        print("="*50 + "\n")
        return False
    
    if warnings:
        print("\n" + "="*50)
        print("🟡 WARNINGS:")
        for warning in warnings:
            print(f"  {warning}")
        print("="*50 + "\n")
    
    print("✅ Environment check passed!\n")
    return True
