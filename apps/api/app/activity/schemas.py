from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityLogRead(BaseModel):
    id: int
    actor_id: int | None
    event_type: str
    entity_type: str
    entity_id: int | None
    summary: str
    payload: dict
    previous_hash: str
    entry_hash: str
    block_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LedgerVerificationResult(BaseModel):
    ok: bool
    checked_entries: int
    checked_blocks: int
    message: str
    first_error_log_id: int | None = None
