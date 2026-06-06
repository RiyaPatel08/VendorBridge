from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.activity.routes import router as activity_router
from app.approvals.routes import router as approvals_router
from app.auth.routes import router as auth_router
from app.core.config import settings
from app.invoices.routes import router as invoices_router
from app.notifications_routes import router as notifications_router
from app.purchase_orders.routes import router as purchase_orders_router
from app.quotations.routes import router as quotations_router
from app.reports.routes import router as dashboard_router
from app.rfqs.routes import router as rfqs_router
from app.vendors.routes import router as vendors_router

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.backend_cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", tags=["system"])
def health_check() -> dict:
    return {"status": "ok", "service": settings.app_name}


api_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(vendors_router, prefix=api_prefix)
app.include_router(rfqs_router, prefix=api_prefix)
app.include_router(quotations_router, prefix=api_prefix)
app.include_router(approvals_router, prefix=api_prefix)
app.include_router(purchase_orders_router, prefix=api_prefix)
app.include_router(invoices_router, prefix=api_prefix)
app.include_router(activity_router, prefix=api_prefix)
app.include_router(dashboard_router, prefix=api_prefix)
app.include_router(notifications_router, prefix=api_prefix)
