# PROOF: [L2/インフラ] <- mekhane/ergasterion/typos/test_integration.py S2→プロンプト言語が必要→test_integration が担う
import sys
import unittest
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from typos_integrate import SkillAdapter


# PURPOSE: Test integration の実装
class TestIntegration(unittest.TestCase):
    # PURPOSE: setUp をセットアップする
    def setUp(self):
        # Setup staging dir
        self.staging_dir = Path(__file__).parent / "staging"
        self.staging_dir.mkdir(exist_ok=True)
        self._created_files: list[str] = []

    # PURPOSE: テスト後に生成されたファイルを自動削除する
    def tearDown(self):
        for filepath in self._created_files:
            p = Path(filepath)
            if p.exists():
                p.unlink(missing_ok=True)

    # PURPOSE: Test the full workflow via SkillAdapter
    def test_skill_adapter_workflow(self):
        """Test the full workflow via SkillAdapter."""

        try:
            # 1. Generate checking file naming
            import time

            slug = f"integration_test_adapter_{int(time.time())}"
            role = "Tester"
            goal = "Verify adapter"
            constraints = ["Pass validation"]

            filepath = SkillAdapter.create_draft(slug, role, goal, constraints=constraints)
            self._created_files.append(filepath)
            print(f"DEBUG: Created file at {filepath}")
            self.assertTrue(Path(filepath).exists())
            self.assertIn(slug, str(filepath))

            # 2. Match
            print("DEBUG: Executing find_prompt...")
            matches = SkillAdapter.find_prompt("verify adapter")
            print(f"DEBUG: Matches found: {len(matches)}")
            self.assertTrue(len(matches) > 0)

            # Check if our file is in the matches
            match_names = [m["name"] for m in matches]
            self.assertIn(Path(filepath).stem, match_names)
            # self.assertIn("Verify adapter", matches[0]["preview"]) # Preview check is loose

            # 3. Match Fail
            no_matches = SkillAdapter.find_prompt(
                "completely unrelated query for non-existent prompt"
            )
            self.assertEqual(len(no_matches), 0)
        except Exception:  # noqa: BLE001
            import traceback

            traceback.print_exc()
            raise


if __name__ == "__main__":
    unittest.main()
