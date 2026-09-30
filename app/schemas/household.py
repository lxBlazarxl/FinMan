from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HouseholdResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    created_at: datetime
