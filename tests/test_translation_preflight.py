from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from translation_preflight import main


class TranslationPreflightTests(unittest.TestCase):
    def test_accepts_isolated_keyless_review_translator_without_provider_call(self):
        self.assertEqual(main(), 0)
