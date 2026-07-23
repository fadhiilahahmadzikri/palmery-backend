from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import get_db
from src.domain.services.readiness_service import ReadinessService, SystemReadinessResponse

router = APIRouter(prefix="/api/v1/system", tags=["system"])

from pydantic import BaseModel
from fastapi import HTTPException

class PurgeRequest(BaseModel):
    confirm_code: str

@router.get("/readiness", response_model=SystemReadinessResponse)
async def get_system_readiness(db: AsyncSession = Depends(get_db)):
    service = ReadinessService(db)
    return await service.get_system_readiness()

@router.post("/purge")
async def purge_system_data(req: PurgeRequest, db: AsyncSession = Depends(get_db)):
    if req.confirm_code != "PURGE-ALL-DATA":
        raise HTTPException(status_code=400, detail="Kode konfirmasi salah. Ketik 'PURGE-ALL-DATA' untuk mengonfirmasi pembersihan.")
    service = ReadinessService(db)
    await service.purge_system_data()
    return {"message": "Seluruh data sistem berhasil dibersihkan. Sistem telah kembali ke kondisi Fresh Install."}
