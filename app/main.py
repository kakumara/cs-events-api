import logging

from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Depends
from .routers import events
from .config import config

logger = logging.getLogger(__name__)


async def cleanup_old_events_task():
    from .events.event_service import get_event_service

    event_service = get_event_service()
    event_service.cleanup_old_events()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        cleanup_old_events_task, "interval", hours=config.CLEANUP_INTERVAL_HOURS
    )
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan, title=config.APP_NAME, version=config.APP_VERSION)
app.include_router(events.router)


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Status [OK]"}
