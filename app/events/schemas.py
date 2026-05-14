from datetime import datetime
from pydantic import BaseModel, Field


class Event(BaseModel):
    event_id: str = Field(..., description="Unique identifier for the event")
    tenant_id: str = Field(..., description="Identifier for the tenant")
    action: str = Field(..., description="Action performed in the event")
    package: str = Field(..., description="Package associated with the event")
    version: str = Field(..., description="Version of the package")
    timestamp: datetime = Field(..., description="Timestamp of when the event occurred")
    actor: str = Field(..., description="Actor who performed the action")
