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

from fastapi.responses import JSONResponse, Response
import json
from src.domain.services.backup_service import BackupService, default_json_serializer

@router.get("/backup/download")
async def download_database_backup(db: AsyncSession = Depends(get_db)):
    service = BackupService(db)
    backup_data = await service.create_backup()
    json_bytes = json.dumps(backup_data, default=default_json_serializer, indent=2).encode('utf-8')
    timestamp_str = backup_data["metadata"]["created_at"].replace(":", "-").replace(".", "-")
    filename = f"database_backup_{timestamp_str}.json"
    
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.post("/backup/restore")
async def restore_database_backup(payload: dict, db: AsyncSession = Depends(get_db)):
    service = BackupService(db)
    try:
        await service.restore_backup(payload)
        return {"message": "Database berhasil dipulihkan dari cadangan (backup)."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal memulihkan database: {str(e)}")
