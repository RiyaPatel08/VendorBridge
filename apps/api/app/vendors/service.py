from fastapi import HTTPException, status
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.activity.service import append_activity_log
from app.common.enums import LifecycleStage, VendorStatus
from app.models.entities import User, Vendor, VendorCategory
from app.vendors.schemas import VendorCreate, VendorUpdate
from app.vendors.validators import is_valid_gstin, is_valid_pan, normalize_gstin, normalize_pan


def derive_lifecycle_stage(completed_orders_count: int) -> LifecycleStage:
    if completed_orders_count >= 100:
        return LifecycleStage.preferred
    if completed_orders_count >= 20:
        return LifecycleStage.trusted
    if completed_orders_count >= 5:
        return LifecycleStage.verified
    if completed_orders_count >= 1:
        return LifecycleStage.emerging
    return LifecycleStage.potential


def compliance_badge(vendor: Vendor) -> str:
    if vendor.status == VendorStatus.blocked.value:
        return "blocked"
    if vendor.is_gstin_verified and (vendor.pan is None or vendor.is_pan_verified):
        return "compliant"
    return "needs_review"


def ensure_category(db: Session, category_id: int) -> VendorCategory:
    category = db.get(VendorCategory, category_id)
    if category is None or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vendor category"
        )
    return category


def _validate_procurement_ids(gstin: str, pan: str | None) -> tuple[str, str | None, bool, bool]:
    normalized_gstin = normalize_gstin(gstin)
    normalized_pan = normalize_pan(pan)
    if not is_valid_gstin(normalized_gstin):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid GSTIN format"
        )
    if normalized_pan is not None and not is_valid_pan(normalized_pan):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid PAN format"
        )
    return normalized_gstin, normalized_pan, True, normalized_pan is not None


def build_vendor_query(
    *,
    search: str | None,
    status_filter: VendorStatus | None,
    category_id: int | None,
) -> Select[tuple[Vendor]]:
    query = select(Vendor)
    if search:
        like = f"%{search.strip()}%"
        query = query.where(
            or_(
                Vendor.name.ilike(like),
                Vendor.gstin.ilike(like),
                Vendor.contact_email.ilike(like),
                Vendor.city.ilike(like),
            )
        )
    if status_filter:
        query = query.where(Vendor.status == status_filter.value)
    if category_id:
        query = query.where(Vendor.category_id == category_id)
    return query.order_by(Vendor.name.asc())


def create_vendor(db: Session, payload: VendorCreate, actor: User) -> Vendor:
    ensure_category(db, payload.category_id)
    gstin, pan, gst_verified, pan_verified = _validate_procurement_ids(payload.gstin, payload.pan)
    if db.scalar(select(Vendor).where(Vendor.gstin == gstin)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="GSTIN already exists")
    lifecycle_stage = derive_lifecycle_stage(payload.completed_orders_count)
    vendor = Vendor(
        name=payload.name.strip(),
        legal_name=payload.legal_name.strip() if payload.legal_name else None,
        category_id=payload.category_id,
        gstin=gstin,
        pan=pan,
        state=payload.state.strip(),
        city=payload.city.strip(),
        contact_name=payload.contact_name.strip(),
        contact_email=str(payload.contact_email).lower(),
        contact_phone=payload.contact_phone.strip(),
        status=payload.status.value,
        lifecycle_stage=lifecycle_stage.value,
        completed_orders_count=payload.completed_orders_count,
        rating=payload.rating,
        reliability_score=payload.reliability_score,
        delivery_score=payload.delivery_score,
        completion_rate=payload.completion_rate,
        satisfaction_score=payload.satisfaction_score,
        is_gstin_verified=gst_verified,
        is_pan_verified=pan_verified,
        compliance_notes=payload.compliance_notes,
        created_by_id=actor.id,
    )
    db.add(vendor)
    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="vendor.created",
        entity_type="vendor",
        entity_id=vendor.id,
        summary=f"Vendor {vendor.name} created",
        payload={
            "gstin": vendor.gstin,
            "status": vendor.status,
            "lifecycle_stage": vendor.lifecycle_stage,
        },
    )
    return vendor


def update_vendor(db: Session, vendor: Vendor, payload: VendorUpdate, actor: User) -> Vendor:
    data = payload.model_dump(exclude_unset=True)
    if "category_id" in data and data["category_id"] is not None:
        ensure_category(db, data["category_id"])
    if "gstin" in data and data["gstin"] is not None:
        gstin = normalize_gstin(data["gstin"])
        if not is_valid_gstin(gstin):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid GSTIN format"
            )
        duplicate = db.scalar(select(Vendor).where(Vendor.gstin == gstin, Vendor.id != vendor.id))
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="GSTIN already exists")
        data["gstin"] = gstin
        data["is_gstin_verified"] = True
    if "pan" in data:
        pan = normalize_pan(data["pan"])
        if pan is not None and not is_valid_pan(pan):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid PAN format"
            )
        data["pan"] = pan
        data["is_pan_verified"] = pan is not None
    if "completed_orders_count" in data and data["completed_orders_count"] is not None:
        data["lifecycle_stage"] = derive_lifecycle_stage(data["completed_orders_count"]).value
    if "status" in data and data["status"] is not None:
        data["status"] = data["status"].value

    for field, value in data.items():
        setattr(vendor, field, value)
    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="vendor.updated",
        entity_type="vendor",
        entity_id=vendor.id,
        summary=f"Vendor {vendor.name} updated",
        payload={"changed_fields": sorted(data.keys()), "status": vendor.status},
    )
    return vendor


def set_vendor_status(
    db: Session, vendor: Vendor, status_value: VendorStatus, actor: User
) -> Vendor:
    vendor.status = status_value.value
    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type=f"vendor.{status_value.value}",
        entity_type="vendor",
        entity_id=vendor.id,
        summary=f"Vendor {vendor.name} marked {status_value.value}",
        payload={"status": vendor.status},
    )
    return vendor


def list_vendors(
    db: Session,
    *,
    search: str | None,
    status_filter: VendorStatus | None,
    category_id: int | None,
    page: int,
    page_size: int,
) -> tuple[list[Vendor], int]:
    query = build_vendor_query(search=search, status_filter=status_filter, category_id=category_id)
    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0
    vendors = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return vendors, total


def seed_category(db: Session, name: str, code: str) -> VendorCategory:
    category = db.scalar(select(VendorCategory).where(VendorCategory.code == code))
    if category:
        return category
    category = VendorCategory(name=name, code=code, is_active=True)
    db.add(category)
    db.flush()
    return category
