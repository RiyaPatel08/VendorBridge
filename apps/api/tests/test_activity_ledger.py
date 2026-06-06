from app.activity.service import append_activity_log, seal_activity_block, verify_activity_integrity
from tests.conftest import get_test_db, reset_db


def test_activity_hash_chain_and_merkle_seal() -> None:
    reset_db()
    db = next(get_test_db())
    try:
        append_activity_log(
            db,
            actor_id=None,
            event_type="test.created",
            entity_type="test",
            entity_id=1,
            summary="First event",
            payload={"step": 1},
        )
        append_activity_log(
            db,
            actor_id=None,
            event_type="test.updated",
            entity_type="test",
            entity_id=1,
            summary="Second event",
            payload={"step": 2},
        )
        block = seal_activity_block(db)
        db.commit()
        assert block is not None
        ok, entries, blocks, message, first_error = verify_activity_integrity(db)
        assert ok is True
        assert entries == 2
        assert blocks == 1
        assert first_error is None
        assert "verified" in message
    finally:
        db.close()
