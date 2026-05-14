from app.events.schemas import Event
from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException
from app.events.event_service import get_event_service

router = APIRouter(tags=["events"], responses={404: {"description": "Not found"}})
event_service = get_event_service()

@router.get("/events", response_model=list[Event], responses={422: {"description": "missing tenant identifier header [X-Tenant-ID]"}})
async def get_events_by_tenant(x_tenant_id: Annotated[str, Header()],
                               start_dt: Optional[datetime] = None, 
                               end_dt: Optional[datetime] = None, 
                               action:Optional[str] = None, 
                               package:Optional[str] = None
                              )-> list[Event] | None:    
    if start_dt is not None and end_dt is not None and start_dt > end_dt:
        raise HTTPException(status_code=400, detail="start_dt must be less than or equal to end_dt")
    
    try:
        events = event_service.find_events(x_tenant_id, start_dt, end_dt, action, package)
        return events
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))