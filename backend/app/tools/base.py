"""
工具基类/协议：每个工具实现 get_context，返回要注入到模型上下文的字符串。
新增功能时在此目录下新建模块并实现 get_context，然后在 tools/__init__.py 中注册。
"""
from typing import Optional, Any
from abc import ABC, abstractmethod


class BaseTool(ABC):
    """可选基类：工具可继承此类并实现 get_context。"""

    name: str = "base"

    @abstractmethod
    async def get_context(
        self,
        message: str,
        project_id: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """返回要拼进 prompt 的上下文文本，无则返回空字符串。"""
        return ""
