"""AEP/1.1 Message Envelope Creation and Validation (PRD §2.4)."""

import json
import uuid
import datetime
from typing import Dict, Any, List, Union, Tuple, Optional

from macao.core.types import AEPType
from macao.core.schema import validate_aep_envelope


class AEPEnvelope:
    """Helper for constructing and validating standard AEP/1.1 message envelopes."""

    PROTOCOL = "AEP/1.1"
    MAX_MESSAGE_BYTES = 16384
    MAX_INLINE_FIELD_BYTES = 2048

    @classmethod
    def generate_message_id(cls) -> str:
        """
        Generates schema-compliant msg-YYYYMMDD-<16-digit-random> string with zero collision probability.
        Uses 16 decimal digits (10^16 space) conforming strictly to ^msg-[0-9]{8}-[0-9]{3,}$.
        """
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
        rand_suffix = str(uuid.uuid4().int)[:16].zfill(16)
        return f"msg-{date_str}-{rand_suffix}"

    @classmethod
    def validate_budget(cls, msg: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validates envelope and field byte budgets."""
        try:
            serialized = json.dumps(msg, ensure_ascii=False).encode("utf-8")
        except Exception as e:
            return False, f"JSON serialization error: {e}"
        if len(serialized) > cls.MAX_MESSAGE_BYTES:
            return False, f"AEP message exceeds max budget of {cls.MAX_MESSAGE_BYTES} bytes (got {len(serialized)} bytes)"

        payload = msg.get("payload", {})
        if isinstance(payload, dict):
            for k, v in payload.items():
                if isinstance(v, str):
                    b_len = len(v.encode("utf-8"))
                    if b_len > cls.MAX_INLINE_FIELD_BYTES:
                        return False, f"Payload field '{k}' exceeds inline limit of {cls.MAX_INLINE_FIELD_BYTES} bytes (got {b_len} bytes)"
                elif isinstance(v, list):
                    for idx, item in enumerate(v):
                        if isinstance(item, str):
                            b_len = len(item.encode("utf-8"))
                            if b_len > cls.MAX_INLINE_FIELD_BYTES:
                                return False, f"Payload field '{k}[{idx}]' exceeds inline limit of {cls.MAX_INLINE_FIELD_BYTES} bytes (got {b_len} bytes)"
        return True, None

    @classmethod
    def create(
        cls,
        msg_type: Union[AEPType, str],
        from_agent: str,
        to_agent: Union[str, List[str]],
        payload: Dict[str, Any],
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates a schema-compliant AEP/1.1 envelope."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        m_id = message_id or cls.generate_message_id()
        type_val = msg_type.value if isinstance(msg_type, AEPType) else str(msg_type)
        msg = {
            "protocol": cls.PROTOCOL,
            "message_id": m_id,
            "timestamp": now_iso,
            "type": type_val,
            "from": from_agent,
            "to": to_agent,
            "payload": payload,
        }
        is_valid, error = validate_aep_envelope(msg)
        if not is_valid:
            raise ValueError(f"Invalid AEP message envelope: {error}")
        is_budget_ok, budget_err = cls.validate_budget(msg)
        if not is_budget_ok:
            raise ValueError(budget_err)
        return msg

    @classmethod
    def parse(cls, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validates envelope structure and byte budget."""
        is_valid, error = validate_aep_envelope(data)
        if not is_valid:
            return False, error
        return cls.validate_budget(data)
