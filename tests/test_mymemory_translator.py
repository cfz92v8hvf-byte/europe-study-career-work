from pathlib import Path
import sqlite3
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from mymemory_translator import SAFE_DAILY_CAP, translate_en_title_to_russian, used_today


class MyMemoryTranslatorTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")

    def test_translates_short_title_and_records_only_success(self):
        response = Mock()
        response.read.return_value = '{"responseData":{"translatedText":"Научный ассистент","match":0.85},"responseStatus":200}'.encode("utf-8")
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        opener = Mock(return_value=response)

        self.assertEqual(translate_en_title_to_russian(self.db, "Research assistant", opener=opener), "Научный ассистент")
        self.assertEqual(used_today(self.db), len("Research assistant"))
        self.assertIn("langpair=en%7Cru", opener.call_args.args[0].full_url)

    def test_blocks_daily_limit_and_low_quality_without_counting(self):
        self.db.execute("CREATE TABLE translation_usage (usage_day TEXT PRIMARY KEY, characters_used INTEGER NOT NULL)")
        self.db.execute("INSERT INTO translation_usage VALUES (date('now'), ?)", (SAFE_DAILY_CAP,))
        self.db.commit()
        with self.assertRaisesRegex(RuntimeError, "safe daily free limit"):
            translate_en_title_to_russian(self.db, "Research assistant")

        fresh = sqlite3.connect(":memory:")
        response = Mock()
        response.read.return_value = '{"responseData":{"translatedText":"Research assistant","match":0.2},"responseStatus":200}'.encode("utf-8")
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        with self.assertRaisesRegex(ValueError, "review threshold"):
            translate_en_title_to_russian(fresh, "Research assistant", opener=Mock(return_value=response))
        self.assertEqual(used_today(fresh), 0)
