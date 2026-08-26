"""JSON Schema Validator for MACAO Artifacts and Messages."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import jsonschema


# Locate docs/schemas directory
def get_schemas_dir() -> Path:
    current = Path(__file__).resolve()
    # Traverse upwards to find docs/schemas
    for parent in current.parents:
        cand = parent / "docs" / "schemas"
        if cand.exists() and cand.is_dir():
            return cand
    # Fallback to local relative
    return Path("docs/schemas").resolve()


class SchemaValidator:
    """Manages loading, caching, and validation of Draft-07 schemas."""

    _instance: Optional["SchemaValidator"] = None
    _schemas: Dict[str, Dict[str, Any]] = {}

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
            validator = jsonschema.Draft7Validator(schema)
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
    return SchemaValidator().validate("macao_config", data)
