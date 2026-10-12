# TED 每日精读

为 IELTS Academic 目标总分 7.5 的学习者准备的原创 TED 学习材料。

## 手机阅读网页

网站文件位于 `docs/`。首页按日期展示材料，正文提供六部分跳转目录、TED 官方链接按钮、可展开的参考答案，以及适配手机的字体、行距和深色模式。

### 首次启用 GitHub Pages

在 GitHub 仓库中打开 **Settings → Pages**：

1. 在 **Build and deployment** 中，将 **Source** 选择为 **Deploy from a branch**。
2. Branch 选择 `main`，目录选择 `/docs`，点击 **Save**。
3. 等待 GitHub 部署完成，以 Pages 设置页显示的实际站点网址为准。

网站已上线：https://caiqian00.github.io/IELTS/ 。

当前仓库和 Pages 网站均为公开。请勿把个人信息或凭据写进学习材料。

### 手机版样板

![手机首页效果](docs/assets/mobile-preview.png)

## 更新材料和网页

Markdown 内容保存在 `TED每日精读/`；索引与逐字稿链接保留，网页是从这些材料生成的，不需分别编辑两份正文。

在仓库根目录运行：

```sh
python3 -m venv .venv-pages
.venv-pages/bin/python -m pip install -r scripts/requirements-pages.txt
.venv-pages/bin/python scripts/build_pages.py
```

构建脚本查找 `YYYY-MM-DD-标题.md`，生成 `docs/YYYY-MM-DD.html` 和首页，并把练习参考答案改成可展开内容。每天仅支持一篇材料，重复日期会报错。新增材料后需重新构建，并将 Markdown 与生成的 `docs/` 一起提交到 `main`；Pages 启用后会由 GitHub 部署分支更新。

不要向 `docs/` 添加任何私密资料。网页仅包含学习材料及静态资源，不包含任务说明或凭据。

## 当前内容

- [2026-10-12：每个孩子都需要支持者](TED每日精读/2026-10-12-每个孩子都需要支持者.md)
- [材料索引](TED每日精读/索引.md)
- [每日任务要求](automation/TED每日精读任务.md)

已验证手机宽度 320、390、430 像素下的首页导航、目录跳转、答案展开和页面宽度。网页化与每日生成任务是不同步骤；每日运行的配置和启用前提见下方。

## 每天早上 8 点自动更新

工作流：`.github/workflows/daily-ted.yml`，北京时间（Asia/Shanghai）每天 08:00，即 UTC 00:00。
GitHub 的定时触发可能延迟；这不是精确到分钟的提醒服务。公开仓库长期没有活动时，GitHub 也可能暂停定时工作流。

### 启用前提

1. 工作流文件须存在于默认分支 `main`，仓库 Actions 须允许运行。
2. 在 **Settings → Secrets and variables → Actions → New repository secret** 中添加 `OPENAI_API_KEY`，值是你的 OpenAI API Key。不要提交密钥到文件或发在聊天里。
3. OpenAI API 账户需有可用额度及所选模型和 Web Search 的访问权限。API 用量单独计费，不由 ChatGPT 订阅自动覆盖。
4. Pages 保持 **Deploy from a branch → main → /docs**。工作流显式请求 Pages 构建，避免 `GITHUB_TOKEN` 提交不触发自动部署的问题。

默认生成模型是 `gpt-5-mini`；可通过同一设置页的仓库变量 `TED_MODEL` 指定支持 Responses API、结构化输出和 Web Search 的模型。

第一次请在 **Actions → Daily TED reading → Run workflow** 手动运行。当天已有材料时不再次调用 API；它会重建网站并验证 Pages 部署。要验证真实内容生成，可以等待第二天或输入未生成的日期；这会产生 API 用量。

流程：读取历史去重与轮换主题 → 搜索 TED 官方视频 → 实际读取官网与英文逐字稿、核验 6–15 分钟及时间戳 → 生成原创材料 → 校验 → 更新索引与手机网站 → 提交 main → 请求并确认对应提交的 Pages 构建。

来源、生成或校验失败时工作流报错，不发布失败内容；已上线的旧网页继续可读。定时工作流尚未端到端通过一次带凭据的生成测试前，不应视为已验证可每天成功运行。
