import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('daily_ted', Path(__file__).parents[1] / 'scripts/daily_ted.py')
daily = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(daily)


class DailyTedTests(unittest.TestCase):
    def setUp(self):
        # Synthetic source and notes exercise validation, not real TED content.
        self.talk = {'title': 'Synthetic practice source', 'duration': 600,
                     'cues': [{'time': i * 60000, 'text': 'Source phrase number ' + str(i)} for i in range(10)]}
        self.notes = {'title_zh': '练习材料',
            'segments': [{'start_seconds': i * 60, 'end_seconds': (i+1) * 60,
                          'heading': '阶段', 'english_summary': 'A distinct original summary.',
                          'chinese_explanation': '解释内容。', 'listening_task': '听出观点。'} for i in range(10)],
            'language': [{'heading': '语言项目', 'analysis': '说明。', 'original_example': 'An original example.',
                          'example_explanation': '中文。', 'usage_and_mistakes': '指出搭配错误。'} for _ in range(10)],
            'argument_analysis': '论证分析。', 'cohesion_analysis': '衔接分析。',
            'pronunciation_practice': '练习建议，未核验音频。',
            'exercises': [{'heading': '练习', 'task': '复述。', 'original_answer': 'A separate original answer.',
                           'answer_explanation': '说明。'} for _ in range(3)],
            'study_steps': [{'minutes': 10, 'task': '观看', 'completion_check': '理解'},
                            {'minutes': 15, 'task': '练习', 'completion_check': '表达'}],
            'review_checklist': ['复习一', '复习二', '复习三', '复习四']}

    def test_valid_contiguous_guide(self):
        daily.validate(self.notes, self.talk)

    def test_rejects_invented_time_or_missing_coverage(self):
        self.notes['segments'][1]['start_seconds'] = 61
        with self.assertRaises(ValueError): daily.validate(self.notes, self.talk)
        self.notes['segments'][1]['start_seconds'] = 60
        self.notes['segments'][-1]['end_seconds'] = 599
        with self.assertRaises(ValueError): daily.validate(self.notes, self.talk)

    def test_rejects_insufficient_video_time(self):
        self.notes['study_steps'][0]['minutes'] = 5
        with self.assertRaises(ValueError): daily.validate(self.notes, self.talk)

    def test_rejects_copyright_overlap(self):
        original = ' '.join('token' + chr(97+i) for i in range(26))
        self.talk['cues'][0]['text'] = original
        self.notes['argument_analysis'] = original
        with self.assertRaisesRegex(ValueError, 'overlap'): daily.validate(self.notes, self.talk)

    def test_rejects_injected_html(self):
        self.notes['language'][0]['analysis'] = '<script>alert(1)</script>'
        with self.assertRaises(ValueError): daily.validate(self.notes, self.talk)

    def test_duplicate_rejected_before_network(self):
        with patch.object(daily, 'fetch') as fetch:
            with self.assertRaises(ValueError):
                daily.load_talk('https://www.ted.com/talks/used_talk', {'used_talk'})
            fetch.assert_not_called()

    def test_non_english_and_short_video_rejected(self):
        video = {'videoData': {'canonicalUrl': 'https://www.ted.com/talks/new_talk', 'duration': 100,
                              'title': 'Example', 'presenterDisplayName': 'Speaker'}}
        def page(data):
            return '<script id="__NEXT_DATA__">' + json.dumps({'props': {'pageProps': data}}) + '</script>'
        with patch.object(daily, 'fetch', return_value=(page(video), 'https://www.ted.com')):
            with self.assertRaisesRegex(ValueError, 'duration'): daily.load_talk(video['videoData']['canonicalUrl'], set())
        video['videoData']['duration'] = 600
        transcript = {'transcriptData': {'translation': {'language': {'internalLanguageCode': 'zh'}}}}
        with patch.object(daily, 'fetch', side_effect=[(page(video), 'https://www.ted.com'), (page(transcript), 'https://www.ted.com')]):
            with self.assertRaisesRegex(ValueError, 'English'): daily.load_talk(video['videoData']['canonicalUrl'], set())

    def test_topic_rotation_and_index_deduplication(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '2026-10-12-example.md').write_text('- **主题**：教育／关系\nhttps://www.ted.com/talks/used_talk')
            (root / '索引.md').write_text('https://www.ted.com/talks/index_only')
            with patch.object(daily, 'LESSONS', root):
                self.assertEqual(daily.history(), ({'used_talk', 'index_only'}, '科技'))

    def test_same_day_rerun_does_not_call_api(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '2026-10-12-example.md').write_text('Existing material')
            with patch.object(daily, 'LESSONS', root), patch('sys.argv', ['daily_ted', '--date', '2026-10-12']), patch.object(daily, 'ask_api') as api:
                daily.main()
                api.assert_not_called()


if __name__ == '__main__':
    unittest.main()
