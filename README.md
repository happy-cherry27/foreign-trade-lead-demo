# 外贸客户邮件线索自动录入与跟进建议系统

一个面向外贸销售场景的 AI 工程闭环 Demo：把客户邮件自动抽取成结构化销售线索，进入待审核状态，并保留 AI 判断依据、审核记录和后续跟进建议。

## 项目背景

外贸销售经常通过邮件收到客户询盘。邮件中可能包含客户姓名、公司、国家、产品需求、数量、预算、交期和联系方式。如果全部人工录入，效率低，容易漏字段，也很难判断哪些客户需要优先跟进。

这个 Demo 的目标不是做完整 CRM，而是在最小范围内证明：AI 可以进入真实业务流程，帮助销售完成线索录入、优先级判断和跟进建议，同时通过人工审核降低误判风险。

## 核心闭环

```text
客户邮件输入 -> AI/规则抽取 -> SQLite 入库 -> 页面展示 -> 人工审核 -> 日志记录 -> CSV 导出
```

## 功能清单

- 邮件正文录入
- 三类内置样例邮件：完整、缺字段、紧急
- 客户线索字段抽取
- 字段缺失时返回 `unknown`
- 优先级识别：high / medium / low
- 适合跟进时间建议
- 跟进建议生成
- AI/mock 抽取依据和置信度展示
- SQLite 保存客户线索
- 线索列表和状态筛选
- 线索详情人工修改、确认、拒绝
- AI 抽取日志和人工审核记录
- CSV 导出

## 技术栈

- Backend: FastAPI + SQLite
- Frontend: HTML + CSS + JavaScript
- AI extraction: rule-based mock extractor first, replaceable with a real LLM API later
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
- `follow_up_time`
- `status`
- `original_email`
- `follow_up_suggestion`
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
| GET | `/api/leads` | 获取线索列表，支持 `status` 筛选 |
| GET | `/api/leads/export.csv` | 导出线索 CSV |
| GET | `/api/leads/{id}` | 获取线索详情 |
| PATCH | `/api/leads/{id}/review` | 人工确认或拒绝线索 |
| GET | `/api/leads/{id}/logs` | 查看 AI 日志和审核记录 |

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
4. 检查字段、置信度、判断依据和跟进建议。
5. 点击“保存线索”。
6. 在线索列表中打开详情。
7. 修改字段或添加审核备注。
8. 点击“确认线索”或“拒绝线索”。
9. 查看 AI 日志和审核记录。
10. 点击“导出 CSV”导出线索表。

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
- 飞书多维表格：作为早期销售线索协作表。
- 正式 CRM：将确认后的线索同步到销售系统。
- GEO 获客：把社媒评论、私信、主页线索也转成统一客户线索。
- 真实 LLM API：替换当前 rule-based mock extractor。

## 面试表达重点

这个 Demo 的关键点不是“AI 自动替销售做决定”，而是让 AI 先生成结构化建议，再进入人工审核流程。外贸客户关系比较敏感，保留审核和日志更符合真实业务落地方式。
