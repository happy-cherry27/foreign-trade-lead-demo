# 外贸客户邮件线索自动录入与跟进建议系统

一个面向外贸销售场景的 AI 工程闭环 Demo：把客户邮件自动抽取成结构化销售线索，进入待审核状态，并保留 AI 判断依据、审核记录和后续跟进建议。

## 项目背景

外贸销售经常通过邮件收到客户询盘。邮件中可能包含客户姓名、公司、国家、产品需求、数量、预算、交期和联系方式。如果全部人工录入，效率低，容易漏字段，也很难判断哪些客户需要优先跟进。

这个 Demo 的目标不是做完整 CRM，而是在最小范围内证明：AI 可以进入真实业务流程，帮助销售完成线索录入、优先级判断和跟进建议，同时通过人工审核降低误判风险。

## 核心闭环

```text
客户邮件输入 -> AI/规则抽取 -> SQLite 入库 -> 页面展示 -> 人工审核 -> 日志记录 -> CSV 导出
```

## 真实业务架构

```text
Gmail / IMAP / 外贸询盘邮箱
        ↓
 n8n Email Trigger
        ↓
 n8n HTTP Request
        ↓
POST /api/webhooks/email
        ↓
字段抽取 + 字段级证据 + lead_score + 回复草稿 + 缺字段追问
        ↓
pending_review 人工审核
        ↓
timeline 留痕
        ↓
飞书多维表格 / HubSpot / CRM
```

## 功能清单

- 邮件正文录入
- n8n/Webhook 邮件入口：`POST /api/webhooks/email`
- 批量导入 `.txt` / `.eml` 邮件
- 三类内置样例邮件：完整、缺字段、紧急
- 客户线索字段抽取
- 字段缺失时返回 `unknown`
- 优先级识别：high / medium / low
- 线索评分：`lead_score` + `score_breakdown`
- 字段级证据：每个字段展示置信度和来源片段
- 适合跟进时间建议
- 跟进建议生成
- 英文回复草稿生成
- 缺字段追问生成：预算、数量、电话、产品规格、目的国、交期
- AI 抽取依据和置信度展示
- SQLite 保存客户线索
- 线索列表和状态筛选
- 线索详情人工修改、确认、拒绝
- AI 抽取日志、人工审核记录和时间线展示
- CSV 导出
- 飞书多维表格同步状态

## 技术栈

- Backend: FastAPI + SQLite
- Frontend: HTML + CSS + JavaScript
- AI extraction: transparent rule-based extractor first, replaceable with a real LLM API later
- Deployment artifact: Dockerfile

## 数据表

### `leads`

保存客户线索主数据。

关键字段：

- `name`
- `email`
- `company`
- `country`
- `phone`
- `product_need`
- `budget`
- `quantity`
- `urgency`
- `priority`
- `lead_score`
- `score_breakdown`
- `follow_up_time`
- `status`
- `original_email`
- `follow_up_suggestion`
- `reply_draft`
- `created_at`
- `updated_at`

### `ai_extraction_logs`

保存每次抽取的原始邮件、结构化 JSON、置信度、判断依据和模型名称。

### `review_records`

保存人工审核动作，包括确认/拒绝、修改前数据、修改后数据、审核备注和审核时间。

## API 清单

| Method | Path | 用途 |
| --- | --- | --- |
| GET | `/health` | 健康检查 |
| POST | `/api/leads/extract` | 从邮件正文抽取结构化线索 |
| POST | `/api/leads` | 保存线索 |
| POST | `/api/webhooks/email` | 给 n8n / 邮箱触发器使用的邮件入口 |
| POST | `/api/leads/import-batch` | 批量导入多封邮件 |
| GET | `/api/leads` | 获取线索列表，支持 `status` 筛选 |
| GET | `/api/leads/export.csv` | 导出线索 CSV |
| GET | `/api/leads/{id}` | 获取线索详情 |
| PATCH | `/api/leads/{id}/review` | 人工确认或拒绝线索 |
| POST | `/api/leads/{id}/sync/feishu` | 同步到飞书多维表格 |
| GET | `/api/leads/{id}/logs` | 查看 AI 日志和审核记录 |

## n8n / Webhook / 飞书 API 怎么理解

这个项目里有三个不同层次：

- **n8n**：工作流编排器，负责“什么时候触发、把数据送到哪里”。例如 Gmail 收到新邮件后，n8n 自动调用本系统的 webhook。
- **Webhook**：本系统对外暴露的入口。外部系统用 HTTP 请求把邮件推过来，本系统接收后自动抽取线索。
- **飞书 API**：下游系统出口。线索经人工确认后，可以推送到飞书多维表格，让销售团队协作跟进。

推荐面试表达：

```text
Gmail / IMAP Email Trigger
-> n8n workflow
-> HTTP Request 调用 POST /api/webhooks/email
-> 本系统抽取并保存为 pending_review
-> 销售人工审核
-> 同步到飞书多维表格或正式 CRM
```

当前版本已经实现了 n8n 友好的 webhook 入口和飞书多维表格 OpenAPI 同步。未配置飞书环境变量时会记录为本地演示兜底；配置飞书凭证后，`/api/leads/{id}/sync/feishu` 会调用飞书多维表格 OpenAPI 写入数据。

### n8n HTTP Request 示例

请求地址：

```text
POST http://127.0.0.1:8000/api/webhooks/email
```

请求 JSON：

```json
{
  "subject": "Urgent quotation needed",
  "sender": "daniel.smith@northpeak.ca",
  "body": "This is Daniel at NorthPeak Supplies from Canada. We need 1200 sets of metal storage racks...",
  "source": "n8n",
  "channel": "gmail"
}
```

系统会自动完成：

```text
接收邮件 -> 抽取字段 -> 计算 lead_score -> 生成回复草稿 -> 保存为待审核 -> 写入 timeline
```

### n8n 字段映射建议

在 n8n 里可以这样配置 HTTP Request 节点：

| n8n 邮件字段 | 发送给本系统 |
| --- | --- |
| Email Subject | `subject` |
| From / Sender | `sender` |
| Text Plain / Text HTML | `body` |
| 固定值 `n8n` | `source` |
| 固定值 `gmail` 或 `imap` | `channel` |

面试表达：

```text
我没有在 Demo 里直接写 Gmail 轮询，因为这会把系统耦合到某一个邮箱服务。
更通用的做法是用 n8n 接 Gmail/IMAP，再通过 HTTP Request 调我的 webhook。
这样以后换企业邮箱、Outlook 或表单入口，都不用改核心线索系统。
```

### 飞书真实同步配置

`.env` 配置以下变量后，飞书同步接口会调用真实 OpenAPI：

```text
FEISHU_APP_ID=
FEISHU_APP_SECRET=
FEISHU_BITABLE_APP_TOKEN=
FEISHU_BITABLE_TABLE_ID=
```

默认不配置时，系统仍可稳定演示，并在 timeline 中记录本地演示兜底同步。

如果真实飞书接口调用失败，系统会：

- 将 `sync_status` 更新为 `failed`
- 在 timeline 中写入 `sync_failed`
- 保留“同步飞书”按钮，修正配置后可再次点击重试

### CORS 配置

本地 Demo 默认允许浏览器调试。生产环境建议通过环境变量限制来源：

```text
CORS_ALLOW_ORIGINS=https://your-frontend.example.com
```

多个来源用英文逗号分隔。

## 线索评分怎么理解

`lead_score` 不是黑箱 AI 分数，而是一套透明销售优先级规则，用来回答“销售今天先跟谁”。当前评分维度包括：

- 紧急程度：是否出现 ASAP、deadline、within 3 days、this week。
- 商业价值：是否有预算、数量、quote、purchase、confirm supplier 等信号。
- 联系完整度：邮箱、电话、公司、国家是否完整。
- 产品清晰度：是否能识别产品需求。
- 市场匹配：是否能识别国家和市场。
- 风险扣分：免费邮箱、关键字段缺失、信息过泛。

这不是生产级预测模型，但适合 Demo 阶段，因为它可解释、可调试、方便销售审核。

## 本地启动

```powershell
cd "D:\陈雅婷\04_牛马AI\工作区\01_求职实习\projects\外贸客户邮件线索自动录入与跟进建议系统"
python -m uvicorn backend.main:app --reload --port 8000
```

打开页面：

```text
http://127.0.0.1:8000
```

API 文档：

```text
http://127.0.0.1:8000/docs
```

## Docker 启动

```powershell
docker build -t foreign-trade-lead-demo .
docker run --rm -p 8000:8000 foreign-trade-lead-demo
```

然后打开：

```text
http://127.0.0.1:8000
```

## 演示流程

1. 打开首页。
2. 点击 `完整` / `缺字段` / `紧急` 任一示例邮件。
3. 点击“抽取客户线索”。
4. 检查字段、字段级证据、线索评分、评分拆解、跟进建议和英文回复草稿。
5. 点击“保存线索”。
6. 在线索列表中打开详情。
7. 修改字段或添加审核备注。
8. 点击“确认线索”或“拒绝线索”。
9. 查看 AI 抽取、人审动作组成的时间线。
10. 点击“导出 CSV”导出线索表。
11. 点击“同步到飞书”，查看同步状态和时间线事件。

## 本轮调研后新增的产品判断

全网同类产品和开源项目的共同方向不是“只把邮件解析成 JSON”，而是把销售线索变成可排序、可审核、可流转的业务对象。因此本项目新增了三类更贴近真实销售运营的能力：

- 可解释：字段级证据和置信度，方便销售判断 AI 是否可信。
- 可排序：`lead_score` 和评分拆解，帮助销售优先处理高意向询盘。
- 可行动：英文回复草稿和时间线，让线索从录入走向跟进闭环。

## 项目边界

第一版刻意不做：

- 真实邮箱接入
- N8N 真接入
- 飞书 API 真接入
- 完整 CRM
- 登录权限
- 复杂客户评分模型

这样做是为了优先保证核心业务闭环稳定可演示。

## 后续扩展

- 邮箱 Webhook：收到客户邮件后自动触发抽取。
- N8N：负责邮箱、飞书、CRM 之间的工作流编排。
- 飞书多维表格：作为早期销售线索协作表，目前已接入飞书 OpenAPI，可将确认后的线索写入表格。
- 正式 CRM：将确认后的线索同步到销售系统。
- 批量导入：一次处理多封询盘邮件。
- 同步状态：记录飞书、HubSpot 或 Google Sheets 的推送结果。
- GEO 获客：把社媒评论、私信、主页线索也转成统一客户线索。
- 真实 LLM API：替换当前透明规则抽取器。

## 面试表达重点

这个 Demo 的关键点不是“AI 自动替销售做决定”，而是让 AI 先生成结构化建议，再进入人工审核流程。外贸客户关系比较敏感，保留审核和日志更符合真实业务落地方式。
