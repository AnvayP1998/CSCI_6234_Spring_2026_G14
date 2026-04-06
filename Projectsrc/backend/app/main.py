from fastapi import FastAPI
from app.core.config import settings
from app.core.db import init_db
from app.api.routes.health import router as health_router
from app.api.routes.assets import router as assets_router
from app.api.routes.query import router as query_router
from app.api.routes.tasks import router as tasks_router

app = FastAPI(title=settings.APP_NAME)

@app.on_event("startup")
def startup() -> None:
    init_db()

app.include_router(health_router, prefix="/api")
app.include_router(assets_router, prefix="/api")
app.include_router(query_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")