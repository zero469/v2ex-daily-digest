"""V2EX 节点帖子抓取器"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict

# 要抓取的节点
NODES = ["tech", "create", "play", "deals"]

# V2EX API
V2EX_TOPICS_API = "https://www.v2ex.com/api/topics/show.json"

# 节点中文名映射
NODE_NAMES = {
    "tech": "科技",
    "create": "分享创造",
    "play": "分享与探索",
    "deals": "优惠信息"
}


def fetch_node_topics(node: str, limit: int = 20) -> List[Dict]:
    """获取指定节点的最新帖子"""
    try:
        url = f"{V2EX_TOPICS_API}?node_name={node}"
        headers = {
            "User-Agent": "V2EX-Daily-Digest/1.0"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        topics = response.json()

        # 只取最近48小时的帖子（确保有内容）
        now = datetime.now()
        cutoff = now - timedelta(hours=48)

        recent_topics = []
        for topic in topics[:limit]:
            created_time = datetime.fromtimestamp(topic.get("created", 0))
            if created_time > cutoff:
                recent_topics.append({
                    "id": topic.get("id"),
                    "title": topic.get("title"),
                    "url": f"https://www.v2ex.com/t/{topic.get('id')}",
                    "author": topic.get("member", {}).get("username", "unknown"),
                    "replies": topic.get("replies", 0),
                    "created": created_time.strftime("%Y-%m-%d %H:%M"),
                    "node": node,
                    "node_name": NODE_NAMES.get(node, node)
                })

        return recent_topics
    except Exception as e:
        print(f"Error fetching node {node}: {e}")
        return []


def fetch_all_nodes() -> Dict[str, List[Dict]]:
    """获取所有节点的帖子"""
    result = {}
    for node in NODES:
        print(f"Fetching node: {node}")
        topics = fetch_node_topics(node)
        result[node] = topics
        print(f"  Found {len(topics)} recent topics")
    return result
