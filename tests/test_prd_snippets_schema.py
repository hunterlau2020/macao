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
            d = json.load(open(p))
            name = os.path.basename(p).replace(".schema.json", "")
            cls.schemas[name] = d
            cls.store[d.get("$id", name)] = d
            cls.store[os.path.basename(p)] = d

        cls.lines = open("docs/MACAO_PRD_v2.md").read().split("\n")

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


if __name__ == "__main__":
    unittest.main()
