#!/usr/bin/env python3
"""Select an official TED source, generate original study notes, then update the index."""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
LESSONS = ROOT / 'TED每日精读'
TOPICS = ['教育', '科技', '环境', '健康', '工作', '城市', '媒体', '文化', '科学', '全球议题']
URL_PATTERN = r'https://www\.ted\.com/talks/([a-z0-9_]+)'
MODEL = os.environ.get('TED_MODEL', 'gpt-5-mini')


def obj(fields: dict) -> dict:
    return {'type': 'object', 'properties': fields, 'required': list(fields), 'additionalProperties': False}


def arr(item: dict) -> dict:
    return {'type': 'array', 'items': item}


STRING = {'type': 'string'}
INTEGER = {'type': 'integer'}
NOTE_SCHEMA = obj({
    'title_zh': STRING,
    'segments': arr(obj({'start_seconds': INTEGER, 'end_seconds': INTEGER, 'heading': STRING,
                         'english_summary': STRING, 'chinese_explanation': STRING, 'listening_task': STRING})),
    'language': arr(obj({'heading': STRING, 'analysis': STRING, 'original_example': STRING,
                        'example_explanation': STRING, 'usage_and_mistakes': STRING})),
    'argument_analysis': STRING,
    'cohesion_analysis': STRING,
    'pronunciation_practice': STRING,
    'exercises': arr(obj({'heading': STRING, 'task': STRING, 'original_answer': STRING, 'answer_explanation': STRING})),
    'study_steps': arr(obj({'minutes': INTEGER, 'task': STRING, 'completion_check': STRING})),
    'review_checklist': arr(STRING),
})


def fetch(url: str) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={'User-Agent': 'IELTS-TED-Study/1.0'})
    with urllib.request.urlopen(req, timeout=45) as response:
        final_url = response.url
        if urllib.parse.urlsplit(final_url).hostname not in {'www.ted.com', 'ted.com'}:
            raise ValueError('TED request redirected outside the official site')
        return response.read().decode('utf-8'), final_url


def page_data(page: str) -> dict:
    match = re.search(r'<script\b[^>]*\bid="__NEXT_DATA__"[^>]*>(.*?)</script>', page, re.DOTALL)
    if not match:
        raise ValueError('Official page data format changed; refusing to guess transcript')
    return json.loads(match.group(1))['props']['pageProps']


def load_talk(url: str, seen: set[str]) -> dict:
    match = re.fullmatch(URL_PATTERN, url)
    if not match or match.group(1) in seen:
        raise ValueError('Invalid or previously used official video URL')
    data = page_data(fetch(url)[0])
    video = data['videoData']
    canonical = video['canonicalUrl']
    if canonical != url or not 360 <= video['duration'] <= 900:
        raise ValueError('Canonical URL or 6–15 minute duration check failed')
    transcript_url = url + '/transcript?language=en'
    transcript_data = page_data(fetch(transcript_url)[0])
    translation = transcript_data['transcriptData']['translation']
    if translation['language']['internalLanguageCode'] != 'en':
        raise ValueError('Official transcript is not English')
    cues = [c for p in translation['paragraphs'] for c in p['cues']]
    if len(cues) < 20 or any(not isinstance(c['time'], int) for c in cues):
        raise ValueError('Missing usable official transcript timestamps')
    if [c['time'] for c in cues] != sorted(c['time'] for c in cues):
        raise ValueError('Transcript timestamps are not chronological')
    return {'url': url, 'transcript_url': transcript_url, 'title': video['title'],
            'speaker': video['presenterDisplayName'], 'duration': video['duration'], 'cues': cues}


def ask_api(key: str, prompt: str, schema: dict, name: str, search: bool = False) -> dict:
    payload = {'model': MODEL, 'input': prompt, 'max_output_tokens': 16000,
               'text': {'format': {'type': 'json_schema', 'name': name, 'schema': schema, 'strict': True}}}
    if search:
        payload['tools'] = [{'type': 'web_search', 'filters': {'allowed_domains': ['ted.com']}}]
        payload['tool_choice'] = 'required'
    req = urllib.request.Request('https://api.openai.com/v1/responses', data=json.dumps(payload).encode(),
                                 headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        # Do not emit raw request bodies or credential-bearing exception details.
        raise RuntimeError(f'OpenAI API returned HTTP {exc.code}; check the GitHub Secret, API billing and model access') from None
    if data.get('status') != 'completed':
        raise RuntimeError('OpenAI response was incomplete; no files will be published')
    output = data.get('output', [])
    if search and not any(x.get('type') == 'web_search_call' for x in output):
        raise RuntimeError('Candidate selection did not execute official-site web search')
    text = ''.join(c['text'] for x in output if x.get('type') == 'message'
                   for c in x.get('content', []) if c.get('type') == 'output_text')
    if not text:
        raise RuntimeError('No structured study output returned')
    print('API call completed:', name, 'total tokens:', data.get('usage', {}).get('total_tokens', 'unknown'))
    return json.loads(text)


def history() -> tuple[set[str], str]:
    seen = set()
    last_topic = None
    paths = sorted(LESSONS.glob('????-??-??-*.md'))
    for path in paths + ([LESSONS / '索引.md'] if (LESSONS / '索引.md').exists() else []):
        source = path.read_text(encoding='utf-8')
        seen.update(re.findall(URL_PATTERN, source))
        if path.name != '索引.md':
            match = re.search(r'^- \*\*主题\*\*：([^／\n；]+)', source, re.MULTILINE)
            if match and match.group(1).strip() in TOPICS:
                last_topic = match.group(1).strip()
    next_topic = TOPICS[(TOPICS.index(last_topic) + 1) % len(TOPICS)] if last_topic else TOPICS[0]
    return seen, next_topic


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)*", text.lower())


def validate(notes: dict, talk: dict) -> None:
    title = notes['title_zh']
    if not 2 <= len(title) <= 36 or not re.search(r'[\u4e00-\u9fff]', title) or re.search(r'[/\\<>|\n]', title):
        raise ValueError('Invalid short Chinese title')
    if not 8 <= len(notes['segments']) <= 18 or not 8 <= len(notes['language']) <= 16:
        raise ValueError('Expected detailed segments and at least eight language analyses')
    previous = 0
    allowed_starts = {c['time'] // 1000 for c in talk['cues']} | {0}
    if notes['segments'][0]['start_seconds'] != 0:
        raise ValueError('Guide must start at the beginning')
    for segment in notes['segments']:
        start, end = segment['start_seconds'], segment['end_seconds']
        if start != previous or start not in allowed_starts or not start < end <= talk['duration']:
            raise ValueError('Guide timestamps must be contiguous and based on official cues')
        previous = end
    if previous != talk['duration']:
        raise ValueError('Guide must cover the full video')
    if not 2 <= len(notes['exercises']) <= 4 or not 3 <= len(notes['review_checklist']) <= 7:
        raise ValueError('Missing exercises or next-day review')
    if any(not isinstance(x['minutes'], int) or x['minutes'] <= 0 for x in notes['study_steps']):
        raise ValueError('Invalid learning step duration')
    if not notes['study_steps'] or notes['study_steps'][0]['minutes'] * 60 < talk['duration']:
        raise ValueError('First study step must allow enough time to watch the full video')
    if not 20 <= sum(x['minutes'] for x in notes['study_steps']) <= 30:
        raise ValueError('Study plan must total 20–30 minutes')
    strings = []
    def collect(value):
        if isinstance(value, str):
            if not value.strip() or '<' in value or 'https://' in value or 'http://' in value:
                raise ValueError('Model notes must be nonempty plain text without HTML or invented links')
            strings.append(value)
        elif isinstance(value, dict):
            for item in value.values(): collect(item)
        elif isinstance(value, list):
            for item in value: collect(item)
    collect(notes)
    # Conservative overlap check: count copied runs of six or more English words.
    # This cannot replace editorial judgement, but rejects extensive verbatim copying.
    source_words = words(' '.join(c['text'] for c in talk['cues']))
    source_grams = {tuple(source_words[i:i+6]) for i in range(len(source_words)-5)}
    overlap = len(words(talk['title']))
    for text in strings:
        token = words(text); matched = set()
        for i in range(len(token)-5):
            if tuple(token[i:i+6]) in source_grams:
                matched.update(range(i, i+6))
        overlap += len(matched)
    if overlap > 25:
        raise ValueError('Conservative source-overlap budget exceeded; refusing to publish')


def clean(text: str) -> str:
    # Model fields are plain text. Escape Markdown syntax so they cannot inject headings or links.
    return re.sub(r'([\\`*_{}\[\]<>#|])', r'\\\1', html.escape(text, quote=False)).strip()


def clock(seconds: int) -> str:
    return f'{seconds // 60:02}:{seconds % 60:02}'


def render(notes: dict, talk: dict, day: str, topic: str) -> str:
    out = [f'# {day}｜{clean(notes["title_zh"])}', '',
           '面向 IELTS Academic 总分 7.5 的原创学习材料。', '', '## 一、视频与官方来源', '',
           f'- **英文标题**：{talk["title"]}', f'- **讲者**：{talk["speaker"]}',
           f'- **时长**：{talk["duration"] // 60} 分 {talk["duration"] % 60:02} 秒（官方页面数据）',
           f'- **主题**：{topic}', f'- **官方视频**：{talk["url"]}',
           f'- **官方交互式英文逐字稿**：{talk["transcript_url"]}', '',
           '已核验 TED 官方页面与英文逐字稿；以下内容为原创概述，不是全文翻译。除英文标题外，不主动引用原文；完整逐字稿请通过官方链接阅读。',
           '时间范围根据官方字幕坐标整理；不同播放器的片头可能造成少量偏移。本次未核验音频，语音部分仅提供练习建议。', '',
           '## 二、按时间顺序的双语内容导读', '']
    for x in notes['segments']:
        out += [f'### {clock(x["start_seconds"])}–{clock(x["end_seconds"])}｜{clean(x["heading"])}', '',
                '**English guide:** ' + clean(x['english_summary']), '',
                '**中文解释：**' + clean(x['chinese_explanation']), '',
                '**跟听任务：**' + clean(x['listening_task']), '']
    out += ['## 三、深入语言分析', '', '以下英文例句均为原创；按 IELTS 口语与学术写作的不同语域使用。', '']
    for i, x in enumerate(notes['language'], 1):
        out += [f'### {i}. {clean(x["heading"])}', '', '**分析：**' + clean(x['analysis']), '',
                '**原创例句：**' + clean(x['original_example']), '',
                '**中文解释：**' + clean(x['example_explanation']), '',
                '**搭配、介词、语域、辨析与误用：**' + clean(x['usage_and_mistakes']), '']
    out += ['## 四、论证、衔接与跟读建议', '', '### 论证路线', '', clean(notes['argument_analysis']), '',
            '### 衔接分析', '', clean(notes['cohesion_analysis']), '',
            '### 重音与语调练习（未核验音频）', '', clean(notes['pronunciation_practice']), '',
            '## 五、练习与参考答案', '']
    for x in notes['exercises']:
        out += ['### ' + clean(x['heading']), '', clean(x['task']), '',
                '**原创参考答案：**' + clean(x['original_answer']), '',
                '**中文说明：**' + clean(x['answer_explanation']), '']
    total = sum(x['minutes'] for x in notes['study_steps'])
    out += [f'## 六、今日 {total} 分钟学习步骤与次日复习', '',
            '| 时间 | 动作 | 完成标志 |', '|---|---|---|']
    elapsed = 0
    for x in notes['study_steps']:
        out += [f'| {elapsed}–{elapsed+x["minutes"]} 分钟 | {clean(x["task"]).replace(chr(10), " ")} | {clean(x["completion_check"]).replace(chr(10), " ")} |']
        elapsed += x['minutes']
    out += ['', '**次日复习清单：**', ''] + ['- [ ] ' + clean(x) for x in notes['review_checklist']]
    out += ['', '**下次主题：**' + TOPICS[(TOPICS.index(topic)+1) % len(TOPICS)] + '。', '',
            '由 AI 根据官方来源生成并通过程序校验；练习不构成官方 IELTS 评分。', '']
    return '\n'.join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', help='Override Shanghai date for a manual backfill: YYYY-MM-DD')
    args = parser.parse_args()
    day = args.date or datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()
    date.fromisoformat(day)
    LESSONS.mkdir(exist_ok=True)
    if list(LESSONS.glob(day + '-*.md')):
        print(f'{day}: lesson already exists; skipping generation and API charges')
        return
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        raise RuntimeError('Set the OPENAI_API_KEY GitHub Actions Secret before generating a new lesson')
    seen, topic = history()
    selection = ask_api(key,
        f'Browse TED official site for five distinct TED Talks on {topic} suitable for IELTS Academic 7.5. '
        'Each must last 6–15 minutes and have an official English transcript. '
        'Use live web search restricted to ted.com. Return only canonical https://www.ted.com/talks/slug URLs. '
        'Exclude all these previously used slugs: ' + json.dumps(sorted(seen)),
        obj({'urls': arr(STRING)}), 'ted_candidates', search=True)
    talk = None
    for url in selection['urls'][:5]:
        try:
            talk = load_talk(url, seen)
            break
        except (ValueError, KeyError, TypeError, urllib.error.URLError):
            print('Candidate rejected by official-source/duration/transcript/duplicate checks')
    if talk is None:
        raise RuntimeError('No new official TED source passed validation; existing site remains unchanged')
    spec = (ROOT / 'automation' / 'TED每日精读任务.md').read_text(encoding='utf-8')
    prompt = f'''根据以下任务要求和已经核验的官方数据，生成中文为主的 IELTS Academic 7.5 精读。
任务要求：{spec}
今天日期：{day}；主题：{topic}。
返回结构化数据，所有文字字段是普通文本，不含 HTML、网址或 Markdown 标题。
不要直接引用逐字稿的任何英文句子，也不要把整篇内容逐句翻译。使用原创分段释义和原创例句。
segments 包含 8–18 段，覆盖整个视频，从 start_seconds=0 起到 duration 结束，连续无空隙。
除 0 和最后结束时间外，每个分段起点必须选自官方 cue 的 time 整秒（time // 1000）；上一段结束等于下一段起点。
每段英文概述 2–3 句，中文解释 2–4 句，说明内容作用；不要杜撰数据。
language 包含 10–12 项，覆盖句法、词汇、固定搭配、介词与语域、近义辨析和误用。
每项必须有原创英文例句、中文解释及具体常见错误；关键句法用自己的例句说明，不复制来源。
论证分析区分个人经历、意见与研究证据。衔接分析给出原创 IELTS 可迁移表达。
未听取音频，pronunciation_practice 必须明确仅为练习建议，不能声称测得讲者重音或语调。
exercises 包含复述、造句和口语练习三项，含原创英文参考答案和中文说明。
study_steps 合计 20–30 分钟，观看完整视频的步骤至少分配足够时长；review_checklist 包含 4–6 条。
材料内容扎实、可读，不以空泛鼓励代替分析。
已核验的视频与官方英文逐字稿（仅供理解，不得全文重现）：
{json.dumps(talk, ensure_ascii=False)}'''
    notes = ask_api(key, prompt, NOTE_SCHEMA, 'ted_study_notes')
    validate(notes, talk)
    destination = LESSONS / (day + '-' + notes['title_zh'] + '.md')
    if destination.exists():
        raise RuntimeError('Refusing to overwrite an existing lesson')
    source = render(notes, talk, day, topic)
    index = LESSONS / '索引.md'
    old_index = index.read_text(encoding='utf-8') if index.exists() else '# TED 每日精读索引\n\n| 日期 | 标题 | 主题 | 官方视频 | 精读材料 |\n|---|---|---|---|---|\n'
    row = f'| {day} | {notes["title_zh"]}（{talk["speaker"]}） | {topic} | [TED 官方视频]({talk["url"]}) | [阅读材料]({destination.name}) |'
    lines = old_index.splitlines()
    table_end = max(i for i, line in enumerate(lines) if line.startswith('|')) + 1
    lines.insert(table_end, row)
    next_topic = TOPICS[(TOPICS.index(topic)+1) % len(TOPICS)]
    updated = re.sub(r'下一主题：[^。\n]+。', '下一主题：' + next_topic + '。', '\n'.join(lines)) + '\n'
    destination.write_text(source, encoding='utf-8')
    index.write_text(updated, encoding='utf-8')
    print('Generated and validated:', destination.name, '| topic:', topic, '| official source:', talk['url'])


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, KeyError, TypeError, urllib.error.URLError) as exc:
        print('Daily TED generation failed:', str(exc), file=sys.stderr)
        sys.exit(1)
