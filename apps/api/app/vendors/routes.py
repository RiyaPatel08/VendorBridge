from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.dependencies import require_roles
from app.common.enums import UserRole, VendorStatus
from app.db.session import get_db
from app.models.entities import User, Vendor, VendorCategory
from app.vendors.schemas import (
    VendorCategoryRead,
    VendorCreate,
    VendorListResponse,
    VendorRead,
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
        require_roles(UserRole.admin, UserRole.procurement_officer, UserRole.manager)
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
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(
        require_roles(UserRole.admin, UserRole.procurement_officer, UserRole.manager)
    ),
) -> VendorListResponse:
    vendors, total = list_vendors(
        db,
        search=search,
        status_filter=status_filter,
        category_id=category_id,
        page=page,
        page_size=page_size,
    )
    return VendorListResponse(
        items=[_vendor_read(vendor) for vendor in vendors],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("/vendors", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
def post_vendor(
    payload: VendorCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.admin, UserRole.procurement_officer)),
) -> VendorRead:
    vendor = create_vendor(db, payload, actor)
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
    actor: User = Depends(require_roles(UserRole.admin, UserRole.procurement_officer)),
) -> VendorRead:
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    vendor = update_vendor(db, vendor, payload, actor)
    db.commit()
    db.refresh(vendor)
    return _vendor_read(vendor)


@router.post("/vendors/{vendor_id}/block", response_model=VendorRead)
def block_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.admin, UserRole.procurement_officer)),
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
    actor: User = Depends(require_roles(UserRole.admin, UserRole.procurement_officer)),
) -> VendorRead:
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    vendor = set_vendor_status(db, vendor, VendorStatus.active, actor)
    db.commit()
    db.refresh(vendor)
    return _vendor_read(vendor)
