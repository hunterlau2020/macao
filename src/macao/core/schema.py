"""JSON Schema Validator for MACAO Artifacts and Messages."""

import json
import math
import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import jsonschema


# Locate docs/schemas directory
def get_schemas_dir() -> Path:
    # 1. Environment variable override
    env_dir = os.getenv("MACAO_SCHEMAS_DIR")
    if env_dir and Path(env_dir).is_dir():
        return Path(env_dir).resolve()

    # 2. Package-internal bundled schemas
    pkg_schemas = Path(__file__).resolve().parent.parent / "schemas"
    if pkg_schemas.exists() and pkg_schemas.is_dir():
        return pkg_schemas

    # 3. Traverse upwards to find repository docs/schemas
    current = Path(__file__).resolve()
    for parent in current.parents:
        cand = parent / "docs" / "schemas"
        if cand.exists() and cand.is_dir():
            return cand

    # 4. Fallback to local relative
    return Path("docs/schemas").resolve()


class SchemaValidator:
    """Manages loading, caching, and validation of Draft-07 schemas."""

    _instance: Optional["SchemaValidator"] = None
    _schemas: Dict[str, Dict[str, Any]] = {}
    _schema_store: Dict[str, Dict[str, Any]] = {}

    def __new__(cls) -> "SchemaValidator":
        if cls._instance is None:
            cls._instance = super(SchemaValidator, cls).__new__(cls)
            cls._instance._load_all_schemas()
        return cls._instance

    def _load_all_schemas(self) -> None:
        schema_dir = get_schemas_dir()
        if not schema_dir.exists():
            return

        for path in schema_dir.glob("*.schema.json"):
            name = path.stem.replace(".schema", "")
            try:
                with open(path, "r", encoding="utf-8") as f:
                    schema_data = json.load(f)
                    jsonschema.Draft7Validator.check_schema(schema_data)
                    self._schemas[name] = schema_data
                    if "$id" in schema_data:
                        self._schema_store[schema_data["$id"]] = schema_data
                    self._schema_store[path.name] = schema_data
                    self._schema_store[f"https://macao.dev/schemas/v2.5/{path.name}"] = schema_data
            except Exception as e:
                # Keep loading others
                pass

    def get_schema(self, name: str) -> Optional[Dict[str, Any]]:
        return self._schemas.get(name)

    def validate(self, schema_name: str, instance: Any) -> Tuple[bool, Optional[str]]:
        """Validate an instance against a named schema. Returns (is_valid, error_msg)."""
        schema = self.get_schema(schema_name)
        if schema is None:
            return False, f"Schema '{schema_name}' not found in registry"

        try:
            resolver = jsonschema.RefResolver.from_schema(schema, store=self._schema_store)
            validator = jsonschema.Draft7Validator(schema, resolver=resolver)
            errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
            if errors:
                first_err = errors[0]
                path_str = ".".join(str(p) for p in first_err.path)
                msg = f"Validation failed at '{path_str}': {first_err.message}" if path_str else first_err.message
                return False, msg
            return True, None
        except Exception as e:
            return False, str(e)


# Convenience functions
def validate_dev_manifest(data: Any) -> Tuple[bool, Optional[str]]:
    return SchemaValidator().validate("dev_manifest", data)

def validate_review_manifest(data: Any) -> Tuple[bool, Optional[str]]:
    return SchemaValidator().validate("review_manifest", data)

def validate_vote_result(data: Any) -> Tuple[bool, Optional[str]]:
    return SchemaValidator().validate("vote_result", data)

def validate_review_context(data: Any) -> Tuple[bool, Optional[str]]:
    return SchemaValidator().validate("review_context", data)

def validate_aep_envelope(data: Any) -> Tuple[bool, Optional[str]]:
    return SchemaValidator().validate("aep_envelope", data)

def validate_config(data: Any) -> Tuple[bool, Optional[str]]:
    is_valid, err = SchemaValidator().validate("macao_config", data)
    if not is_valid:
        return False, err
    if not isinstance(data, dict):
        return True, None

    # D-6 Anti-Dominance & Quorum Semantic Validation
    team = data.get("team", {})
    reviewers = team.get("reviewers", [])
    if isinstance(reviewers, list) and reviewers:
        n_seats = len(reviewers)
        weights = []
        for r in reviewers:
            if isinstance(r, dict):
                w = r.get("vote_weight", 1)
                if isinstance(w, int):
                    weights.append((r.get("id", "unknown"), w))
        total_w = sum(w for _, w in weights)

        # 1. Dictator cap: forall i, 3*w_i < 2*W
        for r_id, w in weights:
            if 3 * w >= 2 * total_w:
                return False, f"Dictator cap violation: reviewer '{r_id}' weight {w} violates 3*w_i < 2*W (3*{w}={3*w} >= 2*{total_w}={2*total_w})"

        policy = data.get("policy", {})
        if isinstance(policy, dict):
            # 2. Minimum winning seats bound: 2 <= minimum_winning_seats <= N
            mws = policy.get("minimum_winning_seats")
            if isinstance(mws, int):
                if mws < 2:
                    return False, f"minimum_winning_seats ({mws}) must be at least 2"
                if mws > n_seats:
                    return False, f"minimum_winning_seats ({mws}) cannot exceed number of reviewers ({n_seats})"

            # 3. Seat quorum: >= ceil(2N/3)
            min_sq = math.ceil(2 * n_seats / 3)
            sq = policy.get("seat_quorum_required")
            if isinstance(sq, int) and sq < min_sq:
                return False, f"seat_quorum_required ({sq}) is less than required minimum ceil(2N/3) = {min_sq}"

            # 4. Weight quorum: >= ceil(2W/3)
            min_wq = math.ceil(2 * total_w / 3)
            wq = policy.get("weight_quorum_required")
            if isinstance(wq, int) and wq < min_wq:
                return False, f"weight_quorum_required ({wq}) is less than required minimum ceil(2W/3) = {min_wq}"

            # 5. Dictator cap enabled must be True
            if policy.get("dictator_cap_enabled") is not True:
                return False, "dictator_cap_enabled must be true"

    return True, None


def validate_review_disposition(data: Any) -> Tuple[bool, Optional[str]]:
    return SchemaValidator().validate("review_disposition", data)


def validate_admin_override(data: Any) -> Tuple[bool, Optional[str]]:
    return SchemaValidator().validate("admin_override", data)

