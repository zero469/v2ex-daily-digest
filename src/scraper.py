"""V2EX 节点帖子抓取器"""
import json
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict

# V2EX API
V2EX_TOPICS_API = "https://www.v2ex.com/api/topics/show.json"

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

        # 只取最近48小时的帖子
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
                })

        return recent_topics
    except Exception as e:
        print(f"Error fetching node {node}: {e}")
        return []


def fetch_all_nodes() -> Dict[str, List[Dict]]:
    """获取所有节点的帖子"""
    nodes_config = load_config()
    result = {}
    
    for node_config in nodes_config:
        node_name = node_config["name"]
        display_name = get_node_display(node_config)
        print(f"Fetching node: {node_name}")
        topics = fetch_node_topics(node_name)
        
        # 保存节点配置信息供邮件模板使用
        result[node_name] = {
            "config": node_config,
            "topics": topics
        }
        print(f"  Found {len(topics)} recent topics")
    
    return result
