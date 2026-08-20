from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import dashboard


class DashboardTests(unittest.TestCase):
    def test_displays_isolated_translation_limit_without_credentials(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            db_path = root / "queue.sqlite3"
            db = sqlite3.connect(db_path)
            db.execute("CREATE TABLE candidates (status TEXT)")
            db.execute("CREATE TABLE translation_usage (usage_day TEXT PRIMARY KEY, characters_used INTEGER NOT NULL)")
            db.execute("INSERT INTO translation_usage VALUES (date('now'), 42)")
            db.commit()
            output = root / "index.html"
            with patch.object(dashboard, "connect", return_value=db), patch.object(dashboard, "OUT", output), patch.object(dashboard, "SOURCE_HEALTH", root / "none.json"):
                dashboard.main()
            page = output.read_text(encoding="utf-8")
            self.assertIn("MyMemory: 42 из 4000 символов", page)
            self.assertIn("публикация недоступна", page)

    def test_displays_zero_when_read_only_queue_has_no_usage_table(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            db = sqlite3.connect(root / "queue.sqlite3")
            db.execute("CREATE TABLE candidates (status TEXT)")
            db.commit()
            output = root / "index.html"
            with patch.object(dashboard, "connect", return_value=db), patch.object(dashboard, "OUT", output), patch.object(dashboard, "SOURCE_HEALTH", root / "none.json"):
                dashboard.main()
            self.assertIn("MyMemory: 0 из 4000 символов", output.read_text(encoding="utf-8"))
