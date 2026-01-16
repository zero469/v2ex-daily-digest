"""V2EX 每日汇总 - 主程序"""
import os
from scraper import fetch_all_nodes
from summarizer import summarize_topics
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

    # 2. AI 摘要
    print("\n🤖 Generating AI summaries...")
    for node_name, data in all_data.items():
        if data["topics"]:
            data["topics"] = summarize_topics(data["topics"])

    # 3. 发送邮件
    print(f"\n📧 Sending email to {to_email}...")
    success = send_email(to_email, all_data)

    if success:
        print("\n✅ Done!")
    else:
        print("\n❌ Failed to send email")
        exit(1)


if __name__ == "__main__":
    main()
