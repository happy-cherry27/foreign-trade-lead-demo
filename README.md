# 外贸客户邮件线索自动录入与跟进建议系统

## 项目目标

把外贸客户邮件自动转成可审核、可跟进、可追踪的客户线索。

## 核心闭环

邮件输入 -> AI/规则抽取 -> SQLite 存储 -> 页面展示 -> 人工审核 -> 日志记录 -> 跟进建议。

## 技术栈

- Backend: FastAPI + SQLite
- Frontend: HTML + CSS + JavaScript
- AI extraction: rule-based mock extractor first, replaceable with real LLM API later

## 第一版不做

- 真实邮箱接入
- N8N 真接入
- 飞书 API 真接入
- 完整 CRM
- 登录权限
- 复杂 UI

## 启动方式

```powershell
cd "D:\陈雅婷\04_牛马AI\工作区\01_求职实习\projects\外贸客户邮件线索自动录入与跟进建议系统"
python -m uvicorn backend.main:app --reload --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

API 文档：

```text
http://127.0.0.1:8000/docs
```

## 演示流程

1. 打开首页。
2. 粘贴一封外贸客户邮件，或点击示例邮件。
3. 点击“抽取客户线索”。
4. 检查字段、判断依据和跟进建议。
5. 点击“保存线索”。
6. 在线索列表中打开详情。
7. 修改字段后确认或拒绝。
8. 查看 AI 日志和审核记录。

## 后续扩展

- 邮箱 Webhook：收到客户邮件后自动触发抽取。
- N8N：负责邮箱、飞书、CRM 之间的工作流编排。
- 飞书多维表格：作为早期销售线索协作表。
- GEO 获客：把社媒评论、私信、主页线索也转成统一客户线索。
- Docker：用于部署到服务器。
