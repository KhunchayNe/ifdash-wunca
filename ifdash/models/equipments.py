import beanie
from pydantic import Field, BaseModel


from typing import List
import datetime

from . import base


class Equipment(base.BaseSchema, beanie.Document):
    id: beanie.PydanticObjectId = Field(
        default_factory=beanie.PydanticObjectId,
        alias="_id",
    )

    host_id: beanie.Indexed(str, unique=True)
    coordinates: base.GeoObject = base.GeoObject()

    created_date: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_date: datetime.datetime = Field(default_factory=datetime.datetime.now)

    class Settings:
        name = "equipments"
