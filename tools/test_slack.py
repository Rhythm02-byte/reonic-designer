"""Offline checks: python -m unittest discover -s tools -p test_slack.py."""
import contextlib
import io
import unittest
from unittest.mock import patch

import slack


class DigestTests(unittest.TestCase):
    def run_digest(self, board, changelog=None, full=False):
        def fetch(_token, channel, *_args, **_kwargs):
            if channel == "board":
                return board
            return (changelog or []) if channel == "changelog" else []

        out = io.StringIO()
        with patch.object(slack, "token", return_value="offline"), patch.object(slack, "fetch", side_effect=fetch), \
                patch.object(slack.time, "time", return_value=100000), contextlib.redirect_stdout(out):
            result = slack.start("Kian738", full)
        return result, out.getvalue()

    def test_claims_are_complete_and_messages_are_not_repeated(self):
        board = [{"ts": "99990", "text": "🔒 CLAIM tools/ — [Other's agent] since 01:00"},
                 {"ts": "99991", "text": "@Kian738 please pull next"}]
        _, output = self.run_digest(board, [{"ts": "99992", "text": "@Kian738 docs shipped"}])
        self.assertEqual(output.count("please pull next"), 1)
        self.assertEqual(output.count("docs shipped"), 1)
        self.assertEqual(output.count("tools/"), 1)
        self.assertNotIn("🔒 CLAIM", output)

    def test_compact_output_and_full_escape_hatch(self):
        board = [{"ts": str(99900 + i), "text": f"update-{i:02d}"} for i in range(20)]
        _, compact = self.run_digest(board)
        _, full = self.run_digest(board, full=True)
        self.assertNotIn("update-00", compact)
        self.assertIn("12 older messages omitted", compact)
        self.assertIn("update-00", full)
        self.assertNotIn("omitted", full)

    def test_older_mention_still_surfaces(self):
        board = [{"ts": "99900", "text": "@Kian738 action required"}]
        board += [{"ts": str(99901 + i), "text": f"update {i}"} for i in range(9)]
        _, output = self.run_digest(board)
        self.assertEqual(output.count("action required"), 1)

    def test_failed_board_does_not_report_no_claims(self):
        with contextlib.redirect_stderr(io.StringIO()):
            result, output = self.run_digest(None)
        self.assertEqual(result, 1)
        self.assertNotIn("none", output)

    def test_older_decisions_are_kept_in_compact_board(self):
        board = [{"ts": "99900", "text": ":pushpin: Build on next"}]
        board += [{"ts": str(99901 + i), "text": f"update {i}"} for i in range(9)]
        _, output = self.run_digest(board)
        self.assertIn("Build on next", output)

    def test_fetch_paginates_before_replaying_claims(self):
        pages = [{"ok": True, "messages": [{"ts": "2", "text": "🔓 RELEASE tools/"}],
                  "response_metadata": {"next_cursor": "page2"}},
                 {"ok": True, "messages": [{"ts": "1", "text": "🔒 CLAIM tools/ — agent"}]}]
        with patch.object(slack, "channel_id", return_value="C123"), \
                patch.object(slack, "call", side_effect=pages) as call:
            messages = slack.fetch("offline", "board", "12h", paginate=True)
        self.assertEqual(call.call_count, 2)
        self.assertEqual(slack.open_claims(messages), {})

    def test_failed_later_page_discards_incomplete_claim_history(self):
        pages = [{"ok": True, "messages": [{"ts": "2", "text": "unrelated"}],
                  "response_metadata": {"next_cursor": "page2"}},
                 {"ok": False, "error": "ratelimited"}]
        with patch.object(slack, "channel_id", return_value="C123"), \
                patch.object(slack, "call", side_effect=pages):
            self.assertIsNone(slack.fetch("offline", "board", "12h", paginate=True))

    def test_missing_token_is_harmless(self):
        with patch.object(slack, "token", return_value=None), patch.object(slack, "fetch") as fetch, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(slack.start("Kian738"), 0)
        fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
