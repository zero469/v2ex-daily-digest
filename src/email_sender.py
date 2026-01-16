"""邮件发送模块 - 使用 Resend"""
import os
import resend
from datetime import datetime
from typing import Dict, List, Any


def generate_html_email(all_data: Dict[str, Dict[str, Any]]) -> str:
    """生成 HTML 格式的邮件内容"""

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
            margin-bottom: 30px;
        }}
        h2 {{
            color: #4a90d9;
            margin-top: 30px;
            margin-bottom: 15px;
            padding: 10px 15px;
            background: #f0f7ff;
            border-radius: 8px;
        }}
        .topic {{
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }}
        .topic:last-child {{
            border-bottom: none;
        }}
        .topic-title {{
            font-size: 15px;
            margin-bottom: 5px;
        }}
        .topic-title a {{
            color: #1a1a2e;
            text-decoration: none;
        }}
        .topic-title a:hover {{
            color: #4a90d9;
        }}
        .topic-summary {{
            font-size: 13px;
            color: #444;
            margin-top: 8px;
            padding: 10px 14px;
            background: #f8f9fa;
            border-left: 3px solid #4a90d9;
            border-radius: 4px;
            line-height: 1.5;
        }}
        .comments-summary {{
            font-size: 12px;
            color: #666;
            margin-top: 6px;
            padding: 8px 12px;
            background: #fff8e6;
            border-left: 3px solid #f0ad4e;
            border-radius: 4px;
        }}
        .topic-meta {{
            font-size: 12px;
            color: #888;
            margin-top: 6px;
        }}
        .replies {{
            background: #e8f4e8;
            color: #2d862d;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
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

    total_count = 0
    for node_name, data in all_data.items():
        config = data["config"]
        topics = data["topics"]
        
        emoji = config.get("emoji", "📌")
        title = config.get("title", node_name)
        node_display = f"{emoji} {title}"
        
        html += f'<h2>{node_display} ({len(topics)})</h2>'

        if topics:
            for topic in topics:
                total_count += 1
                replies_badge = f'<span class="replies">{topic["replies"]} 回复</span>' if topic["replies"] > 0 else ""
                
                # AI 摘要
                summary_html = ""
                if topic.get("summary"):
                    summary_html = f'<div class="topic-summary">💡 {topic["summary"]}</div>'
                
                # 评论精华
                comments_html = ""
                if topic.get("comments_summary"):
                    comments_html = f'<div class="comments-summary">💬 {topic["comments_summary"]}</div>'
                
                html += f"""
        <div class="topic">
            <div class="topic-title">
                <a href="{topic['url']}" target="_blank">{topic['title']}</a>
            </div>
            {summary_html}
            {comments_html}
            <div class="topic-meta">
                👤 {topic['author']} · 🕐 {topic['created']} {replies_badge}
            </div>
        </div>
"""
        else:
            html += '<div class="empty">今日暂无更新</div>'

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


def send_email(to_email: str, all_data: Dict[str, Dict[str, Any]]) -> bool:
    """发送邮件"""
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("Error: RESEND_API_KEY not set")
        return False

    resend.api_key = api_key

    today = datetime.now().strftime("%m/%d")
    html_content = generate_html_email(all_data)

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
