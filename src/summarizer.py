"""AI 摘要模块 - 使用 Azure OpenAI"""
import os
import time
from typing import Dict, List
from openai import AzureOpenAI


# Azure OpenAI 配置
AZURE_ENDPOINT = "https://ai-imliuyao1639ai979686794225.cognitiveservices.azure.com/"
AZURE_API_VERSION = "2024-12-01-preview"
DEPLOYMENT_NAME = "gpt-5.2-chat"

# 每批处理的帖子数量
BATCH_SIZE = 10

# 批次之间的延迟（秒）
BATCH_DELAY = 2

# 最大重试次数
MAX_RETRIES = 3

# 重试延迟
RETRY_DELAY = 5


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


def summarize_batch(client: AzureOpenAI, topics: List[Dict]) -> Dict[int, str]:
    """批量总结多个帖子，返回 {topic_id: summary}"""
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
            response = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_completion_tokens=1000,
            )
            
            output_text = response.choices[0].message.content or ""
            
            if output_text:
                return parse_batch_response(output_text)
            return {}
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                wait_time = RETRY_DELAY * (attempt + 1)
                print(f"    Rate limited, waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            
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
    client = get_client()
    if not client:
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
        summaries = summarize_batch(client, batch)
        
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
