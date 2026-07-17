from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.calculate import router as calculate_router
from src.api.v1.config import router as config_router
from src.api.v1.records import router as records_router

app = FastAPI(
    title="Palm Oil Harvest Premium Calculator",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calculate_router)
app.include_router(config_router)
app.include_router(records_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
