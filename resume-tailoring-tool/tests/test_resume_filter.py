import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from resume_filter import (
    analyze_job,
    skill_appears_in_text,
    score_entry_bullets,
    select_best_bullets,
)

class ResumeFilterTests(unittest.TestCase):
    def test_alias_matching(self):
        self.assertTrue(skill_appears_in_text("AI", "Worked with artificial intelligence tools"))
        self.assertTrue(skill_appears_in_text("Microsoft Copilot", "Used Copilot for research"))

    def test_job_weighting(self):
        job = {
            "Summary": ["Python role"],
            "Responsibilities": ["Use Python for automation"],
            "Qualifications": ["Python experience required"],
        }
        skills, weights = analyze_job(job, ["Python", "automation"])
        self.assertEqual(skills, ["Python", "automation"])
        self.assertEqual(weights["Python"], 6)
        self.assertEqual(weights["automation"], 2)

    def test_bullet_scoring(self):
        entry = {
            "bullets": [
                "Built Python automation tools.",
                "Helped customers.",
                "Used ChatGPT with Python.",
            ]
        }
        weights = {"Python": 5, "automation": 3, "ChatGPT": 2}
        scored = score_entry_bullets(
            entry, ["Python", "automation", "ChatGPT"], weights
        )
        self.assertEqual(scored[0]["score"], 8)
        self.assertEqual(scored[1]["score"], 7)
        self.assertEqual(scored[2]["score"], 0)

    def test_select_best_bullets(self):
        entry = {
            "bullets": [
                "General communication.",
                "Built Python tools.",
                "Created automation with Python.",
            ]
        }
        chosen = select_best_bullets(
            entry,
            ["Python", "automation"],
            {"Python": 3, "automation": 2},
            limit=1,
        )
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0]["score"], 5)

if __name__ == "__main__":
    unittest.main()
