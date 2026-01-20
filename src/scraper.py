"""V2EX 节点帖子抓取器"""
import json
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict

# V2EX API
V2EX_TOPICS_API = "https://www.v2ex.com/api/topics/show.json"
V2EX_HOT_API = "https://www.v2ex.com/api/topics/hot.json"
V2EX_REPLIES_API = "https://www.v2ex.com/api/replies/show.json"

# 默认节点配置
DEFAULT_NODES = [
    {"name": "create", "title": "分享创造", "emoji": "🎨"},
    {"name": "ideas", "title": "奇思妙想", "emoji": "💡"},
    {"name": "programmer", "title": "程序员", "emoji": "👨‍💻"},
    {"name": "all4all", "title": "二手交易", "emoji": "🛒"},
]


def load_config() -> List[Dict]:
    """加载节点配置"""
    # 优先从环境变量读取
    nodes_env = os.environ.get("V2EX_NODES")
    if nodes_env:
        try:
            return json.loads(nodes_env)
        except json.JSONDecodeError:
            print("Warning: Invalid V2EX_NODES format, using default")
    
    # 其次从配置文件读取
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("nodes", DEFAULT_NODES)
        except Exception as e:
            print(f"Warning: Failed to load config.json: {e}")
    
    return DEFAULT_NODES


def get_node_display(node_config: Dict) -> str:
    """获取节点显示名称"""
    emoji = node_config.get("emoji", "📌")
    title = node_config.get("title", node_config["name"])
    return f"{emoji} {title}"


def parse_topic(topic: Dict, node: str = "") -> Dict:
    """解析帖子数据为统一格式"""
    created_time = datetime.fromtimestamp(topic.get("created", 0))
    return {
        "id": topic.get("id"),
        "title": topic.get("title"),
        "url": f"https://www.v2ex.com/t/{topic.get('id')}",
        "author": topic.get("member", {}).get("username", "unknown"),
        "replies": topic.get("replies", 0),
        "created": created_time.strftime("%Y-%m-%d %H:%M"),
        "node": node or topic.get("node", {}).get("name", ""),
        "node_title": topic.get("node", {}).get("title", ""),
    }


def fetch_hot_topics(limit: int = 20) -> List[Dict]:
    """获取全站热门帖子 Top N"""
    try:
        headers = {
            "User-Agent": "V2EX-Daily-Digest/1.0"
        }
        response = requests.get(V2EX_HOT_API, headers=headers, timeout=30)
        response.raise_for_status()
        topics = response.json()
        
        result = []
        for topic in topics[:limit]:
            result.append(parse_topic(topic))
        
        return result
    except Exception as e:
        print(f"Error fetching hot topics: {e}")
        return []


def fetch_node_topics(node: str, limit: int = 20, sort_by_replies: bool = False) -> List[Dict]:
    """获取指定节点的帖子
    
    Args:
        node: 节点名称
        limit: 返回数量限制
        sort_by_replies: 是否按回复数排序（热度）
    """
    try:
        url = f"{V2EX_TOPICS_API}?node_name={node}"
        headers = {
            "User-Agent": "V2EX-Daily-Digest/1.0"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        topics = response.json()

        # 只取最近48小时的帖子
        now = datetime.now()
        cutoff = now - timedelta(hours=48)

        recent_topics = []
        for topic in topics:
            created_time = datetime.fromtimestamp(topic.get("created", 0))
            if created_time > cutoff:
                recent_topics.append(parse_topic(topic, node))
        
        # 按回复数排序（热度）
        if sort_by_replies:
            recent_topics.sort(key=lambda x: x["replies"], reverse=True)
        
        return recent_topics[:limit]
    except Exception as e:
        print(f"Error fetching node {node}: {e}")
        return []


def fetch_topic_replies(topic_id: int, max_replies: int = 20) -> List[str]:
    """获取帖子的评论内容"""
    try:
        url = f"{V2EX_REPLIES_API}?topic_id={topic_id}"
        headers = {
            "User-Agent": "V2EX-Daily-Digest/1.0"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        replies = response.json()
        
        # 提取评论内容，最多取 max_replies 条
        reply_contents = []
        for reply in replies[:max_replies]:
            content = reply.get("content", "").strip()
            if content:
                # 限制单条评论长度
                if len(content) > 200:
                    content = content[:200] + "..."
                reply_contents.append(content)
        
        return reply_contents
    except Exception:
        # 静默失败，不影响主流程
        return []


def fetch_all_nodes() -> Dict[str, Dict]:
    """获取所有帖子：全站热门 + 各节点热门"""
    result = {}
    
    # 1. 获取全站热门 Top 20
    print("Fetching hot topics...")
    hot_topics = fetch_hot_topics(limit=20)
    result["_hot"] = {
        "config": {"name": "_hot", "title": "全站热门", "emoji": "🔥"},
        "topics": hot_topics
    }
    print(f"  Found {len(hot_topics)} hot topics")
    
    # 记录已获取的帖子ID，避免重复
    seen_ids = {t["id"] for t in hot_topics}
    
    # 2. 获取各节点热门 Top 10（按回复数排序）
    nodes_config = load_config()
    
    for node_config in nodes_config:
        node_name = node_config["name"]
        print(f"Fetching node: {node_name}")
        topics = fetch_node_topics(node_name, limit=20, sort_by_replies=True)
        
        # 过滤掉已在热门中出现的帖子，取 Top 10
        unique_topics = [t for t in topics if t["id"] not in seen_ids][:10]
        
        # 更新已见ID
        seen_ids.update(t["id"] for t in unique_topics)
        
        result[node_name] = {
            "config": node_config,
            "topics": unique_topics
        }
        print(f"  Found {len(unique_topics)} unique hot topics")
    
    return result
