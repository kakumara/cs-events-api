import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.events.schemas import Event
from app.config import config
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventService:
    def __init__(self):
        self.__events_by_tenant = {}
        self.load_events()

    # This method loads events from the specified file and organizes them in a dictionary for efficient retrieval.
    # {tenant_id: {event_id: Event}}
    def load_events(self):
        try:
            with open(config.EVENTS_FILE, "r") as f:
                for line_number, line in enumerate(f, start=1):
                    try:
                        event = Event.model_validate_json(line)
                        if event.tenant_id not in self.__events_by_tenant:
                            self.__events_by_tenant[event.tenant_id] = {}
                        event_entry = {event.event_id: event}
                        self.__events_by_tenant[event.tenant_id].update(event_entry)
                    except Exception as e:
                        logger.debug(f"Error parsing event on line {line_number}: {e}")
        except FileNotFoundError:
            logger.warning(
                f"Events file not found: {config.EVENTS_FILE}. Starting with empty events."
            )
        except Exception as e:
            logger.error(f"Error loading events from file: {e}")

    # This method is used by the API endpoint to find events based on the provided filters
    def find_events(
        self,
        tenant_id: str,
        start_dt: Optional[datetime] = None,
        end_dt: Optional[datetime] = None,
        action: Optional[str] = None,
        package: Optional[str] = None,
    ) -> list[Event] | None:
        if tenant_id not in self.__events_by_tenant:
            raise ValueError(f"Invalid tenant identifier: {tenant_id}")

        found_events = []
        for event in self.__events_by_tenant.get(tenant_id, {}).values():
            if (
                (start_dt is None or event.timestamp >= start_dt)
                and (end_dt is None or event.timestamp <= end_dt)
                and (action is None or event.action == action)
                and (package is None or event.package == package)
            ):
                found_events.append(event)

        found_events.sort(key=lambda e: e.timestamp)
        return found_events

    # This method is called by the scheduled task to clean up old events based on the retention policy
    def cleanup_old_events(self):
        ret_days = config.RETENTION_DAYS
        logger.info("Task: Cleaning up old events older than %d days", ret_days)
        cutoff_dt = datetime.now(timezone.utc) - timedelta(days=ret_days)
        for tenant_id, events_dict in self.__events_by_tenant.items():
            old_event_ids = [
                event_id
                for event_id, event in events_dict.items()
                if event.timestamp < cutoff_dt
            ]
            for event_id in old_event_ids:
                del events_dict[event_id]
                logger.info(f"Deleted old event {event_id} for tenant {tenant_id}")


@lru_cache(maxsize=1)
def get_event_service() -> EventService:
    return EventService()


event_service = get_event_service()
