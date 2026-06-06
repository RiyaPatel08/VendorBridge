from app.vendors.service import derive_lifecycle_stage
from app.vendors.validators import is_valid_gstin, is_valid_hsn_sac, is_valid_pan


def test_india_procurement_validators() -> None:
    assert is_valid_gstin("24INFRA1234F1Z5")
    assert not is_valid_gstin("24BAD")
    assert is_valid_pan("INFRA1234F")
    assert not is_valid_pan("1234")
    assert is_valid_hsn_sac("9403")
    assert is_valid_hsn_sac("998346")
    assert is_valid_hsn_sac("12345678")
    assert not is_valid_hsn_sac("12345")


def test_lifecycle_stage_derivation() -> None:
    assert derive_lifecycle_stage(0).value == "potential"
    assert derive_lifecycle_stage(1).value == "emerging"
    assert derive_lifecycle_stage(5).value == "verified"
    assert derive_lifecycle_stage(20).value == "trusted"
    assert derive_lifecycle_stage(100).value == "preferred"
