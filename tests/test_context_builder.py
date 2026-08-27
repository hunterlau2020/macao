"""Unit tests for ReviewContextBuilder and review_context.schema.json."""

import unittest
from macao.utils.context_builder import ReviewContextBuilder
from macao.core.schema import validate_review_context


class TestReviewContextBuilder(unittest.TestCase):

    def test_minimal_review_context_builder(self):
        builder = ReviewContextBuilder(
            task_description="Implement rate limiter",
            base_commit="main",
            head_commit="f1a2b3c"
        )
        builder.set_quality_snapshot(passed=10, failed=0, coverage=0.925)
        builder.set_diff_info(
            files_changed=3,
            insertions=120,
            deletions=15,
            files_list=[
                {"path": "src/limiter.py", "status": "added"},
                {"path": "src/config.py", "status": "modified"},
                {"path": "tests/test_limiter.py", "status": "added"}
            ]
        )
        context = builder.build()

        is_valid, err = validate_review_context(context)
        self.assertTrue(is_valid, f"Expected valid review_context, got: {err}")
        self.assertEqual(context["code_changes"]["refs"]["base_commit"], "main")
        self.assertEqual(context["code_changes"]["refs"]["head_commit"], "f1a2b3c")
        self.assertEqual(context["quality_snapshot"]["tests"]["passed"], 10)

    def test_full_review_context_builder(self):
        builder = ReviewContextBuilder(
            task_description="Refactor connection pool",
            base_commit="a1b2c3d",
            head_commit="e4f5g6h"
        )
        builder.set_self_assessment(
            what_was_done="Upgraded pool to threadsafe LRU cache",
            review_focus=["concurrency", "memory_leak"],
            known_limitations=["Tested only with sqlite, not postgres"]
        )
        builder.set_history(
            previous_reviews_count=1,
            previous_feedback=["Fix race condition on close()"]
        )
        context = builder.build()

        is_valid, err = validate_review_context(context)
        self.assertTrue(is_valid, f"Expected valid full review_context, got: {err}")
        self.assertIn("executor_self_assessment", context)
        self.assertIn("history", context)


if __name__ == "__main__":
    unittest.main()
