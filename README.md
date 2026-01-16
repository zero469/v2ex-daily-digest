# V2EX 每日汇总

自动抓取 V2EX 论坛的 tech、creative、play、deals 节点，每天发送邮件汇总。

## 配置步骤

### 1. 获取 Resend API Key（免费）

1. 访问 [Resend](https://resend.com) 并注册账号
2. 进入 Dashboard → API Keys → Create API Key
3. 复制生成的 API Key

### 2. Fork 本仓库

点击右上角 Fork 按钮

### 3. 配置 GitHub Secrets

进入你 Fork 的仓库 → Settings → Secrets and variables → Actions → New repository secret

添加以下 Secrets：

| Name | Value |
|------|-------|
| `RESEND_API_KEY` | 你的 Resend API Key |
| `TO_EMAIL` | 你的邮箱地址（如 im.liuyao@outlook.com） |

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

## 本地测试

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export RESEND_API_KEY="your-api-key"
export TO_EMAIL="your-email@example.com"

# 运行
python src/main.py
```

## 自定义节点

编辑 `src/scraper.py` 中的 `NODES` 列表：

```python
NODES = ["tech", "creative", "play", "deals"]
```

可用节点列表：https://www.v2ex.com/api/nodes/all.json
