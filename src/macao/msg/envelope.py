"""AEP/1.0 Message Envelope Creation and Validation (PRD §2.4)."""

import uuid
import datetime
from typing import Dict, Any, List, Union, Tuple, Optional

from macao.core.types import MessageType
from macao.core.schema import validate_aep_envelope


class AEPEnvelope:
    """Helper for constructing and validating standard AEP/1.0 message envelopes."""

    PROTOCOL = "AEP/1.0"

    @classmethod
    def generate_message_id(cls) -> str:
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
        rand_suffix = str(uuid.uuid4().int)[:4].zfill(4)
        return f"msg-{date_str}-{rand_suffix}"

    @classmethod
    def create(
        cls,
        msg_type: Union[MessageType, str],
        from_agent: str,
        to_agent: Union[str, List[str]],
        payload: Dict[str, Any],
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Constructs a compliant AEP message dictionary."""
        type_val = msg_type.value if isinstance(msg_type, MessageType) else str(msg_type)
        msg = {
            "protocol": cls.PROTOCOL,
            "message_id": message_id or cls.generate_message_id(),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "type": type_val,
            "from": from_agent,
            "to": to_agent,
            "payload": payload,
        }
        is_valid, error = validate_aep_envelope(msg)
        if not is_valid:
            raise ValueError(f"Invalid AEP message envelope: {error}")
        return msg

    @classmethod
    def parse(cls, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validates envelope structure."""
        return validate_aep_envelope(data)
