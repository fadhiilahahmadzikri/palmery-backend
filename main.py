import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from src.api.v1.config import router as config_router
from src.api.v1.records import router as records_router
from src.api.v1.harvesters import router as harvesters_router
from src.api.v1.locations import router as locations_router
from src.api.v1.payroll import router as payroll_router
from src.api.v1.system import router as system_router
from src.api.v1.dashboard import router as dashboard_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Palm Oil Harvest Premium Calculator",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.warning("IntegrityError on %s %s: %s", request.method, request.url.path, exc.orig)
    detail = "Data tidak dapat diproses karena masih terkait dengan data lain."
    if "ForeignKeyViolationError" in str(exc.orig):
        detail = "Data tidak dapat dihapus karena masih direferensikan oleh data lain."
    elif "UniqueViolationError" in str(exc.orig):
        detail = "Data dengan nilai unik tersebut sudah ada."
    return JSONResponse(status_code=409, content={"detail": detail})


app.include_router(config_router)
app.include_router(records_router)
app.include_router(harvesters_router)
app.include_router(locations_router)
app.include_router(payroll_router)
app.include_router(system_router)
app.include_router(dashboard_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

