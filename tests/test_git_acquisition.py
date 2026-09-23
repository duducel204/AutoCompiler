import unittest
from unittest.mock import patch

from src.autocompiler.git_acquisition import plan_git_capability


class GitAcquisitionBenchmarkTests(unittest.TestCase):
    @patch("src.autocompiler.git_acquisition.platform.system", return_value="Windows")
    @patch("src.autocompiler.git_acquisition.shutil.which")
    @patch("src.autocompiler.git_acquisition.detect_command")
    def test_missing_git_becomes_authorized_acquisition(self, detect, which, _system):
        detect.return_value.detected = False
        which.return_value = r"C:\\Windows\\winget.exe"
        plan = plan_git_capability()
        self.assertEqual(plan["action"], "acquire")
        self.assertEqual(plan["provider"], "Git.Git")
        self.assertTrue(plan["authorization_required"])
        self.assertTrue(plan["mutates_environment"])
        self.assertIn("Git.Git", plan["command"])
        self.assertTrue(plan["rollback"])

    @patch("src.autocompiler.git_acquisition.detect_command")
    def test_existing_git_is_reused_without_acquisition(self, detect):
        detect.return_value.detected = True
        detect.return_value.path = r"C:\\Program Files\\Git\\cmd\\git.exe"
        detect.return_value.version = "git version 2.x"
        plan = plan_git_capability()
        self.assertEqual(plan["action"], "reuse")
        self.assertFalse(plan["authorization_required"])
        self.assertFalse(plan["mutates_environment"])

    @patch("src.autocompiler.git_acquisition.platform.system", return_value="Windows")
    @patch("src.autocompiler.git_acquisition.shutil.which", return_value=None)
    @patch("src.autocompiler.git_acquisition.detect_command")
    def test_missing_git_and_provider_stays_unresolved(self, detect, _which, _system):
        detect.return_value.detected = False
        plan = plan_git_capability()
        self.assertEqual(plan["action"], "unresolved")
        self.assertFalse(plan["mutates_environment"])


if __name__ == "__main__":
    unittest.main()
