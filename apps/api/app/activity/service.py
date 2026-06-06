from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import ActivityLog, ActivityLogBlock

GENESIS_HASH = "0" * 64


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    return str(value)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def canonical_log_payload(
    *,
    actor_id: int | None,
    event_type: str,
    entity_type: str,
    entity_id: int | None,
    summary: str,
    payload: dict[str, Any],
    previous_hash: str,
    created_at: datetime,
) -> str:
    canonical = {
        "actor_id": actor_id,
        "created_at": _as_utc(created_at).isoformat(),
        "entity_id": entity_id,
        "entity_type": entity_type,
        "event_type": event_type,
        "payload": payload,
        "previous_hash": previous_hash,
        "summary": summary,
    }
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=_json_default)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def calculate_entry_hash(
    *,
    actor_id: int | None,
    event_type: str,
    entity_type: str,
    entity_id: int | None,
    summary: str,
    payload: dict[str, Any],
    previous_hash: str,
    created_at: datetime,
) -> str:
    return sha256_hex(
        canonical_log_payload(
            actor_id=actor_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
            payload=payload,
            previous_hash=previous_hash,
            created_at=created_at,
        )
    )


def append_activity_log(
    db: Session,
    *,
    actor_id: int | None,
    event_type: str,
    entity_type: str,
    entity_id: int | None,
    summary: str,
    payload: dict[str, Any] | None = None,
) -> ActivityLog:
    previous = db.scalar(select(ActivityLog).order_by(ActivityLog.id.desc()).limit(1))
    previous_hash = previous.entry_hash if previous else GENESIS_HASH
    created_at = datetime.now(UTC)
    safe_payload = payload or {}
    entry_hash = calculate_entry_hash(
        actor_id=actor_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        payload=safe_payload,
        previous_hash=previous_hash,
        created_at=created_at,
    )
    log = ActivityLog(
        actor_id=actor_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        payload=safe_payload,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
        created_at=created_at,
    )
    db.add(log)
    db.flush()
    return log


def _merkle_root(hashes: list[str]) -> str:
    if not hashes:
        return GENESIS_HASH
    level = hashes[:]
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        level = [sha256_hex(level[i] + level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


def seal_activity_block(db: Session, block_size: int = 8) -> ActivityLogBlock | None:
    latest_block = db.scalar(select(ActivityLogBlock).order_by(ActivityLogBlock.id.desc()).limit(1))
    already_sealed_until = latest_block.end_log_id if latest_block else 0
    pending_logs = db.scalars(
        select(ActivityLog)
        .where(ActivityLog.id > already_sealed_until)
        .order_by(ActivityLog.id.asc())
        .limit(block_size)
    ).all()
    if not pending_logs:
        return None

    previous_block_hash = latest_block.block_hash if latest_block else GENESIS_HASH
    merkle_root = _merkle_root([log.entry_hash for log in pending_logs])
    block_hash = sha256_hex(
        json.dumps(
            {
                "end_log_id": pending_logs[-1].id,
                "merkle_root": merkle_root,
                "previous_block_hash": previous_block_hash,
                "start_log_id": pending_logs[0].id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    block = ActivityLogBlock(
        start_log_id=pending_logs[0].id,
        end_log_id=pending_logs[-1].id,
        merkle_root=merkle_root,
        previous_block_hash=previous_block_hash,
        block_hash=block_hash,
    )
    db.add(block)
    db.flush()
    return block


def verify_activity_integrity(db: Session) -> tuple[bool, int, int, str, int | None]:
    logs = db.scalars(select(ActivityLog).order_by(ActivityLog.id.asc())).all()
    previous_hash = GENESIS_HASH
    for log in logs:
        if log.previous_hash != previous_hash:
            return False, len(logs), 0, "Hash chain previous_hash mismatch", log.id
        expected = calculate_entry_hash(
            actor_id=log.actor_id,
            event_type=log.event_type,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            summary=log.summary,
            payload=log.payload,
            previous_hash=log.previous_hash,
            created_at=log.created_at,
        )
        if expected != log.entry_hash:
            return False, len(logs), 0, "Entry hash mismatch", log.id
        previous_hash = log.entry_hash

    blocks = db.scalars(select(ActivityLogBlock).order_by(ActivityLogBlock.id.asc())).all()
    previous_block_hash = GENESIS_HASH
    for block in blocks:
        block_logs = [log for log in logs if block.start_log_id <= log.id <= block.end_log_id]
        if block.previous_block_hash != previous_block_hash:
            return False, len(logs), len(blocks), "Block hash chain mismatch", block.start_log_id
        if _merkle_root([log.entry_hash for log in block_logs]) != block.merkle_root:
            return False, len(logs), len(blocks), "Merkle root mismatch", block.start_log_id
        expected_block_hash = sha256_hex(
            json.dumps(
                {
                    "end_log_id": block.end_log_id,
                    "merkle_root": block.merkle_root,
                    "previous_block_hash": block.previous_block_hash,
                    "start_log_id": block.start_log_id,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        if expected_block_hash != block.block_hash:
            return False, len(logs), len(blocks), "Block hash mismatch", block.start_log_id
        previous_block_hash = block.block_hash

    return True, len(logs), len(blocks), "Ledger integrity verified", None
