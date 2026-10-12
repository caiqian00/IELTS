# TED 每日精读

为 IELTS Academic 目标总分 7.5 的学习者准备的原创 TED 学习材料。

## 手机阅读网页

网站文件位于 `docs/`。首页按日期展示材料，正文提供六部分跳转目录、TED 官方链接按钮、可展开的参考答案，以及适配手机的字体、行距和深色模式。

### 首次启用 GitHub Pages

在 GitHub 仓库中打开 **Settings → Pages**：

1. 在 **Build and deployment** 中，将 **Source** 选择为 **Deploy from a branch**。
2. Branch 选择 `main`，目录选择 `/docs`，点击 **Save**。
3. 等待 GitHub 部署完成，以 Pages 设置页显示的实际站点网址为准。

默认预期地址为 `https://caiqian00.github.io/IELTS/`；仅在 Pages 已启用并部署成功后才能访问。

当前仓库是私有的。私有仓库发布 Pages 受 GitHub 账户方案限制；若设置页提示方案不支持，需要用户选择升级方案或使用单独的公开网站仓库。此项目不会自动将仓库改为公开。普通 Pages 站点内容通常公开可访问，请按设置页实际提示确认。

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

已验证手机宽度 320、390、430 像素下的首页导航、目录跳转、答案展开和页面宽度。网页化与每日生成任务是不同步骤；本仓库尚未开启每日自动生成。
