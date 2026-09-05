"""Test validating all YAML and JSON code snippets in PRD v2.0 against Draft-07 schemas."""

import glob
import json
import os
import re
import unittest
import yaml
import jsonschema


class TestPRDSnippetsSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas = {}
        cls.store = {}
        for p in glob.glob("docs/schemas/*.schema.json"):
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            name = os.path.basename(p).replace(".schema.json", "")
            cls.schemas[name] = d
            cls.store[d.get("$id", name)] = d
            cls.store[os.path.basename(p)] = d

        with open("docs/MACAO_PRD_v2.md", "r", encoding="utf-8") as f:
            cls.lines = f.read().split("\n")

    def get_validator(self, name):
        s = self.schemas[name]
        return jsonschema.Draft7Validator(s, resolver=jsonschema.RefResolver.from_schema(s, store=self.store))

    def get_section(self, a_re, b_re):
        a = b = None
        for i, l in enumerate(self.lines):
            if a is None and re.match(a_re, l):
                a = i
            elif a is not None and re.match(b_re, l):
                b = i
                break
        return "\n".join(self.lines[a:b]) if a is not None and b is not None else ""

    def test_prd_structural_examples(self):
        cases = [
            (r"^### 2\.1 ", r"^### 2\.2 ", "dev_manifest"),
            (r"^### 2\.2 ", r"^### 2\.3 ", "review_manifest"),
            (r"^### 2\.3 ", r"^### 2\.4 ", "vote_result"),
            (r"^### 2\.5 ", r"^## 第三部分", "review_disposition"),
            (r"^### 5\.2 ", r"^### 5\.3 ", "review_context"),
            (r"^## 第十三部分", r"^## 第十四部分", "macao_config"),
        ]
        for a_re, b_re, sch in cases:
            s_text = self.get_section(a_re, b_re)
            matches = re.findall(r"^```(?:yaml|json)\n(.*?)^```", s_text, re.M | re.S)
            self.assertTrue(len(matches) > 0, f"No code block found for {a_re}")
            for f in matches:
                o = yaml.safe_load(f)
                if not o or not isinstance(o, dict):
                    continue
                cand = [o]
                if len(o) == 1 and isinstance(list(o.values())[0], dict):
                    cand.append(list(o.values())[0])
                errors_list = [list(self.get_validator(sch).iter_errors(c)) for c in cand]
                best = min(errors_list, key=len)
                err_msgs = ["/".join(map(str, e.path)) + ": " + e.message for e in best]
                self.assertEqual(len(best), 0, f"PRD snippet {a_re} failed {sch} schema: {err_msgs}")

    def test_prd_aep_envelope_examples(self):
        s_aep = self.get_section(r"^### 2\.4 ", r"^### 2\.5 ")
        matches = re.findall(r"^```json\n(.*?)^```", s_aep, re.M | re.S)
        self.assertTrue(len(matches) >= 8, f"Expected 8 AEP examples, found {len(matches)}")
        for f in matches:
            o = json.loads(f)
            if not isinstance(o, dict) or "type" not in o:
                continue
            errs = list(self.get_validator("aep_envelope").iter_errors(o))
            err_msgs = ["/".join(map(str, e.path)) + ": " + e.message for e in errs]
            self.assertEqual(len(errs), 0, f"AEP snippet {o.get('type')} failed aep_envelope schema: {err_msgs}")

    def test_proposal_and_usecase_disposition_snippets(self):
        """Regression test for Claude A-P1-1/B-P1-1 & Grok P1-1: verify disposition examples in proposal and UC6."""
        val = self.get_validator("review_disposition")
        for p in ["docs/PRD_CHANGE_PROPOSAL_v2.5.md", "docs/usercases/UC6-issue-triage-rework.md"]:
            with open(p, "r", encoding="utf-8") as f:
                t = f.read()
            matches = re.findall(r"^```(?:yaml|json)\n(.*?)^```", t, re.M | re.S)
            found = 0
            for code in matches:
                try:
                    o = yaml.safe_load(code)
                    if isinstance(o, dict) and "disposition_status" in o:
                        found += 1
                        errs = list(val.iter_errors(o))
                        err_msgs = ["/".join(map(str, e.path)) + ": " + e.message for e in errs]
                        self.assertEqual(len(errs), 0, f"Snippet in {p} failed review_disposition schema: {err_msgs}")
                except Exception:
                    pass
            self.assertGreaterEqual(found, 1, f"Expected at least 1 disposition snippet in {p}, found {found}")


    def test_all_usercases_and_proposals_code_snippets(self):
        """Comprehensive fence extraction test for all usercase and proposal markdown documents (Claude A-P2-6)."""
        tested_count = 0
        for p in sorted(glob.glob("docs/usercases/*.md")):
            with open(p, "r", encoding="utf-8") as f:
                t = f.read()
            matches = re.findall(r"^```(?:yaml|json)\n(.*?)^```", t, re.M | re.S)
            for code in matches:
                try:
                    o = yaml.safe_load(code)
                except Exception:
                    continue
                if not isinstance(o, dict):
                    continue
                if "team" in o and "policy" in o:
                    errs = list(self.get_validator("macao_config").iter_errors(o))
                    self.assertEqual(len(errs), 0, f"{p} config failed schema: {errs}")
                    tested_count += 1
                elif "signal" in o and "checkpoint_ref" in o:
                    errs = list(self.get_validator("dev_manifest").iter_errors(o))
                    self.assertEqual(len(errs), 0, f"{p} dev_manifest failed schema: {errs}")
                    tested_count += 1
                elif "disposition_status" in o:
                    errs = list(self.get_validator("review_disposition").iter_errors(o))
                    self.assertEqual(len(errs), 0, f"{p} disposition failed schema: {errs}")
                    tested_count += 1
        self.assertGreaterEqual(tested_count, 3, f"Expected at least 3 usercase schema snippets, found {tested_count}")

    def test_all_templates_code_snippets(self):
        """Verify all YAML/JSON manifest snippets in templates/*.md pass Draft-07 schemas."""
        from macao.core.schema import SchemaValidator
        val = SchemaValidator()
        tested_count = 0
        for p in sorted(glob.glob("templates/*.md")):
            with open(p, "r", encoding="utf-8") as f:
                t = f.read()
            matches = re.findall(r"^```(?:yaml|json)\s*\n(.*?)\n```", t, re.M | re.S)
            for code in matches:
                try:
                    o = yaml.safe_load(code)
                except Exception:
                    continue
                if not isinstance(o, dict):
                    continue
                tested_count += 1
                matched_schema = None
                if "signal" in o and "checkpoint_ref" in o:
                    matched_schema = "dev_manifest"
                elif "disposition_status" in o:
                    matched_schema = "review_disposition"
                elif "override_id" in o:
                    matched_schema = "admin_override"
                elif "reviewer" in o and "vote" in o:
                    matched_schema = "review_manifest"
                elif "type" in o and "payload" in o:
                    matched_schema = "aep_envelope"

                self.assertIsNotNone(matched_schema, f"Snippet in {p} must map to a known schema")
                ok, err = val.validate(matched_schema, o)
                self.assertTrue(ok, f"Snippet in {p} failed {matched_schema}: {err}")
        self.assertGreaterEqual(tested_count, 6, f"Expected at least 6 template snippets, found {tested_count}")


if __name__ == "__main__":
    unittest.main()

