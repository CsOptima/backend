from dotenv.main import rewrite
from fastapi import APIRouter

from src.api.bridge import bridge_router
from src.api.rewriter import rewriter_router

api_router = APIRouter(prefix="/api")

all_routers = [
    bridge_router,
    rewriter_router
]

for router in all_routers:
    api_router.include_router(router)
