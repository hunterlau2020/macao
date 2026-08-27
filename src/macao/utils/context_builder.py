"""Builder for REVIEW_REQUEST review_context complying with PRD §5.2 and review_context.schema.json."""

from typing import Dict, Any, Optional, List
from macao.core.schema import validate_review_context


class ReviewContextBuilder:
    """Builds valid, schema-compliant review_context payloads."""

    def __init__(
        self,
        task_description: str,
        base_commit: str,
        head_commit: str,
        workspace_path: str = ".",
        dev_checkpoint_path: str = ".macao/.dev.yml"
    ):
        self.task_description = task_description
        self.base_commit = base_commit
        self.head_commit = head_commit
        self.workspace_path = workspace_path
        self.dev_checkpoint_path = dev_checkpoint_path

        # Defaults for required blocks
        self.review_focus: List[str] = ["logic_correctness", "edge_cases", "security"]
        self.remote_name: str = "origin"
        self.fetch_policy: str = "auto"
        self.diff_command: str = f"git diff {base_commit}..{head_commit}"
        self.summary: Dict[str, int] = {
            "files_changed": 1,
            "insertions": 20,
            "deletions": 5
        }
        self.files_list: List[Dict[str, Any]] = [
            {"path": "src/main.py", "status": "modified"}
        ]
        self.tests_passed: int = 1
        self.tests_failed: int = 0
        self.coverage: float = 0.85  # ratio between 0 and 1
        self.lint_errors: int = 0
        self.security_issues: int = 0

        # Optional blocks
        self.executor_self_assessment: Optional[Dict[str, Any]] = None
        self.history: Optional[Dict[str, Any]] = None
        self.references: Optional[Dict[str, Any]] = None

    def populate_from_dev_manifest(self, dev_data: Dict[str, Any]) -> "ReviewContextBuilder":
        """Populates quality snapshot and self-assessment from real .dev.yml data."""
        dev_block = dev_data.get("development", {})
        qm = dev_block.get("quality_metrics", {})
        if qm:
            tests = qm.get("tests", {})
            passed = tests.get("passed", 1 if qm.get("tests_passed") else 0)
            failed = tests.get("failed", 0)
            cov = qm.get("coverage", 0.85)
            self.set_quality_snapshot(passed=passed, failed=failed, coverage=cov)

        self_assess = dev_data.get("self_assessment", {})
        if self_assess:
            what_was_done = self_assess.get("summary", "Code development completed")
            focus = self_assess.get("review_focus", self.review_focus)
            limitations = self_assess.get("known_limitations", [])
            self.set_self_assessment(what_was_done, focus, limitations)

        return self

    def set_diff_info(self, files_changed: int, insertions: int, deletions: int, files_list: Optional[List[Dict[str, Any]]] = None) -> "ReviewContextBuilder":
        self.summary = {
            "files_changed": files_changed,
            "insertions": insertions,
            "deletions": deletions
        }
        if files_list is not None:
            self.files_list = files_list
        return self

    def set_quality_snapshot(
        self,
        passed: int,
        failed: int,
        coverage: float = 0.85,
        lint_errors: int = 0,
        security_issues: int = 0
    ) -> "ReviewContextBuilder":
        self.tests_passed = passed
        self.tests_failed = failed
        self.coverage = coverage if coverage <= 1.0 else coverage / 100.0
        self.lint_errors = lint_errors
        self.security_issues = security_issues
        return self

    def set_self_assessment(self, what_was_done: str, review_focus: List[str], known_limitations: Optional[List[str]] = None) -> "ReviewContextBuilder":
        self.executor_self_assessment = {
            "what_was_done": what_was_done,
            "review_focus": review_focus,
            "known_limitations": known_limitations or []
        }
        return self

    def set_history(self, previous_reviews_count: int, previous_feedback: List[str]) -> "ReviewContextBuilder":
        self.history = {
            "previous_reviews": previous_reviews_count,
            "previous_feedback": previous_feedback
        }
        return self

    def build(self) -> Dict[str, Any]:
        """Constructs and validates review_context against Schema."""
        context: Dict[str, Any] = {
            "dev_checkpoint": {
                "path": self.dev_checkpoint_path
            },
            "repository": {
                "workspace_path": self.workspace_path,
                "remote_name": self.remote_name,
                "fetch_policy": self.fetch_policy
            },
            "task_info": {
                "description": self.task_description,
                "review_focus": self.review_focus
            },
            "code_changes": {
                "refs": {
                    "base_commit": self.base_commit,
                    "head_commit": self.head_commit
                },
                "diff_command": self.diff_command,
                "summary": self.summary,
                "files_list": self.files_list
            },
            "quality_snapshot": {
                "tests": {
                    "passed": self.tests_passed,
                    "failed": self.tests_failed,
                    "coverage": self.coverage
                },
                "static_analysis": {
                    "lint_errors": self.lint_errors,
                    "security_issues": self.security_issues
                }
            }
        }

        if self.executor_self_assessment:
            context["executor_self_assessment"] = self.executor_self_assessment
        if self.history:
            context["history"] = self.history
        if self.references:
            context["references"] = self.references

        is_valid, err = validate_review_context(context)
        if not is_valid:
            raise ValueError(f"Generated review_context is invalid: {err}")

        return context
