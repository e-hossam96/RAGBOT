import datetime
from bson.objectid import ObjectId
from pydantic import BaseModel, Field


class Asset(BaseModel):
    id: ObjectId = Field(default=None, alias="_id")
    name: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    size: int = Field(gt=0, default=None)
    pushed_at_time: datetime.datetime = Field(
        default=datetime.datetime.now(datetime.timezone.utc)
    )

    class Config:
        arbitrary_types_allowed = True
