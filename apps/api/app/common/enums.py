from enum import StrEnum


class UserRole(StrEnum):
    admin = "admin"
    procurement_officer = "procurement_officer"
    vendor = "vendor"
    manager = "manager"
    finance_manager = "finance_manager"


class VendorStatus(StrEnum):
    pending = "pending"
    active = "active"
    blocked = "blocked"


class LifecycleStage(StrEnum):
    potential = "potential"
    emerging = "emerging"
    verified = "verified"
    trusted = "trusted"
    preferred = "preferred"


class RFQStatus(StrEnum):
    draft = "draft"
    sent = "sent"
    closed = "closed"
    cancelled = "cancelled"


class QuotationStatus(StrEnum):
    draft = "draft"
    submitted = "submitted"
    selected = "selected"
    rejected = "rejected"


class ApprovalStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
