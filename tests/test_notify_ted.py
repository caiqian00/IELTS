import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('notify', Path(__file__).parents[1] / 'scripts/notify_ted.py')
notify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(notify)


class NotificationTests(unittest.TestCase):
    def test_mobile_links_and_mention(self):
        body = notify.notification_body({'2026-10-12': '每个孩子都需要支持者'}, '2026-10-12', 'caiqian00')
        self.assertIn('@caiqian00', body)
        self.assertIn('1. [精读首页](https://caiqian00.github.io/IELTS/)', body)
        self.assertIn('2. [今日精读：每个孩子都需要支持者](https://caiqian00.github.io/IELTS/2026-10-12.html)', body)

    def test_old_material_not_mislabeled_today(self):
        body = notify.notification_body({'2026-10-11': '旧材料'}, '2026-10-12', 'caiqian00')
        self.assertNotIn('今日精读', body)
        self.assertIn('精读（2026-10-11）', body)

    def test_manual_run_uses_latest_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);(root/'docs').mkdir()
            for day in ['2026-10-11', '2026-10-12']:
                (root/'docs'/f'{day}.html').write_text('page')
            with patch.object(notify, 'ROOT', root):
                self.assertEqual(notify.changed_pages({}, 'abc'), ['2026-10-12'])


if __name__ == '__main__':
    unittest.main()
