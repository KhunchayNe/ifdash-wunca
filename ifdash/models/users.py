import datetime
import beanie
from pydantic import Field

from flask_login import UserMixin

from . import base


class User(base.BaseSchema, beanie.Document, UserMixin):
    id: beanie.PydanticObjectId = Field(
        default_factory=beanie.PydanticObjectId,
        alias="_id",
    )

    username: str
    email: str
    first_name: str
    last_name: str
    status: str = "disactive"
    roles: list[str] = ["user"]

    created_date: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_date: datetime.datetime = Field(default_factory=datetime.datetime.now)
    last_login_date: datetime.datetime = Field(default_factory=datetime.datetime.now)

    picture_url: str | None = None
    resources: dict = dict()

    class Settings:
        name = "users"

    def get_image(self):
        return self.picture_url

    def has_roles(self, *roles):
        for role in roles:
            if role not in self.roles:
                return False

        return True
