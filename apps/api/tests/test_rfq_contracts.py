from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.rfqs.contracts import RFQCreateContract


def test_rfq_contract_accepts_valid_hsn_and_line_items() -> None:
    contract = RFQCreateContract(
        title="Office Furniture Procurement Q2",
        category_id=1,
        deadline=datetime.now(UTC) + timedelta(days=7),
        vendor_ids=[1, 2, 3],
        items=[
            {
                "item_name": "Ergonomic chair",
                "hsn_sac": "9403",
                "quantity": "25",
                "unit": "NOS",
                "target_price": "5000.00",
            }
        ],
    )

    assert contract.items[0].hsn_sac == "9403"
    assert contract.vendor_ids == [1, 2, 3]


def test_rfq_contract_rejects_invalid_hsn() -> None:
    with pytest.raises(ValidationError):
        RFQCreateContract(
            title="Office Furniture Procurement Q2",
            category_id=1,
            deadline=datetime.now(UTC) + timedelta(days=7),
            vendor_ids=[1],
            items=[
                {
                    "item_name": "Ergonomic chair",
                    "hsn_sac": "12345",
                    "quantity": "25",
                    "unit": "NOS",
                }
            ],
        )
