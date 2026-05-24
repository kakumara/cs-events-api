from app.events.schemas import Event
from typing import Annotated, Optional, Tuple
from datetime import datetime, UTC

from fastapi import APIRouter, Header, HTTPException
from app.events.event_service import get_event_service

router = APIRouter(tags=["events"], responses={404: {"description": "Not found"}})
event_service = get_event_service()


@router.get(
    "/events",
    response_model=list[Event],
    responses={422: {"description": "missing tenant identifier header [X-Tenant-ID]"}},
)
async def get_events_by_tenant(
    x_tenant_id: Annotated[str, Header()],
    start_dt: Optional[str] = None,
    end_dt: Optional[str] = None,
    action: Optional[str] = None,
    package: Optional[str] = None,
) -> list[Event] | None:

    st_datetime_utc, end_datetime_utc = validate_date_range(start_dt, end_dt)
    try:
        events = event_service.find_events(
            x_tenant_id, st_datetime_utc, end_datetime_utc, action, package
        )
        return events
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

"""
Validates and converts a provided datetime string to a comparable format (UTC datetime)
This provides a correct datetime comparison with events datastore
""" 
def validate_date_range(
    start_dt: Optional[str], end_dt: Optional[str]
) -> Tuple[Optional[datetime], Optional[datetime]]:
    if start_dt is None and end_dt is None:
        return None, None

    if start_dt is None or end_dt is None:
        raise HTTPException(
            status_code=400, detail="Both start_dt and end_dt are required"
        )

    if not is_iso_datetime(start_dt) or not is_iso_datetime(end_dt):
        raise HTTPException(
            status_code=400, detail="start_dt and end_dt must be valid datetime strings"
        )

    st_datetime = with_timezone(datetime.fromisoformat(start_dt)).astimezone(UTC)
    end_datetime = with_timezone(datetime.fromisoformat(end_dt)).astimezone(UTC)

    if st_datetime > end_datetime:
        raise HTTPException(
            status_code=400, detail="start_dt must be less than or equal to end_dt"
        )
    return st_datetime, end_datetime


def is_iso_datetime(date_str: str):
    try:
        datetime.fromisoformat(date_str)
        return True
    except ValueError:
        return False


def with_timezone(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt
