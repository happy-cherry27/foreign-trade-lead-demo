# 项目上线说明

这个项目不是纯静态页面，而是一个 FastAPI 后端 + 前端页面 + SQLite Demo 数据库的完整系统。  
因此需要部署成 Web Service 后访问，不能只通过 `file://` 打开展示页。`http://127.0.0.1:8000/` 只代表本机地址，外部访问需要公网部署地址。

## 推荐上线方式

推荐使用 Render 或 Railway 部署 Docker Web Service。

项目已经准备好：

- `Dockerfile`：打包 FastAPI、前端页面和展示页。
- `render.yaml`：Render 可识别的 Web Service 配置。
- `/health`：云平台健康检查接口。
- `/`：默认项目展示页。
- `/showcase`：项目展示页。
- `/app`：真实系统首页。

## 上线后给别人的地址

假设平台分配的域名是：

```text
https://foreign-trade-lead-ai.onrender.com
```

那么可以这样给：

- 项目展示页：`https://foreign-trade-lead-ai.onrender.com/`
- 系统演示：`https://foreign-trade-lead-ai.onrender.com/app`
- 项目展示页备用入口：`https://foreign-trade-lead-ai.onrender.com/showcase`
- 接口文档：`https://foreign-trade-lead-ai.onrender.com/docs`
- 健康检查：`https://foreign-trade-lead-ai.onrender.com/health`

## Render 部署步骤

1. 把代码推到 GitHub 仓库。
2. 打开 Render，选择 `New Web Service`。
3. 连接这个 GitHub 仓库。
4. Runtime 选择 Docker，Render 会自动读取 `Dockerfile`。
5. Health Check Path 填：

```text
/health
```

6. 部署成功后，打开平台生成的公网地址。
7. 进入 `/showcase` 或 `/`，复制公开访问链接。

## 部署效果

这个项目已经不是只能在本地运行的 Demo。  
我把 FastAPI 后端、前端页面和展示页打包成 Docker 服务，部署后外部人员可以直接访问系统、粘贴一封外贸询盘邮件进行测试，并看到 AI 抽取、评分、人审、timeline 和飞书同步的完整闭环。

## 注意

免费云平台的 SQLite 文件通常不是长期持久化数据库，适合 Demo 展示。  
如果进入生产环境，建议把 SQLite 换成 PostgreSQL，并继续完善飞书多维表格 API 的权限、重试和告警策略。
