import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from resume_filter import run_pipeline, skill_appears_in_text
ROOT = Path(__file__).resolve().parents[1]
class PipelineTests(unittest.TestCase):
    def run_quiet(self, *args, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return run_pipeline(*args, **kwargs)
    def test_boundaries(self):
        self.assertFalse(skill_appears_in_text("Java", "JavaScript"))
        self.assertFalse(skill_appears_in_text("AI", "Maintained"))
        self.assertTrue(skill_appears_in_text("C++", "C++ developer"))
    def test_exports_preserve_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = self.run_quiet(ROOT / "resume.txt", ROOT / "job_description.txt", tmp)
            self.assertGreater(report["match_percentage"], 0)
            original = (ROOT / "resume.txt").read_text()
            for entries in report["selected_entries"].values():
                for entry in entries:
                    for bullet in entry["selected_bullets"]:
                        self.assertIn(bullet["bullet"], original)
            saved = json.loads((Path(tmp) / "job_match_report.json").read_text())
            self.assertEqual(saved["skill_weights"], report["skill_weights"])
            self.assertEqual(len(list(Path(tmp).iterdir())), 4)
    def test_no_match_preserves_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp) / "job.txt"
            job.write_text("Friendly colleague needed.")
            report = self.run_quiet(ROOT / "resume.txt", job, Path(tmp) / "out")
            self.assertEqual(report["job_skills"], [])
            self.assertIn("Study Dashboard | Python, Excel", report["tailored_resume"]["Projects"])
    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            self.run_quiet(ROOT / "resume.txt", ROOT / "job_description.txt", "unused", bullet_limit=0)
    def test_missing_input(self):
        with self.assertRaises(FileNotFoundError):
            self.run_quiet(ROOT / "missing.txt", ROOT / "job_description.txt", "unused")
