# FastAPI 项目上线 Render 教程

这个项目原来只能在本地访问：

```text
http://127.0.0.1:8000
```

`127.0.0.1` 只代表自己的电脑，所以别人打不开。要让别人访问，需要把项目部署到公网服务器。这里用的是 **Render + GitHub + Docker**。

## 一、项目需要先准备好

项目里要有这些文件：

```text
Dockerfile
render.yaml
requirements.txt
backend/
frontend/
docs/
show_pictures/
```

其中：

- `Dockerfile`：告诉 Render 怎么启动项目。
- `render.yaml`：给 Render 的部署配置。
- `/health`：健康检查接口。
- `/`：默认展示页。
- `/showcase`：展示页。
- `/app`：真实系统页面。
- `/docs`：FastAPI 自动接口文档。

这个项目是 FastAPI 后端，所以 `Dockerfile` 里最后启动的是：

```dockerfile
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

注意这里不能写死 `8000`，要用 Render 分配的 `PORT`。

## 二、先把代码推到 GitHub

本地提交代码：

```bash
git add .
git commit -m "Upgrade lead workflow demo and showcase"
git push origin main
```

不要上传这些：

```text
.env
leads.db
outputs/
memory/
```

因为 `.env` 可能有密钥，`leads.db` 是本地数据库，不适合上传。

## 三、在 Render 创建 Web Service

打开：

```text
https://dashboard.render.com
```

然后：

1. 点 `New +`
2. 选 `Web Service`
3. 连接 GitHub
4. 选择项目仓库
5. 配置：

```text
Language: Docker
Branch: main
Region: Oregon (US West)
Root Directory: 留空
Instance Type: Free
```

如果有 Health Check Path，填：

```text
/health
```

环境变量可以填：

```text
CORS_ALLOW_ORIGINS=*
```

飞书 API 那些变量先不填，因为演示版用 mock 更稳定。

然后点：

```text
Deploy Web Service
```

## 四、等待部署完成

Render 会经历：

```text
Building -> Deploying -> Live
```

看到 `Live` 就说明上线成功。

示例公网地址：

```text
https://foreign-trade-lead-demo.onrender.com
```

## 五、上线后测试这些地址

健康检查：

```text
https://foreign-trade-lead-demo.onrender.com/health
```

展示页：

```text
https://foreign-trade-lead-demo.onrender.com/showcase
```

真实系统：

```text
https://foreign-trade-lead-demo.onrender.com/app
```

接口文档：

```text
https://foreign-trade-lead-demo.onrender.com/docs
```

如果 `/health` 返回：

```json
{"status":"ok"}
```

就说明后端正常。

## 六、注意事项

Render 免费版会休眠，所以别人第一次打开可能要等 30-60 秒，这是正常的。

这个项目用了 SQLite，本地数据库不会上传。Render 上线后会生成自己的临时数据库，适合 Demo。如果要生产环境长期保存数据，应该换 PostgreSQL。

## 一句话总结

```text
本地 FastAPI 项目
-> Docker 打包
-> 推到 GitHub
-> Render 从 GitHub 拉代码
-> Render 按 Dockerfile 启动服务
-> 获得公网链接
```

所以别人现在打开根域名会先看到展示页，也可以从页面按钮进入系统粘贴邮件测试。
