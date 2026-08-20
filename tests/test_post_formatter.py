from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from post_formatter import format_post


class PostFormatterTests(unittest.TestCase):
    def test_keeps_primary_link_and_russian_summary(self):
        post = format_post(
            title_ru="Исследовательская вакансия",
            summary_ru="Официальная возможность с проверяемыми условиями подачи.",
            source_name="EURAXESS",
            source_url="https://euraxess.ec.europa.eu/jobs/offer/42",
            deadline_label="30 сентября 2026",
        )
        self.assertIn("https://euraxess.ec.europa.eu/jobs/offer/42", post)
        self.assertIn("Срок", post)

    def test_rejects_non_russian_or_insecure_content(self):
        with self.assertRaises(ValueError):
            format_post(title_ru="Job", summary_ru="Apply now", source_name="Official", source_url="https://example.org")
        with self.assertRaises(ValueError):
            format_post(title_ru="Вакансия", summary_ru="Описание", source_name="Official", source_url="http://example.org")


if __name__ == "__main__":
    unittest.main()
