from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import VendorStatus
from app.core.config import settings
from app.models.entities import (
    Budget,
    Quotation,
    RFQItem,
    Vendor,
)

MONEY = Decimal("0.01")
SCORE = Decimal("0.01")


def money(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def score(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(SCORE, rounding=ROUND_HALF_UP)


def now_utc() -> datetime:
    return datetime.now(UTC)


def calculate_line_totals(
    quantity: Decimal, unit_price: Decimal, gst_percent: Decimal
) -> tuple[Decimal, Decimal, Decimal]:
    subtotal = money(quantity * unit_price)
    gst = money(subtotal * gst_percent / Decimal("100"))
    return subtotal, gst, money(subtotal + gst)


def lifecycle_weight(stage: str) -> Decimal:
    weights = {
        "potential": Decimal("40"),
        "emerging": Decimal("55"),
        "verified": Decimal("72"),
        "trusted": Decimal("88"),
        "preferred": Decimal("100"),
    }
    return weights.get(stage, Decimal("40"))


def compliance_score(vendor: Vendor) -> Decimal:
    if vendor.status == VendorStatus.blocked.value:
        return Decimal("0")
    value = Decimal("30")
    if vendor.status == VendorStatus.active.value:
        value += Decimal("25")
    if vendor.is_gstin_verified:
        value += Decimal("25")
    if vendor.pan and vendor.is_pan_verified:
        value += Decimal("20")
    return min(value, Decimal("100"))


def best_value_breakdown(
    *,
    quotation: Quotation,
    vendor: Vendor,
    min_total: Decimal,
    max_delivery: int,
    max_payment_terms: int,
) -> dict[str, float]:
    price_score = (
        Decimal("100") if quotation.grand_total == 0 else (min_total / quotation.grand_total) * 100
    )
    delivery_score = (
        Decimal("100")
        if max_delivery <= 0
        else Decimal(max(0, max_delivery - quotation.delivery_days + 1))
        / Decimal(max_delivery + 1)
        * 100
    )
    rating_score = (Decimal(vendor.rating) / Decimal("5")) * 100
    payment_score = (
        Decimal("100")
        if max_payment_terms <= 0
        else Decimal(quotation.payment_terms_days) / Decimal(max_payment_terms) * 100
    )
    compliance = compliance_score(vendor)
    final = (
        price_score * Decimal("0.35")
        + delivery_score * Decimal("0.20")
        + rating_score * Decimal("0.20")
        + compliance * Decimal("0.15")
        + payment_score * Decimal("0.10")
    )
    return {
        "price_score": float(score(min(price_score, Decimal("100")))),
        "delivery_score": float(score(min(delivery_score, Decimal("100")))),
        "vendor_rating_score": float(score(min(rating_score, Decimal("100")))),
        "compliance_score": float(score(compliance)),
        "payment_terms_score": float(score(min(payment_score, Decimal("100")))),
        "final_score": float(score(final)),
    }


def budget_impact(db: Session, po_amount: Decimal, department: str = "Procurement") -> dict:
    budget = db.scalar(select(Budget).where(Budget.department == department))
    if budget is None:
        return {
            "department": department,
            "budget": 0.0,
            "spent": 0.0,
            "po_amount": float(money(po_amount)),
            "remaining_after": float(money(-po_amount)),
            "health": "red",
        }
    remaining_after = money(budget.amount - budget.spent_amount - po_amount)
    threshold = budget.amount * Decimal("0.25")
    health = (
        "green" if remaining_after >= threshold else "yellow" if remaining_after >= 0 else "red"
    )
    return {
        "department": department,
        "budget": float(money(budget.amount)),
        "spent": float(money(budget.spent_amount)),
        "po_amount": float(money(po_amount)),
        "remaining_after": float(remaining_after),
        "health": health,
    }


def risk_assessment(
    *,
    db: Session,
    selected_quote: Quotation,
    vendor: Vendor,
    quote_count: int,
) -> tuple[str, dict, list[str]]:
    submitted_quotes = db.scalars(
        select(Quotation).where(
            Quotation.rfq_id == selected_quote.rfq_id,
            Quotation.status.in_(["submitted", "selected", "rejected"]),
        )
    ).all()
    lowest_total = min(
        (quote.grand_total for quote in submitted_quotes), default=selected_quote.grand_total
    )
    average_total = (
        sum((quote.grand_total for quote in submitted_quotes), Decimal("0")) / len(submitted_quotes)
        if submitted_quotes
        else selected_quote.grand_total
    )

    verification = compliance_score(vendor)
    delivery_reliability = Decimal(vendor.delivery_score)
    history = lifecycle_weight(vendor.lifecycle_stage)
    inventory = Decimal("100")
    price_abnormality = Decimal("100")
    if selected_quote.grand_total > lowest_total * Decimal("1.10"):
        price_abnormality -= Decimal("25")
    if selected_quote.grand_total < average_total * Decimal("0.70"):
        price_abnormality -= Decimal("20")

    weighted = (
        verification * Decimal("0.25")
        + delivery_reliability * Decimal("0.20")
        + inventory * Decimal("0.20")
        + history * Decimal("0.15")
        + price_abnormality * Decimal("0.20")
    )
    tier = "low" if weighted >= 75 else "medium" if weighted >= 50 else "high"

    reasons: list[str] = []
    if vendor.status != VendorStatus.active.value:
        reasons.append("Vendor is not active")
    if not vendor.is_gstin_verified:
        reasons.append("GSTIN is not verified")
    if quote_count <= 1:
        reasons.append("Only one quotation received")
    if selected_quote.grand_total > lowest_total:
        reasons.append("Selected vendor is not the lowest price")
    if selected_quote.best_value_score < Decimal("65"):
        reasons.append("Best Value Score is below policy threshold")

    breakdown = {
        "verification": float(score(verification)),
        "delivery_reliability": float(score(delivery_reliability)),
        "inventory_availability": float(score(inventory)),
        "vendor_history": float(score(history)),
        "price_abnormality": float(score(price_abnormality)),
        "weighted_score": float(score(weighted)),
    }
    return tier, breakdown, reasons


def tax_split(subtotal: Decimal, gst_total: Decimal, vendor_state: str) -> dict[str, Decimal]:
    if vendor_state.strip().lower() == settings.company_state.strip().lower():
        half = money(gst_total / Decimal("2"))
        return {
            "cgst_total": half,
            "sgst_total": money(gst_total - half),
            "igst_total": Decimal("0.00"),
        }
    return {
        "cgst_total": Decimal("0.00"),
        "sgst_total": Decimal("0.00"),
        "igst_total": money(gst_total),
    }


def sum_required_quantity(db: Session, rfq_id: int) -> Decimal:
    items = db.scalars(select(RFQItem).where(RFQItem.rfq_id == rfq_id)).all()
    return sum((item.quantity for item in items), Decimal("0"))
