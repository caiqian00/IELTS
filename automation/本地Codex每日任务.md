# 本地 Codex 每日 TED 精读

## 在桌面端设置

编辑现有 Automation `ted`，每天 **08:00，Asia/Shanghai** 执行。运行位置必须是本地。
可选择已有项目 `/Users/zikomac/学习/雅思IELTS`；任务将使用其下独立的 `IELTS云端同步` 仓库目录。
对应 RRULE：`FREQ=DAILY;BYHOUR=8;BYMINUTE=0;BYSECOND=0`（时区需在界面确认，不是 RRULE 的一部分）。
用 ChatGPT 账号登录 Codex，使用订阅额度；不要调用 scripts/daily_ted.py，它使用付费 API。
电脑需要在 08:00 开机并保持唤醒，Codex 桌面端需要运行；首次手动执行验证网络和 GitHub 推送权限。

## 可粘贴到 Automation 的任务指令

每天为目标 IELTS Academic 总分 7.5 的学习者制作一份 TED 英语精读，并同步 GitHub 与 Pages。

工作目录：/Users/zikomac/学习/雅思IELTS/IELTS云端同步。
仓库：https://github.com/caiqian00/IELTS.git。
若此目录不存在，从该 HTTPS 地址 clone 到此目录；若目录存在，先核验它确为该仓库且没有未提交修改，不得覆盖其他目录或用户修改。
使用现有 checkout，不另建 Git worktree。开始前检查 git status、当前分支及 origin，在干净仓库使用 main 并 git pull --ff-only origin main。
若遇到未提交的用户修改、分叉或身份不符，停止写入并说明，不 reset、不 force push、不盲目 stash。
沿用此仓库 TED每日精读/ 的材料和索引做历史去重；用户已同意从云端重新开始，不导入电脑旧目录的历史。
输出位置为此同步仓库内的 TED每日精读/；不要覆盖原始 /Users/zikomac/学习/雅思IELTS/TED每日精读 目录。

日期按 Asia/Shanghai 当天。先查已有材料和 索引.md，按视频 URL 的 talk slug 去重。
主题轮换：教育 → 科技 → 环境 → 健康 → 工作 → 城市 → 媒体 → 文化 → 科学 → 全球议题，依据最近材料确定下一主题。
如当天已有正式材料，不重复生成；仍检查网页是否需要重新构建并同步。

浏览 TED 官网，选择 6–15 分钟、有官方英文逐字稿且未重复的演讲。
实际读取官方页面和带时间戳的英文逐字稿，核验讲者、标题、时长、语言和 URL。选材失败则换另一篇官方演讲，不使用转载文本。
生成 YYYY-MM-DD-简短标题.md，包含六部分：
1. 英文标题、讲者、时长、主题、TED 官方视频和交互式英文逐字稿链接。使用仓库现有材料相同的 metadata 格式。
2. 按时间顺序的细致分段导读，每段原创英文概述和中文解释；时间对应官方字幕，不能猜测。
3. 深入语言分析：关键句法、IELTS 口语/写作可迁移表达、词汇与搭配、介词和语域、近义辨析、误用；每项有原创英文例句和中文说明。
4. 论证结构与衔接；只有实际听取音频后才能描述讲者重音语调，否则明确仅为跟读建议。
5. 少量复述、造句和口头表达练习及参考答案。答案以 **原创参考答案：** 开头，练习标题使用 ###，便于网页自动折叠。
6. 当日 20–30 分钟学习步骤和次日复习清单。
不得复制或翻译全文。直接英文引文（连同英文标题）合计不超过 25 词；优先零短句引用，用原创例句分析。
正文 h1 使用 `# YYYY-MM-DD｜中文标题`，六部分使用 `## 一、…` 至 `## 六、…`。
metadata 必须有以下各行，供网页构建读取：
- **英文标题**：实际官方英文标题
- **讲者**：实际讲者
- **时长**：X 分 XX 秒
- **主题**：轮换主题（教育、科技等）
- **官方视频**：https://www.ted.com/talks/实际slug
- **官方交互式英文逐字稿**：https://www.ted.com/talks/实际slug/transcript?language=en

材料核验通过后更新 索引.md，保留已有记录，添加日期、中文标题、主题、官方链接、材料相对链接，更新下一主题。
在仓库根目录准备并运行：
python3 -m venv .venv-pages
.venv-pages/bin/python -m pip install -r scripts/requirements-pages.txt
.venv-pages/bin/python scripts/build_pages.py
使用已有 .venv-pages 即可；保留 TLS 和包校验，不修改 lockfile 或学习之外的程序。
确认 docs/当天日期.html、首页和材料链接正确，目录和答案折叠能正常使用。

只提交本次 TED每日精读/ 和生成的 docs/ 文件。检查 git diff --check 和暂存内容后，以明确提交说明 git commit，再 git push origin HEAD:main。
GitHub Pages 保持 main /docs 分支发布；本地正常 Git 推送会触发 Pages 部署。不得把凭据提交到仓库。
复用现有 Git/GitHub 认证；若推送需要交互且无人值守，明确报告失败，要求用户在本地先完成认证，不索取密钥值。
若 gh 可用，查看 Pages 部署结果；否则实际请求 https://caiqian00.github.io/IELTS/当天日期.html，等待合理部署时间，确认返回新内容。
不要把“推送成功”称为“Pages 已更新”，需要站点内容或部署记录证据；无法验证时保留该限制。
最终汇报今天演讲、输出文件、Git 提交、推送和部署结果，并包含：
1. [精读首页](https://caiqian00.github.io/IELTS/)
2. [今日精读：当天中文标题](https://caiqian00.github.io/IELTS/当天日期.html)
云端 Notify TED update 工作流会在材料或网页提交后等待 Pages 发布完成，再发送 GitHub 手机通知；不需要另设 09:00 定时任务。
