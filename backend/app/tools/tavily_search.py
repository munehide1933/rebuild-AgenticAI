import os
import requests

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def tavily_search(query: str) -> str:
    """
    调用 Tavily Search API，返回文本内容。
    """
    if not TAVILY_API_KEY:
        return "Tavily API key not found."

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": 5
    }

    try:
        response = requests.post(url, json=payload)
        data = response.json()
        return "\n".join(i.get("content", "") for i in data.get("results", []))
    except Exception as e:
        return f"Search error: {e}"