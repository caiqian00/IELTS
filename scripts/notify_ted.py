#!/usr/bin/env python3
"""Send an update notification through an assigned GitHub Issue after Pages is ready."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://caiqian00.github.io/IELTS/'


def changed_pages(event: dict, sha: str) -> list[str]:
    before = event.get('before', '')
    if before and before != '0' * 40:
        args = ['git', 'diff', '--name-only', before, sha, '--', 'TED每日精读', 'docs']
        result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=True)
        paths = result.stdout.splitlines()
        dates = set()
        for path in paths:
            match = re.fullmatch(r'docs/(\d{4}-\d{2}-\d{2})\.html', path)
            if not match:
                match = re.match(r'TED每日精读/(\d{4}-\d{2}-\d{2})-.+\.md$', path)
            if match and (ROOT / 'docs' / (match.group(1) + '.html')).is_file():
                dates.add(match.group(1))
        if dates:
            return sorted(dates, reverse=True)
    # A manual test, CSS update or index update links to the latest available lesson.
    existing = sorted(ROOT.glob('docs/????-??-??.html'), reverse=True)
    if not existing:
        return []
    return [existing[0].stem]


def page_titles(days: list[str]) -> dict[str, str]:
    titles = {}
    for day in days:
        files = list((ROOT / 'TED每日精读').glob(day + '-*.md'))
        if len(files) != 1:
            raise ValueError('Expected exactly one source lesson for ' + day)
        heading = files[0].read_text(encoding='utf-8').splitlines()[0]
        titles[day] = heading.removeprefix('# ').split('｜', 1)[-1].strip()
    return titles


def notification_body(titles: dict[str, str], today: str, owner: str) -> str:
    lines = [f'@{owner}，精读网页有更新，以下链接已确认可以阅读。', '',
             f'1. [精读首页]({BASE})']
    for number, (day, title) in enumerate(titles.items(), 2):
        label = '今日精读' if day == today else f'精读（{day}）'
        title = re.sub(r'[\[\]\r\n]', '', title)
        lines.append(f'{number}. [{label}：{title}]({BASE}{day}.html)')
    return '\n'.join(lines) + '\n'


def site_matches(paths: list[str], sha: str) -> bool:
    for path in paths:
        expected = hashlib.sha256((ROOT / 'docs' / path).read_bytes()).digest()
        req = urllib.request.Request(BASE + path + '?v=' + sha,
                                     headers={'Cache-Control': 'no-cache', 'User-Agent': 'TED-update-check/1.0'})
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                if response.status != 200 or hashlib.sha256(response.read()).digest() != expected:
                    return False
        except urllib.error.URLError:
            return False
    return True


def github(method: str, repo: str, route: str, token: str, payload: dict | None = None):
    req = urllib.request.Request('https://api.github.com/repos/' + repo + '/' + route,
        method=method, data=json.dumps(payload).encode() if payload is not None else None,
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'Content-Type': 'application/json', 'X-GitHub-Api-Version': '2022-11-28'})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'GitHub notification API returned HTTP {exc.code}') from None


def main() -> None:
    repo = os.environ['GITHUB_REPOSITORY']
    owner = repo.split('/', 1)[0]
    sha = os.environ['GITHUB_SHA']
    token = os.environ['GH_TOKEN']
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    days = changed_pages(event, sha)
    if not days:
        print('No lesson remains after this update; skipping reading notification')
        return
    titles = page_titles(days)
    marker = f'TED 精读更新 · {sha[:12]}'
    # Exact commit identity makes workflow reruns idempotent.
    page = 1
    while True:
        issues = github('GET', repo, f'issues?state=all&per_page=100&page={page}', token)
        if any(x['title'] == marker for x in issues):
            print('Notification already sent for this commit; skipping')
            return
        if len(issues) < 100:
            break
        page += 1
    paths = ['index.html', 'assets/styles.css'] + [day + '.html' for day in days]
    for attempt in range(30):
        if site_matches(paths, sha):
            break
        if attempt == 29:
            raise RuntimeError('Pages did not publish matching content; no success notification was sent')
        print('Waiting for the matching Pages content...', flush=True)
        time.sleep(10)
    today = datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()
    issue = github('POST', repo, 'issues', token,
                   {'title': marker, 'body': notification_body(titles, today, owner), 'assignees': [owner]})
    print('Notification issued:', issue['html_url'])
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
            summary.write('已验证 Pages 更新并发送 GitHub 通知：' + issue['html_url'] + '\n')


if __name__ == '__main__':
    try:
        main()
    except (KeyError, ValueError, RuntimeError, urllib.error.URLError, subprocess.CalledProcessError) as exc:
        print('TED update notification failed:', str(exc), file=sys.stderr)
        sys.exit(1)
