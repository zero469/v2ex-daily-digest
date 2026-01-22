"""V2EX 每日汇总 - 主程序"""
import os
from scraper import fetch_all_nodes
from summarizer import summarize_topics, generate_daily_overview, get_client
from email_sender import send_email


def main():
    # 收件人邮箱
    to_email = os.environ.get("TO_EMAIL")
    if not to_email:
        print("Error: TO_EMAIL environment variable not set")
        exit(1)

    print("=" * 50)
    print("V2EX Daily Digest")
    print("=" * 50)

    # 1. 抓取所有节点
    print("\n📡 Fetching topics from V2EX...")
    all_data = fetch_all_nodes()

    # 统计
    total = sum(len(data["topics"]) for data in all_data.values())
    print(f"\n📊 Total topics found: {total}")

    if total == 0:
        print("No new topics in the last 48 hours. Skipping email.")
        return

    # 2. 生成今日概览
    print("\n💬 Generating daily overview...")
    daily_overview = ""
    hot_topics = all_data.get("_hot", {}).get("topics", [])
    client = get_client()
    if client and hot_topics:
        daily_overview = generate_daily_overview(client, hot_topics)
        if daily_overview:
            print(f"  Overview: {daily_overview[:50]}...")

    # 3. AI 摘要（区分热门和普通帖子）
    print("\n🤖 Generating AI summaries...")
    for node_name, data in all_data.items():
        if data["topics"]:
            # 热门帖子用更详细的摘要
            is_hot = (node_name == "_hot")
            data["topics"] = summarize_topics(data["topics"], is_hot=is_hot)

    # 4. 发送邮件
    print(f"\n📧 Sending email to {to_email}...")
    success = send_email(to_email, all_data, daily_overview=daily_overview)

    if success:
        print("\n✅ Done!")
    else:
        print("\n❌ Failed to send email")
        exit(1)


if __name__ == "__main__":
    main()
