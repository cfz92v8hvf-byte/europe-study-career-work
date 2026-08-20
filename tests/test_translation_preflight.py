from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from translation_preflight import main
class TranslationPreflightTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_blocks_without_dedicated_credential(self):
        with self.assertRaisesRegex(RuntimeError, "TRANSLATION_API_KEY"): main()
    @patch.dict(os.environ, {"TRANSLATION_API_KEY": "configured"}, clear=True)
    def test_accepts_present_credential_without_calling_provider(self):
        self.assertEqual(main(), 0)
if __name__ == "__main__": unittest.main()
