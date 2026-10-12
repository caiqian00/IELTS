#!/usr/bin/env python3
"""Build the mobile reading site from the existing TED Markdown lessons."""
from __future__ import annotations

import hashlib
import html
import re
from datetime import date
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'TED每日精读'
OUT = ROOT / 'docs'


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def anchor(value: str, separator: str) -> str:
    return 'section-' + hashlib.sha256(value.encode()).hexdigest()[:10]


def fold_answers(source: str) -> str:
    pattern = r'^\*\*原创参考答案：\*\*(.*?)(?=^#{1,3} |\Z)'
    def replace(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        return '\n<details class="answer" markdown="1">\n<summary>查看参考答案与解释</summary>\n\n' + body + '\n\n</details>\n\n'
    return re.sub(pattern, replace, source, flags=re.MULTILINE | re.DOTALL)


def frame(title: str, body: str, description: str) -> str:
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="description" content="{esc(description)}">
<title>{esc(title)} · TED 每日精读</title>
<link rel="stylesheet" href="assets/styles.css">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
</head>
<body>
<a class="skip-link" href="#main">跳到正文</a>
<header class="site-header"><nav aria-label="主导航"><a class="brand" href="index.html"><span class="brand-icon" aria-hidden="true">T</span>TED 每日精读</a><span class="nav-note">IELTS 7.5 学习计划</span></nav></header>
<main id="main">{body}</main>
<footer class="site-footer">原创学习导读 · 完整逐字稿请访问 TED 官方网站<br>个人学习项目，与 TED 官方无隶属关系</footer>
</body>
</html>
'''


def metadata(source: str, label: str) -> str:
    match = re.search(r'^- \*\*' + re.escape(label) + r'\*\*：(.+)$', source, re.MULTILINE)
    if not match:
        raise ValueError(f'Missing metadata: {label}')
    return match.group(1).strip()


def build() -> None:
    OUT.mkdir(exist_ok=True)
    lessons = []
    for path in sorted(SOURCE.glob('????-??-??-*.md'), reverse=True):
        source = path.read_text(encoding='utf-8')
        day = path.name[:10]
        date.fromisoformat(day)
        if any(item['day'] == day for item in lessons):
            raise ValueError(f'More than one lesson for {day}; choose unique page names first')
        heading = re.match(r'^# (.+)\n', source)
        if not heading:
            raise ValueError(f'Missing title in {path}')
        title = heading.group(1).split('｜', 1)[-1].strip()
        speaker = metadata(source, '讲者').split('，', 1)[0].rstrip('。')
        duration = metadata(source, '时长').split('（', 1)[0]
        topic = metadata(source, '主题').split('／', 1)[0]
        video = metadata(source, '官方视频')
        transcript = metadata(source, '官方交互式英文逐字稿')
        if not video.startswith('https://www.ted.com/talks/') or not transcript.startswith('https://www.ted.com/talks/'):
            raise ValueError('Expected TED official HTTPS links')
        page = day + '.html'
        md = markdown.Markdown(extensions=['toc', 'tables', 'sane_lists', 'md_in_html'], extension_configs={'toc': {'toc_depth': '2', 'slugify': anchor}})
        rendered = md.convert(fold_answers(source[heading.end():]))
        rendered = rendered.replace('<table>', '<div class="table-wrap" tabindex="0" aria-label="学习计划表，可横向滚动"><table>').replace('</table>', '</table></div>')
        body = f'''
<section class="lesson-heading">
<a class="back-link" href="index.html">← 全部精读</a>
<div class="eyebrow"><time datetime="{day}">{day}</time><span class="pill">{esc(topic)}</span></div>
<h1>{esc(title)}</h1>
<p class="lesson-meta">{esc(speaker)} <span aria-hidden="true">·</span> {esc(duration)} <span aria-hidden="true">·</span> 25 分钟学习</p>
<p class="intro">先听懂观点，再拆解语言，最后开口表达。</p>
<div class="source-buttons"><a class="button primary" href="{esc(video)}" target="_blank" rel="noopener noreferrer">▶ 看 TED 视频 <span class="sr-only">（新窗口）</span></a><a class="button secondary" href="{esc(transcript)}" target="_blank" rel="noopener noreferrer">打开英文逐字稿 <span class="sr-only">（新窗口）</span></a></div>
</section>
<details class="contents"><summary>本篇目录 · 6 个部分</summary>{md.toc}</details>
<article class="reading">{rendered}</article>
<div class="end-actions"><a class="button secondary" href="#main">↑ 回到顶部</a><a class="button secondary" href="index.html">浏览全部精读</a></div>
'''
        (OUT / page).write_text(frame(title, body, f'{speaker} 的 {topic}主题 TED 精读：双语导读、语言分析、练习及学习计划。'), encoding='utf-8')
        lessons.append({'day': day, 'title': title, 'speaker': speaker, 'duration': duration, 'topic': topic, 'page': page})
    if not lessons:
        raise ValueError('No dated TED lessons found')
    cards = '\n'.join(f'''<a class="lesson-card" href="{x['page']}"><div class="eyebrow"><time datetime="{x['day']}">{x['day']}</time><span class="pill">{esc(x['topic'])}</span></div><h2>{esc(x['title'])}</h2><p>{esc(x['speaker'])} · {esc(x['duration'])}</p><span class="card-cta">开始精读 <span aria-hidden="true">→</span></span></a>''' for x in lessons)
    body = f'''<section class="home-hero"><span class="eyebrow">每天一篇 · 英语积累</span><h1>听懂一个观点，<br>学会一组表达。</h1><p>用 TED 练习理解、分析与表达。<br>每篇都有双语导读、语言拆解和口头练习。</p><div class="hero-tags"><span>官方来源</span><span>25 分钟学习</span><span>手机友好</span></div></section><section class="lesson-list" aria-labelledby="list-title"><div class="section-heading"><h2 id="list-title">精读目录</h2><span>{len(lessons)} 篇材料</span></div>{cards}</section><aside class="home-note"><h2>如何开始</h2><p>点开一篇材料，先看视频，再按目录选择学习部分。练习答案默认收起，尝试作答后再展开。</p></aside>'''
    (OUT / 'index.html').write_text(frame('学习首页', body, '适配手机的 TED 英语精读材料，包含双语导读、IELTS 表达练习和学习计划。'), encoding='utf-8')
    (OUT / '.nojekyll').touch()
    # Remove only generated dated pages whose Markdown source has been removed.
    valid = {x['page'] for x in lessons}
    for page in OUT.glob('????-??-??.html'):
        if page.name not in valid:
            page.unlink()
    print(f'Built {len(lessons)} lesson(s) and index in {OUT}')


if __name__ == '__main__':
    build()
