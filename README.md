# V2EX 每日汇总

自动抓取 V2EX 论坛指定节点的帖子，使用 AI 提取重点，每天发送邮件汇总。

## 功能特性

- 🔍 自动抓取指定节点的最新帖子
- 🤖 使用 Azure OpenAI 提取每个帖子的核心内容
- 📧 生成精美的 HTML 邮件并自动发送
- ⚙️ 节点可配置，支持自定义

## 默认节点

| 节点 | 说明 |
|------|------|
| create | 分享创造 |
| ideas | 奇思妙想 |
| programmer | 程序员 |
| all4all | 二手交易 |

## 配置步骤

### 1. 获取 API Keys

**Resend（邮件服务，免费）：**
1. 访问 [Resend](https://resend.com) 并注册账号
2. 进入 Dashboard → API Keys → Create API Key

**Azure OpenAI（AI 摘要）：**
1. 访问 [Azure Portal](https://portal.azure.com) 并创建 Azure OpenAI 资源
2. 获取 API Key 和 Endpoint

### 2. Fork 本仓库

点击右上角 Fork 按钮

### 3. 配置 GitHub Secrets

进入你 Fork 的仓库 → Settings → Secrets and variables → Actions → New repository secret

添加以下 Secrets：

| Name | Value |
|------|-------|
| `RESEND_API_KEY` | 你的 Resend API Key |
| `AZURE_OPENAI_KEY` | 你的 Azure OpenAI API Key |
| `TO_EMAIL` | 你的收件邮箱 |

> ⚠️ 注意：Resend 免费版只能发送到注册时使用的邮箱。如需发送到其他邮箱，需在 Resend 验证自己的域名。

### 4. 启用 GitHub Actions

进入 Actions 标签页，点击 "I understand my workflows, go ahead and enable them"

### 5. 测试运行

进入 Actions → V2EX Daily Digest → Run workflow → Run workflow

## 运行时间

默认每天北京时间早上 8:00 自动运行。

修改 `.github/workflows/daily-digest.yml` 中的 cron 表达式可调整时间：

```yaml
schedule:
  - cron: '0 0 * * *'  # UTC 时间，北京时间 +8
```

## 自定义节点

编辑 `config.json` 文件：

```json
{
    "nodes": [
        {
            "name": "create",
            "title": "分享创造",
            "emoji": "🎨"
        },
        {
            "name": "programmer",
            "title": "程序员",
            "emoji": "👨‍💻"
        }
    ]
}
```

或通过环境变量 `V2EX_NODES` 设置（JSON 格式）。

可用节点列表：https://www.v2ex.com/api/nodes/all.json

## 本地测试

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export RESEND_API_KEY="your-resend-key"
export AZURE_OPENAI_KEY="your-azure-openai-key"
export TO_EMAIL="your-email@example.com"

# 运行
python src/main.py
```

## 项目结构

```
v2ex-daily-digest/
├── .github/workflows/
│   └── daily-digest.yml    # GitHub Actions 工作流
├── src/
│   ├── main.py             # 主程序入口
│   ├── scraper.py          # V2EX 帖子抓取
│   ├── summarizer.py       # Azure OpenAI 摘要
│   └── email_sender.py     # 邮件发送
├── config.json             # 节点配置
├── requirements.txt        # Python 依赖
└── README.md
```
