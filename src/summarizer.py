"""AI 摘要模块 - 使用 Azure OpenAI"""
import os
import time
import requests
from typing import Dict, List


# Azure OpenAI 配置
AZURE_OPENAI_ENDPOINT = os.environ.get(
    "AZURE_OPENAI_ENDPOINT",
    "https://ai-imliuyao1639ai979686794225.cognitiveservices.azure.com/openai/responses"
)
AZURE_API_VERSION = "2025-04-01-preview"

# 每批处理的帖子数量
BATCH_SIZE = 10

# 批次之间的延迟（秒）
BATCH_DELAY = 2

# 最大重试次数
MAX_RETRIES = 3

# 重试延迟
RETRY_DELAY = 5


def summarize_batch(topics: List[Dict]) -> Dict[int, str]:
    """批量总结多个帖子，返回 {topic_id: summary}"""
    api_key = os.environ.get("AZURE_OPENAI_KEY")
    if not api_key:
        return {}
    
    # 构建批量 prompt
    topics_text = ""
    for topic in topics:
        topics_text += f"\n- 【{topic['id']}】{topic['title']}"
    
    prompt = f"""请为以下V2EX帖子各生成一句简短的中文摘要（15-40字），提取核心要点。

格式要求：每行一个，格式为 "ID:摘要"，例如：
123456:这是一个关于xxx的分享
789012:作者开发了一个yyy工具

帖子列表：{topics_text}

请严格按格式输出，每个ID一行，不要有其他内容："""

    for attempt in range(MAX_RETRIES):
        try:
            url = f"{AZURE_OPENAI_ENDPOINT}?api-version={AZURE_API_VERSION}"
            
            response = requests.post(
                url,
                json={
                    "model": "gpt-4o",
                    "input": prompt,
                },
                headers={
                    "Content-Type": "application/json",
                    "api-key": api_key
                },
                timeout=60
            )
            
            if response.status_code == 429:
                wait_time = RETRY_DELAY * (attempt + 1)
                print(f"    Rate limited, waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            result = response.json()
            
            # Azure OpenAI responses API 格式
            output_text = ""
            if "output" in result:
                for item in result.get("output", []):
                    if item.get("type") == "message":
                        for content in item.get("content", []):
                            if content.get("type") == "output_text":
                                output_text = content.get("text", "")
                                break
            
            if output_text:
                return parse_batch_response(output_text)
            return {}
            
        except Exception as e:
            print(f"    Azure OpenAI error (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    return {}


def parse_batch_response(text: str) -> Dict[int, str]:
    """解析批量响应，返回 {topic_id: summary}"""
    result = {}
    for line in text.strip().split("\n"):
        line = line.strip()
        if ":" in line and line[0].isdigit():
            try:
                # 解析 "ID:摘要" 格式
                parts = line.split(":", 1)
                topic_id = int(parts[0].strip())
                summary = parts[1].strip()
                if summary:
                    result[topic_id] = summary
            except (ValueError, IndexError):
                continue
    return result


def summarize_topics(topics: List[Dict]) -> List[Dict]:
    """为帖子列表添加 AI 摘要"""
    api_key = os.environ.get("AZURE_OPENAI_KEY")
    if not api_key:
        print("Warning: AZURE_OPENAI_KEY not set, skipping summarization")
        return topics
    
    if not topics:
        return topics
    
    print(f"  Summarizing {len(topics)} topics in batches of {BATCH_SIZE}...")
    
    # 分批处理
    for i in range(0, len(topics), BATCH_SIZE):
        batch = topics[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(topics) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"    Processing batch {batch_num}/{total_batches}...")
        
        # 批次间延迟
        if i > 0:
            time.sleep(BATCH_DELAY)
        
        # 批量获取摘要
        summaries = summarize_batch(batch)
        
        # 应用摘要到帖子
        success_count = 0
        for topic in batch:
            topic_id = topic["id"]
            if topic_id in summaries:
                topic["summary"] = summaries[topic_id]
                success_count += 1
            else:
                topic["summary"] = ""
        
        print(f"    Batch {batch_num}: {success_count}/{len(batch)} summaries generated")
    
    total_success = sum(1 for t in topics if t.get("summary"))
    print(f"  Total: {total_success}/{len(topics)} topics summarized")
    
    return topics
