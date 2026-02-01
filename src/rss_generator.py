"""V2EX RSS Feed 生成器"""
import os
from datetime import datetime
from email.utils import formatdate
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
from typing import Dict, List, Optional
import time


def generate_rss(all_data: Dict[str, Dict], output_path: str = "output/v2ex-digest.xml", 
                 max_items: int = 30) -> bool:
    """
    生成 RSS 2.0 格式的 feed 文件
    
    Args:
        all_data: 从 main.py 传来的数据，格式:
            {
                "node_name": {
                    "config": {"name": "...", "title": "...", "emoji": "..."},
                    "topics": [
                        {"id": 123, "title": "...", "url": "...", "summary": "...", ...}
                    ]
                }
            }
        output_path: RSS 文件输出路径
        max_items: 最大条目数限制
        
    Returns:
        bool: 是否成功生成
    """
    try:
        # 创建 RSS 根元素
        rss = Element("rss", version="2.0")
        rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")
        
        channel = SubElement(rss, "channel")
        
        # 频道元信息
        title = SubElement(channel, "title")
        title.text = "V2EX 每日汇总"
        
        link = SubElement(channel, "link")
        link.text = "https://www.v2ex.com"
        
        description = SubElement(channel, "description")
        description.text = "V2EX 精选帖子每日摘要 - 自动抓取热门内容，AI 智能总结"
        
        language = SubElement(channel, "language")
        language.text = "zh-cn"
        
        # 最后构建时间
        last_build = SubElement(channel, "lastBuildDate")
        last_build.text = formatdate(time.time(), usegmt=True)
        
        # 生成器信息
        generator = SubElement(channel, "generator")
        generator.text = "V2EX Daily Digest RSS Generator"
        
        # Atom self link (RSS 最佳实践)
        atom_link = SubElement(channel, "{http://www.w3.org/2005/Atom}link")
        atom_link.set("href", "https://zero469.github.io/v2ex-daily-digest/v2ex-digest.xml")
        atom_link.set("rel", "self")
        atom_link.set("type", "application/rss+xml")
        
        # 收集所有帖子并生成 items
        all_topics = []
        
        for node_name, data in all_data.items():
            config = data.get("config", {})
            topics = data.get("topics", [])
            node_emoji = config.get("emoji", "📌")
            node_title = config.get("title", node_name)
            
            for topic in topics:
                topic["_node_display"] = f"{node_emoji} {node_title}"
                all_topics.append(topic)
        
        # 按创建时间排序（如果有的话），限制数量
        # 注意：created 可能是字符串格式 "2024-01-01 08:00"
        all_topics = all_topics[:max_items]
        
        # 生成 RSS items
        for topic in all_topics:
            item = SubElement(channel, "item")
            
            # 标题：带节点前缀
            item_title = SubElement(item, "title")
            node_display = topic.get("_node_display", "")
            item_title.text = f"[{node_display}] {topic.get('title', '无标题')}"
            
            # 链接
            item_link = SubElement(item, "link")
            item_link.text = topic.get("url", "")
            
            # 描述：使用 AI 摘要或原标题
            item_desc = SubElement(item, "description")
            summary = topic.get("summary", "")
            if summary:
                # 使用 CDATA 包裹，避免 HTML 字符问题
                item_desc.text = summary
            else:
                # 如果没有摘要，显示基本信息
                author = topic.get("author", "unknown")
                replies = topic.get("replies", 0)
                item_desc.text = f"作者: {author} | 回复数: {replies}"
            
            # GUID (唯一标识)
            item_guid = SubElement(item, "guid", isPermaLink="true")
            item_guid.text = topic.get("url", "")
            
            # 发布时间
            item_pub_date = SubElement(item, "pubDate")
            created = topic.get("created", "")
            if created:
                try:
                    # 尝试解析时间字符串
                    if isinstance(created, str):
                        dt = datetime.strptime(created, "%Y-%m-%d %H:%M")
                    else:
                        dt = datetime.now()
                    item_pub_date.text = formatdate(dt.timestamp(), usegmt=True)
                except (ValueError, TypeError):
                    item_pub_date.text = formatdate(time.time(), usegmt=True)
            else:
                item_pub_date.text = formatdate(time.time(), usegmt=True)
            
            # 作者
            if topic.get("author"):
                item_author = SubElement(item, "author")
                item_author.text = topic.get("author")
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 写入文件
        tree = ElementTree(rss)
        
        # 手动生成 XML 声明和格式化
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += _pretty_xml(rss)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_content)
        
        print(f"✅ RSS feed generated: {output_path} ({len(all_topics)} items)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate RSS feed: {e}")
        return False


def _pretty_xml(element: Element, indent: str = "  ", level: int = 0) -> str:
    """简单的 XML 格式化"""
    result = ""
    tag = element.tag
    
    # 处理命名空间
    if tag.startswith("{"):
        ns_end = tag.find("}")
        ns = tag[1:ns_end]
        local_tag = tag[ns_end + 1:]
        # 对于 atom 命名空间使用前缀
        if "atom" in ns.lower():
            tag = f"atom:{local_tag}"
        else:
            tag = local_tag
    
    # 开始标签
    attrs = ""
    for key, value in element.attrib.items():
        attrs += f' {key}="{value}"'
    
    if len(element) == 0 and element.text is None:
        # 自闭合标签
        result = f"{indent * level}<{tag}{attrs}/>\n"
    elif len(element) == 0:
        # 有文本内容的标签
        text = element.text or ""
        # 转义 XML 特殊字符
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        result = f"{indent * level}<{tag}{attrs}>{text}</{tag}>\n"
    else:
        # 有子元素的标签
        result = f"{indent * level}<{tag}{attrs}>\n"
        for child in element:
            result += _pretty_xml(child, indent, level + 1)
        result += f"{indent * level}</{tag}>\n"
    
    return result


if __name__ == "__main__":
    # 测试用例
    test_data = {
        "_hot": {
            "config": {"name": "_hot", "title": "全站热门", "emoji": "🔥"},
            "topics": [
                {
                    "id": 123456,
                    "title": "测试帖子标题",
                    "url": "https://www.v2ex.com/t/123456",
                    "author": "testuser",
                    "replies": 42,
                    "created": "2026-02-02 10:00",
                    "summary": "这是一个测试摘要，展示 AI 生成的内容概述。"
                }
            ]
        },
        "create": {
            "config": {"name": "create", "title": "分享创造", "emoji": "🎨"},
            "topics": [
                {
                    "id": 789012,
                    "title": "分享一个开源项目",
                    "url": "https://www.v2ex.com/t/789012",
                    "author": "developer",
                    "replies": 15,
                    "created": "2026-02-02 09:30",
                    "summary": "一个很棒的开源工具，解决了某个痛点问题。"
                }
            ]
        }
    }
    
    # 测试生成
    generate_rss(test_data, "output/v2ex-digest.xml")
