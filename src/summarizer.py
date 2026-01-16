"""AI 摘要模块 - 使用 Gemini"""
import os
import requests
from typing import Dict, List


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


def summarize_topic(title: str, content: str = "") -> str:
    """使用 Gemini 总结单个帖子"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return ""
    
    prompt = f"""请用1-2句中文简洁总结这个V2EX帖子的核心内容和要点。只输出总结，不要其他内容。

标题：{title}
{f'内容：{content[:1000]}' if content else ''}"""

    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 150
                }
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        # 提取生成的文本
        candidates = result.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "").strip()
        return ""
    except Exception as e:
        print(f"Gemini API error: {e}")
        return ""


def fetch_topic_content(topic_id: int) -> str:
    """获取帖子详细内容"""
    try:
        url = f"https://www.v2ex.com/api/topics/show.json?id={topic_id}"
        headers = {"User-Agent": "V2EX-Daily-Digest/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0].get("content", "")
        return ""
    except Exception:
        return ""


def summarize_topics(topics: List[Dict]) -> List[Dict]:
    """为帖子列表添加 AI 摘要"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not set, skipping summarization")
        return topics
    
    print("  Generating AI summaries...")
    for topic in topics:
        # 获取帖子内容
        content = fetch_topic_content(topic["id"])
        # 生成摘要
        summary = summarize_topic(topic["title"], content)
        topic["summary"] = summary
        if summary:
            print(f"    ✓ {topic['title'][:30]}...")
    
    return topics
