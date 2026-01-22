"""邮件发送模块 - 使用 Resend"""
import os
import resend
from datetime import datetime
from typing import Dict, List, Any, Optional


def generate_html_email(all_data: Dict[str, Dict[str, Any]], daily_overview: str = "") -> str:
    """生成 HTML 格式的邮件内容
    
    新布局：
    1. 今日一句话概览
    2. 热门 Top 5 卡片样式（大标题、完整摘要、精彩评论引用）
    3. 各节点紧凑列表（标题 + 简短摘要）
    """

    today = datetime.now().strftime("%Y年%m月%d日")

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a1a2e;
            border-bottom: 3px solid #4a90d9;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        
        /* 今日概览 */
        .daily-overview {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 24px;
            border-radius: 12px;
            margin-bottom: 30px;
            font-size: 16px;
            line-height: 1.6;
        }}
        .daily-overview-label {{
            font-size: 13px;
            opacity: 0.9;
            margin-bottom: 8px;
        }}
        
        /* 节点标题 */
        h2 {{
            color: #4a90d9;
            margin-top: 30px;
            margin-bottom: 15px;
            padding: 10px 15px;
            background: #f0f7ff;
            border-radius: 8px;
            font-size: 16px;
        }}
        
        /* 热门帖子卡片 */
        .hot-card {{
            background: #fff;
            border: 1px solid #e8e8e8;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            transition: box-shadow 0.2s;
        }}
        .hot-card:hover {{
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }}
        .hot-card-title {{
            font-size: 17px;
            font-weight: 600;
            margin-bottom: 12px;
            line-height: 1.4;
        }}
        .hot-card-title a {{
            color: #1a1a2e;
            text-decoration: none;
        }}
        .hot-card-title a:hover {{
            color: #4a90d9;
        }}
        .hot-card-summary {{
            font-size: 14px;
            color: #444;
            margin-bottom: 14px;
            padding: 12px 16px;
            background: #f8f9fa;
            border-left: 4px solid #4a90d9;
            border-radius: 4px;
            line-height: 1.6;
        }}
        
        /* 精彩评论引用块 */
        .featured-comments {{
            background: #fffbf0;
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 12px;
        }}
        .featured-comments-label {{
            font-size: 12px;
            color: #b8860b;
            font-weight: 500;
            margin-bottom: 10px;
        }}
        .featured-comment {{
            font-size: 13px;
            color: #555;
            padding: 8px 0;
            border-bottom: 1px dashed #e8e0d0;
            line-height: 1.5;
        }}
        .featured-comment:last-child {{
            border-bottom: none;
            padding-bottom: 0;
        }}
        .featured-comment-author {{
            color: #b8860b;
            font-weight: 500;
        }}
        
        .hot-card-meta {{
            font-size: 12px;
            color: #888;
            margin-top: 10px;
        }}
        .replies-badge {{
            background: #e8f4e8;
            color: #2d862d;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
        }}
        
        /* 紧凑列表样式 */
        .compact-list {{
            margin: 0;
            padding: 0;
            list-style: none;
        }}
        .compact-item {{
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
            display: flex;
            align-items: flex-start;
        }}
        .compact-item:last-child {{
            border-bottom: none;
        }}
        .compact-bullet {{
            color: #4a90d9;
            margin-right: 10px;
            flex-shrink: 0;
        }}
        .compact-content {{
            flex: 1;
        }}
        .compact-title {{
            font-size: 14px;
            margin-bottom: 3px;
        }}
        .compact-title a {{
            color: #1a1a2e;
            text-decoration: none;
        }}
        .compact-title a:hover {{
            color: #4a90d9;
        }}
        .compact-summary {{
            font-size: 12px;
            color: #666;
            line-height: 1.4;
        }}
        .compact-meta {{
            font-size: 11px;
            color: #999;
            margin-top: 4px;
        }}
        
        .empty {{
            color: #999;
            font-style: italic;
            padding: 20px;
            text-align: center;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            text-align: center;
            color: #888;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📰 V2EX 每日精选 - {today}</h1>
"""

    # 今日概览
    if daily_overview:
        html += f"""
        <div class="daily-overview">
            <div class="daily-overview-label">💬 今日一句话</div>
            {daily_overview}
        </div>
"""

    total_count = 0
    
    # 热门帖子 Top 5（卡片样式）
    hot_data = all_data.get("_hot", {})
    hot_topics = hot_data.get("topics", [])[:5]  # 只展示 Top 5
    
    if hot_topics:
        html += f'<h2>🔥 今日热门 TOP {len(hot_topics)}</h2>'
        
        for topic in hot_topics:
            total_count += 1
            html += generate_hot_card(topic)
    
    # 其他节点（紧凑列表）
    for node_name, data in all_data.items():
        if node_name == "_hot":
            continue
            
        config = data["config"]
        topics = data["topics"]
        
        if not topics:
            continue
        
        emoji = config.get("emoji", "📌")
        title = config.get("title", node_name)
        node_display = f"{emoji} {title}"
        
        html += f'<h2>{node_display} ({len(topics)})</h2>'
        html += '<ul class="compact-list">'
        
        for topic in topics:
            total_count += 1
            html += generate_compact_item(topic)
        
        html += '</ul>'

    html += f"""
        <div class="footer">
            共收录 {total_count} 篇帖子 · 由 V2EX Daily Digest 自动生成<br>
            <a href="https://www.v2ex.com" style="color: #4a90d9;">访问 V2EX</a>
        </div>
    </div>
</body>
</html>
"""
    return html


def generate_hot_card(topic: Dict) -> str:
    """生成热门帖子卡片 HTML"""
    title = topic["title"]
    url = topic["url"]
    author = topic["author"]
    created = topic["created"]
    replies = topic.get("replies", 0)
    summary = topic.get("summary", "")
    featured_comments = topic.get("featured_comments", [])
    
    # 回复徽章
    replies_badge = ""
    if replies > 0:
        replies_badge = f'<span class="replies-badge">{replies} 回复</span>'
    
    # 摘要
    summary_html = ""
    if summary:
        summary_html = f'<div class="hot-card-summary">💡 {summary}</div>'
    
    # 精彩评论
    comments_html = ""
    if featured_comments:
        comments_items = ""
        for comment in featured_comments[:3]:
            author_name = comment.get("author", "")
            content = comment.get("content", "")
            comments_items += f'''
            <div class="featured-comment">
                <span class="featured-comment-author">@{author_name}:</span> {content}
            </div>'''
        
        comments_html = f'''
        <div class="featured-comments">
            <div class="featured-comments-label">💬 精彩评论</div>
            {comments_items}
        </div>'''
    
    return f"""
        <div class="hot-card">
            <div class="hot-card-title">
                <a href="{url}" target="_blank">{title}</a>
            </div>
            {summary_html}
            {comments_html}
            <div class="hot-card-meta">
                👤 {author} · 🕐 {created} {replies_badge}
            </div>
        </div>
"""


def generate_compact_item(topic: Dict) -> str:
    """生成紧凑列表项 HTML"""
    title = topic["title"]
    url = topic["url"]
    author = topic["author"]
    replies = topic.get("replies", 0)
    summary = topic.get("summary", "")
    
    # 截取摘要（紧凑模式只显示一行）
    short_summary = ""
    if summary:
        short_summary = summary[:80] + "..." if len(summary) > 80 else summary
    
    replies_text = f" · {replies}回复" if replies > 0 else ""
    
    return f"""
        <li class="compact-item">
            <span class="compact-bullet">•</span>
            <div class="compact-content">
                <div class="compact-title">
                    <a href="{url}" target="_blank">{title}</a>
                </div>
                <div class="compact-summary">{short_summary}</div>
                <div class="compact-meta">👤 {author}{replies_text}</div>
            </div>
        </li>
"""


def send_email(to_email: str, all_data: Dict[str, Dict[str, Any]], daily_overview: str = "") -> bool:
    """发送邮件"""
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("Error: RESEND_API_KEY not set")
        return False

    resend.api_key = api_key

    today = datetime.now().strftime("%m/%d")
    html_content = generate_html_email(all_data, daily_overview)

    # 计算总帖子数
    total = sum(len(data["topics"]) for data in all_data.values())

    try:
        params = {
            "from": "V2EX Daily <digest@resend.dev>",
            "to": [to_email],
            "subject": f"📰 V2EX 每日精选 ({today}) - {total}篇新帖",
            "html": html_content
        }

        email = resend.Emails.send(params)
        print(f"Email sent successfully! ID: {email['id']}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
