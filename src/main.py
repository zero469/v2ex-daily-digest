"""V2EX 每日汇总 - 主程序"""
import os
from scraper import fetch_all_nodes
from email_sender import send_email


def main():
    # 收件人邮箱
    to_email = os.environ.get("TO_EMAIL", "im.liuyao@outlook.com")

    print("=" * 50)
    print("V2EX Daily Digest")
    print("=" * 50)

    # 1. 抓取所有节点
    print("\n📡 Fetching topics from V2EX...")
    all_topics = fetch_all_nodes()

    # 统计
    total = sum(len(topics) for topics in all_topics.values())
    print(f"\n📊 Total topics found: {total}")

    if total == 0:
        print("No new topics in the last 24 hours. Skipping email.")
        return

    # 2. 发送邮件
    print(f"\n📧 Sending email to {to_email}...")
    success = send_email(to_email, all_topics)

    if success:
        print("\n✅ Done!")
    else:
        print("\n❌ Failed to send email")
        exit(1)


if __name__ == "__main__":
    main()
