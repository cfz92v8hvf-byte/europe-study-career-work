from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from google_translate import SAFE_MONTHLY_CAP, translate_to_russian


class GoogleTranslateTests(unittest.TestCase):
    def test_sends_only_explicit_text_and_accepts_russian_result(self):
        response = Mock()
        response.read.return_value = '{"data":{"translations":[{"translatedText":"Научный ассистент"}]}}'.encode("utf-8")
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        opener = Mock(return_value=response)

        result = translate_to_russian("Research assistant", monthly_used_characters=10, api_key="test", opener=opener)

        self.assertEqual(result, "Научный ассистент")
        request = opener.call_args.args[0]
        self.assertIn(b"Research+assistant", request.data)
        self.assertIn(b"target=ru", request.data)

    def test_blocks_missing_key_and_monthly_limit(self):
        with self.assertRaisesRegex(RuntimeError, "GOOGLE_TRANSLATE_API_KEY"):
            translate_to_russian("Research assistant", monthly_used_characters=0, api_key="")
        with self.assertRaisesRegex(RuntimeError, "safe monthly free limit"):
            translate_to_russian("Research assistant", monthly_used_characters=SAFE_MONTHLY_CAP, api_key="test")
