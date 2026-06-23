# n8n Webhook 接入说明

这个项目已经提供邮箱/工作流入口：

```text
POST https://foreign-trade-lead-demo.onrender.com/api/webhooks/email
```

## 推荐工作流

```text
Gmail Trigger / Email Trigger / Webhook Trigger
-> HTTP Request
-> POST /api/webhooks/email
-> 系统自动抽取线索并保存为 pending_review
```

## 可导入文件

可以在 n8n 里导入：

```text
docs/n8n_email_to_leads_workflow.json
```

导入后会得到两个节点：

- `Webhook Trigger`：接收外部邮件或测试请求。
- `Send to Lead System`：调用本系统公网接口。

## HTTP Request 请求体

```json
{
  "subject": "Urgent quotation needed",
  "sender": "customer@example.com",
  "body": "Customer email body...",
  "source": "n8n",
  "channel": "webhook"
}
```

## 设计说明

我没有把系统强绑定到 Gmail 或某一个企业邮箱，而是提供了 n8n 友好的 webhook 入口。真实业务里，Gmail、IMAP、表单、CRM 或其他数据源都可以通过 n8n HTTP Request 把询盘推到系统，后续统一进入 AI 抽取、人审、评分和飞书同步流程。
