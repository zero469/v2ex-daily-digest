"""AI 摘要模块 - 使用 Azure OpenAI"""
import os
import time
from typing import Dict, List
from openai import AzureOpenAI

from scraper import fetch_topic_replies


# Azure OpenAI 配置
AZURE_ENDPOINT = "https://ai-imliuyao1639ai979686794225.cognitiveservices.azure.com/"
AZURE_API_VERSION = "2024-12-01-preview"
DEPLOYMENT_NAME = "gpt-5.2-chat"

# 最大重试次数
MAX_RETRIES = 3

# 重试延迟
RETRY_DELAY = 3

# 请求间延迟（避免限流）
REQUEST_DELAY = 1


def get_client() -> AzureOpenAI | None:
    """获取 Azure OpenAI 客户端"""
    api_key = os.environ.get("AZURE_OPENAI_KEY")
    if not api_key:
        return None
    
    return AzureOpenAI(
        api_version=AZURE_API_VERSION,
        azure_endpoint=AZURE_ENDPOINT,
        api_key=api_key,
    )


def summarize_single_topic(client: AzureOpenAI, topic: Dict) -> Dict[str, str]:
    """为单个帖子生成摘要和评论总结
    
    返回: {"summary": "...", "comments_summary": "..."}
    """
    topic_id = topic["id"]
    title = topic["title"]
    replies_count = topic.get("replies", 0)
    
    # 获取评论内容
    replies = []
    if replies_count > 0:
        replies = fetch_topic_replies(topic_id, max_replies=15)
    
    # 构建 prompt
    if replies:
        replies_text = "\n".join([f"- {r}" for r in replies[:10]])
        prompt = f"""请为这个V2EX帖子生成摘要。

帖子标题：{title}

热门评论（共{replies_count}条，展示部分）：
{replies_text}

请按以下格式输出：

【帖子摘要】
（50-100字，详细描述帖子的核心内容、作者的主要观点或分享的内容）

【评论精华】
（30-60字，总结评论区的主要讨论方向、热门观点或有价值的回复）

请直接输出，不要有其他内容："""
    else:
        prompt = f"""请为这个V2EX帖子生成摘要。

帖子标题：{title}

请按以下格式输出：

【帖子摘要】
（50-100字，根据标题推断帖子的核心内容、可能讨论的话题）

请直接输出，不要有其他内容："""

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=500,
            )
            
            output_text = response.choices[0].message.content or ""
            
            if output_text:
                return parse_summary_response(output_text)
            return {"summary": "", "comments_summary": ""}
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                wait_time = RETRY_DELAY * (attempt + 1)
                print(f"      Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            print(f"      Error (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    return {"summary": "", "comments_summary": ""}


def parse_summary_response(text: str) -> Dict[str, str]:
    """解析摘要响应"""
    result = {"summary": "", "comments_summary": ""}
    
    lines = text.strip().split("\n")
    current_section = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        if "【帖子摘要】" in line:
            if current_section and current_content:
                result[current_section] = " ".join(current_content).strip()
            current_section = "summary"
            current_content = []
        elif "【评论精华】" in line:
            if current_section and current_content:
                result[current_section] = " ".join(current_content).strip()
            current_section = "comments_summary"
            current_content = []
        elif line and current_section:
            # 移除括号提示
            if not (line.startswith("（") and line.endswith("）")):
                current_content.append(line)
    
    # 保存最后一个 section
    if current_section and current_content:
        result[current_section] = " ".join(current_content).strip()
    
    return result


def summarize_topics(topics: List[Dict]) -> List[Dict]:
    """为帖子列表添加 AI 摘要"""
    client = get_client()
    if not client:
        print("Warning: AZURE_OPENAI_KEY not set, skipping summarization")
        return topics
    
    if not topics:
        return topics
    
    print(f"  Summarizing {len(topics)} topics (with comments)...")
    
    success_count = 0
    for i, topic in enumerate(topics):
        # 请求间延迟
        if i > 0:
            time.sleep(REQUEST_DELAY)
        
        print(f"    [{i+1}/{len(topics)}] {topic['title'][:30]}...")
        
        result = summarize_single_topic(client, topic)
        
        topic["summary"] = result.get("summary", "")
        topic["comments_summary"] = result.get("comments_summary", "")
        
        if topic["summary"]:
            success_count += 1
    
    print(f"  Total: {success_count}/{len(topics)} topics summarized")
    
    return topics
