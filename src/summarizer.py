"""AI 摘要模块 - 使用 Azure OpenAI"""
import os
import time
from typing import Dict, List, Optional
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


def generate_daily_overview(client: AzureOpenAI, hot_topics: List[Dict]) -> str:
    """基于热门帖子生成今日一句话概览"""
    if not hot_topics:
        return ""
    
    # 提取热门帖子标题
    titles = [t["title"] for t in hot_topics[:15]]
    titles_text = "\n".join([f"- {t}" for t in titles])
    
    prompt = f"""你是V2EX社区的观察员。根据今天的热门帖子标题，用一句话（30-50字）总结今天V2EX社区在讨论什么。

今日热门帖子：
{titles_text}

要求：
1. 用轻松、有趣的语气
2. 提炼2-3个核心话题/趋势
3. 可以适当加入emoji
4. 不要用"今天"开头

直接输出一句话，不要有其他内容："""

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=100,
            )
            return response.choices[0].message.content.strip() or ""
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    return ""


def summarize_single_topic(client: AzureOpenAI, topic: Dict, is_hot: bool = False) -> Dict:
    """为单个帖子生成摘要和评论精华
    
    Args:
        client: Azure OpenAI 客户端
        topic: 帖子数据
        is_hot: 是否为热门帖子（热门帖子获取更详细的摘要和评论原文）
    
    返回: {"summary": "...", "comments_summary": "...", "featured_comments": [...]}
    """
    topic_id = topic["id"]
    title = topic["title"]
    replies_count = topic.get("replies", 0)
    
    # 获取评论内容（现在包含作者信息）
    replies = []
    if replies_count > 0:
        replies = fetch_topic_replies(topic_id, max_replies=20 if is_hot else 15)
    
    # 热门帖子：更详细的摘要 + 提取精彩评论原文
    if is_hot and replies:
        replies_text = "\n".join([f"- @{r['author']}: {r['content']}" for r in replies[:15]])
        prompt = f"""请为这个V2EX热门帖子生成深度摘要。

帖子标题：{title}

评论区（共{replies_count}条，展示部分）：
{replies_text}

请按以下格式输出：

【帖子摘要】
（80-150字，深入分析这个帖子的核心内容、为什么值得一看、读者能从中获得什么。写得有洞察力，让人想点进去看）

【精彩评论】
（从评论中挑选2-3条最有价值、最有趣或最有争议的评论，保留原文和作者。格式如下）
@用户名: 评论原文
@用户名: 评论原文

请直接输出，不要有其他内容："""
    elif replies:
        replies_text = "\n".join([f"- {r['content']}" for r in replies[:10]])
        prompt = f"""请为这个V2EX帖子生成摘要。

帖子标题：{title}

热门评论（共{replies_count}条，展示部分）：
{replies_text}

请按以下格式输出：

【帖子摘要】
（50-100字，描述帖子的核心内容、作者的主要观点）

【评论精华】
（30-60字，总结评论区的主要讨论方向、热门观点）

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
                max_completion_tokens=600 if is_hot else 500,
            )
            
            output_text = response.choices[0].message.content or ""
            
            if output_text:
                return parse_summary_response(output_text, is_hot)
            return {"summary": "", "comments_summary": "", "featured_comments": []}
            
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
    
    return {"summary": "", "comments_summary": "", "featured_comments": []}


def parse_summary_response(text: str, is_hot: bool = False) -> Dict:
    """解析摘要响应"""
    result = {"summary": "", "comments_summary": "", "featured_comments": []}
    
    lines = text.strip().split("\n")
    current_section = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        if "【帖子摘要】" in line:
            if current_section and current_content:
                _save_section(result, current_section, current_content, is_hot)
            current_section = "summary"
            current_content = []
        elif "【评论精华】" in line or "【精彩评论】" in line:
            if current_section and current_content:
                _save_section(result, current_section, current_content, is_hot)
            current_section = "featured_comments" if is_hot else "comments_summary"
            current_content = []
        elif line and current_section:
            # 移除括号提示
            if not (line.startswith("（") and line.endswith("）")):
                current_content.append(line)
    
    # 保存最后一个 section
    if current_section and current_content:
        _save_section(result, current_section, current_content, is_hot)
    
    return result


def _save_section(result: Dict, section: str, content: List[str], is_hot: bool):
    """保存解析的 section 内容"""
    if section == "featured_comments":
        # 解析精彩评论：格式 "@用户名: 评论内容"
        for line in content:
            if line.startswith("@"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    author = parts[0].strip().lstrip("@")
                    comment = parts[1].strip()
                    result["featured_comments"].append({
                        "author": author,
                        "content": comment
                    })
    else:
        result[section] = " ".join(content).strip()


def summarize_topics(topics: List[Dict], is_hot: bool = False) -> List[Dict]:
    """为帖子列表添加 AI 摘要
    
    Args:
        topics: 帖子列表
        is_hot: 是否为热门帖子（热门帖子获取更详细的摘要）
    """
    client = get_client()
    if not client:
        print("Warning: AZURE_OPENAI_KEY not set, skipping summarization")
        return topics
    
    if not topics:
        return topics
    
    label = "hot" if is_hot else "node"
    print(f"  Summarizing {len(topics)} {label} topics...")
    
    success_count = 0
    for i, topic in enumerate(topics):
        # 请求间延迟
        if i > 0:
            time.sleep(REQUEST_DELAY)
        
        print(f"    [{i+1}/{len(topics)}] {topic['title'][:30]}...")
        
        result = summarize_single_topic(client, topic, is_hot=is_hot)
        
        topic["summary"] = result.get("summary", "")
        topic["comments_summary"] = result.get("comments_summary", "")
        topic["featured_comments"] = result.get("featured_comments", [])
        
        if topic["summary"]:
            success_count += 1
    
    print(f"  Total: {success_count}/{len(topics)} topics summarized")
    
    return topics
