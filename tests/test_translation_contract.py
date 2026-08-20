from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from translation_contract import build_request, parse_response


class TranslationContractTests(unittest.TestCase):
    def test_request_preserves_original_and_official_url(self):
        request = build_request(original_title="Research assistant role", source_url="https://euraxess.ec.europa.eu/jobs/1")
        self.assertIn("Research assistant role", request)
        self.assertIn("euraxess.ec.europa.eu", request)

    def test_accepts_only_russian_json_title(self):
        self.assertEqual(parse_response('{"title_ru":"Вакансия ассистента исследователя"}'), "Вакансия ассистента исследователя")
        with self.assertRaises(ValueError):
            parse_response('{"title_ru":"Research assistant"}')


if __name__ == "__main__":
    unittest.main()
