from decimal import Decimal

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user, require_roles
from app.common.enums import LifecycleStage, UserRole, VendorStatus
from app.db.session import get_db
from app.models.entities import User, Vendor, VendorCategory
from app.vendors.schemas import (
    VendorCategoryRead,
    VendorCreate,
    VendorListResponse,
    VendorRead,
    VendorSelfRegister,
    VendorUpdate,
)
from app.vendors.service import (
    compliance_badge,
    create_vendor,
    list_vendors,
    set_vendor_status,
    update_vendor,
)

router = APIRouter(tags=["vendors"])


def _vendor_read(vendor: Vendor) -> VendorRead:
    return VendorRead.model_validate(vendor).model_copy(
        update={"compliance_badge": compliance_badge(vendor)}
    )


@router.get("/vendor-categories", response_model=list[VendorCategoryRead])
def get_vendor_categories(
    db: Session = Depends(get_db),
    _: User = Depends(
        require_roles(
            UserRole.admin,
            UserRole.procurement_officer,
            UserRole.manager,
            UserRole.vendor,
        )
    ),
) -> list[VendorCategory]:
    return db.scalars(
        select(VendorCategory)
        .where(VendorCategory.is_active.is_(True))
        .order_by(VendorCategory.name)
    ).all()


@router.get("/vendors", response_model=VendorListResponse)
def get_vendors(
    search: str | None = None,
    status_filter: VendorStatus | None = Query(default=None, alias="status"),
    category_id: int | None = None,
    attributes: str | None = Query(
        default=None,
        description='JSON object for JSONB containment search, e.g. {"iso_certified": true}',
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(
        require_roles(UserRole.admin, UserRole.procurement_officer, UserRole.manager)
    ),
) -> VendorListResponse:
    attribute_filter: dict | None = None
    if attributes:
        try:
            parsed = json.loads(attributes)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="attributes must be a valid JSON object",
            ) from exc
        if not isinstance(parsed, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="attributes must be a JSON object",
            )
        attribute_filter = parsed
    vendors, total = list_vendors(
        db,
        search=search,
        status_filter=status_filter,
        category_id=category_id,
        page=page,
        page_size=page_size,
        attributes=attribute_filter,
    )
    return VendorListResponse(
        items=[_vendor_read(vendor) for vendor in vendors],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("/vendors/self-register", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
def vendor_self_register(
    payload: VendorSelfRegister,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.vendor)),
) -> VendorRead:
    """Vendor self-registration: creates a vendor profile linked to the authenticated vendor user."""
    existing = db.scalar(select(Vendor).where(Vendor.contact_email == current_user.email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A vendor profile already exists for this account",
        )
    vendor_create = VendorCreate(
        name=payload.name,
        legal_name=payload.legal_name,
        category_id=payload.category_id,
        gstin=payload.gstin,
        pan=payload.pan,
        state=payload.state,
        city=payload.city,
        contact_name=f"{current_user.first_name} {current_user.last_name}",
        contact_email=current_user.email,
        contact_phone=payload.contact_phone,
        status=VendorStatus.pending,
        completed_orders_count=0,
        rating=Decimal("0.00"),
        reliability_score=Decimal("0.00"),
        delivery_score=Decimal("0.00"),
        completion_rate=Decimal("0.00"),
        satisfaction_score=Decimal("0.00"),
        compliance_notes=payload.compliance_notes,
    )
    vendor = create_vendor(db, vendor_create, current_user)
    vendor.status = VendorStatus.pending.value
    vendor.lifecycle_stage = LifecycleStage.potential.value
    vendor.is_gstin_verified = False
    vendor.is_pan_verified = False
    db.commit()
    db.refresh(vendor)
    return _vendor_read(vendor)


@router.post("/vendors", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
def post_vendor(
    payload: VendorCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> VendorRead:
    """Manual vendor creation is intentionally disabled.

    Vendors must sign up themselves, then an admin verifies the pending profile.
    Keeping this endpoint explicit makes older clients fail with a clear product
    rule instead of quietly recreating the assisted ERP flow.
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Vendors must self-register before admin verification",
    )


@router.get("/vendors/me", response_model=VendorRead)
def get_my_vendor_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.vendor)),
) -> VendorRead:
    vendor = db.scalar(select(Vendor).where(Vendor.contact_email == current_user.email))
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor profile not found")
    return _vendor_read(vendor)


@router.patch("/vendors/me", response_model=VendorRead)
def patch_my_vendor_profile(
    payload: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.vendor)),
) -> VendorRead:
    vendor = db.scalar(select(Vendor).where(Vendor.contact_email == current_user.email))
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor profile not found")
    original_gstin = vendor.gstin
    original_pan = vendor.pan
    update_vendor(db, vendor, payload, current_user)
    if vendor.gstin != original_gstin or vendor.pan != original_pan:
        vendor.status = VendorStatus.pending.value
        vendor.is_gstin_verified = False
        vendor.is_pan_verified = False
    db.commit()
    db.refresh(vendor)
    return _vendor_read(vendor)


@router.get("/vendors/{vendor_id}", response_model=VendorRead)
def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(
        require_roles(UserRole.admin, UserRole.procurement_officer, UserRole.manager)
    ),
) -> VendorRead:
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return _vendor_read(vendor)


@router.patch("/vendors/{vendor_id}", response_model=VendorRead)
def patch_vendor(
    vendor_id: int,
    payload: VendorUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.admin)),
) -> VendorRead:
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    vendor = update_vendor(db, vendor, payload, actor)
    db.commit()
    db.refresh(vendor)
    return _vendor_read(vendor)


@router.post("/vendors/{vendor_id}/verify", response_model=VendorRead)
def verify_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.admin)),
) -> VendorRead:
    """Admin verifies a self-registered vendor, activating their account on the platform."""
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    if vendor.status == VendorStatus.active.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Vendor is already active"
        )
    vendor.is_gstin_verified = True
    vendor.is_pan_verified = vendor.pan is not None
    vendor = set_vendor_status(db, vendor, VendorStatus.active, actor)
    db.commit()
    db.refresh(vendor)
    return _vendor_read(vendor)


@router.post("/vendors/{vendor_id}/block", response_model=VendorRead)
def block_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.admin)),
) -> VendorRead:
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    vendor = set_vendor_status(db, vendor, VendorStatus.blocked, actor)
    db.commit()
    db.refresh(vendor)
    return _vendor_read(vendor)


@router.post("/vendors/{vendor_id}/unblock", response_model=VendorRead)
def unblock_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.admin)),
) -> VendorRead:
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    vendor = set_vendor_status(db, vendor, VendorStatus.active, actor)
    db.commit()
    db.refresh(vendor)
    return _vendor_read(vendor)
