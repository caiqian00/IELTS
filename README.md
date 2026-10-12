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

- 当前材料已清空，等待本地任务重新生成。
- [材料索引](TED每日精读/索引.md)
- [每日任务要求](automation/TED每日精读任务.md)

已验证手机宽度 320、390、430 像素下的首页导航、目录跳转、答案展开和页面宽度。网页化与每日生成任务是不同步骤；每日运行的配置和启用前提见下方。

## 本地 Codex 每天 08:00 更新

已移除 GitHub Actions 调用 OpenAI API 生成材料的定时工作流，改用本地 Codex Automation。
本地任务在北京时间（Asia/Shanghai）08:00 生成材料、更新索引和网页、提交并推送 main。Pages 保持 main /docs 分支部署。

在 Codex 桌面端编辑现有任务 ted，使用 [本地任务设置与完整指令](automation/本地Codex每日任务.md)。
当前云端无法直接编辑用户电脑中的 Automation，需在桌面端完成时间和指令替换，并手动验证一次。
电脑需保持唤醒，Codex 需运行；通过 ChatGPT 登录时使用相应 Codex 额度。无需 OPENAI_API_KEY。

## 网页有更新时发送手机通知

工作流 `.github/workflows/notify-ted.yml` 在 main 分支的精读材料或 docs 网页发生更新时执行，不设固定通知时间，也不调用 OpenAI API。
它等待 Pages 上的首页、样式和更新的精读页面与提交内容完全一致后，为仓库所有者创建并指派一条 GitHub Issue 通知。重复运行同一提交不会重复发送。
通知包含：
1. [精读首页](https://caiqian00.github.io/IELTS/)
2. 带材料标题的直接阅读链接（当天材料标为“今日精读”，旧材料标注对应日期）。

手机登录 GitHub App 并开启推送通知，允许系统通知及与提及/指派相关的提醒。实际手机推送取决于账号与手机通知设置；创建 Issue 成功不等于手机已显示通知。
若 Pages 没有成功发布新内容，工作流会报错，不发送“已更新”的成功通知。
更新通知可在 Actions → Notify TED update 中手动测试；它不会生成或修改材料。
