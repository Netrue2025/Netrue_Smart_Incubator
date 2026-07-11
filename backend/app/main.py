import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config.settings import get_settings
from app.database.session import init_db
from app.sync.scheduler import live_scheduler
from app.websocket.manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    stop_event = asyncio.Event()
    task = asyncio.create_task(live_scheduler(stop_event))
    yield
    stop_event.set()
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.firmware_version, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix=settings.api_prefix)


@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
