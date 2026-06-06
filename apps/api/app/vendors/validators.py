import re

GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
HSN_SAC_PATTERN = re.compile(r"^[0-9]{4}([0-9]{2})?([0-9]{2})?$")


def normalize_gstin(value: str) -> str:
    return value.strip().upper()


def normalize_pan(value: str | None) -> str | None:
    return value.strip().upper() if value else None


def is_valid_gstin(value: str) -> bool:
    return bool(GSTIN_PATTERN.fullmatch(normalize_gstin(value)))


def is_valid_pan(value: str | None) -> bool:
    return value is not None and bool(PAN_PATTERN.fullmatch(normalize_pan(value) or ""))


def is_valid_hsn_sac(value: str) -> bool:
    return bool(HSN_SAC_PATTERN.fullmatch(value.strip()))
