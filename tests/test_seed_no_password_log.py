"""
Test that seed script does not log demo password in clear text.
Addresses CodeQL alert: py/clear-text-logging-sensitive-data
"""

import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestSeedPasswordSecurity:
    """Test that demo password is not logged in clear text"""

    def test_seed_summary_does_not_log_password(self, capsys):
        """Verify that the summary print does not output the demo password value
        in clear text. Should print emails but reference password via env var name."""
        from scripts.seed_demo_data import DEMO_ACCOUNTS, _print_summary

        sentinel_password = "SENTINEL_TEST_PASSWORD_DO_NOT_LOG"

        # Temporarily replace DEMO_PASSWORD for testing
        import scripts.seed_demo_data as seed_module

        original_password = seed_module.DEMO_PASSWORD
        seed_module.DEMO_PASSWORD = sentinel_password

        try:
            _print_summary(DEMO_ACCOUNTS)
            captured = capsys.readouterr()
            stdout = captured.out

            # Password value must NOT appear in output
            assert (
                sentinel_password not in stdout
            ), f"Password value leaked in output: {stdout}"

            # Emails MUST appear in output
            for account in DEMO_ACCOUNTS:
                assert (
                    account["email"] in stdout
                ), f"Email {account['email']} not found in output: {stdout}"

            # Role MUST appear in output
            assert "student" in stdout, f"Role 'student' not found in output: {stdout}"
            assert "tutor" in stdout, f"Role 'tutor' not found in output: {stdout}"
            assert "parent" in stdout, f"Role 'parent' not found in output: {stdout}"

            # Reference to env var MUST appear (indicate password comes from env)
            assert (
                "DEMO_PASSWORD" in stdout or "env" in stdout.lower()
            ), f"No reference to DEMO_PASSWORD or env var found: {stdout}"

        finally:
            # Restore original password
            seed_module.DEMO_PASSWORD = original_password
