import datetime

import beanie
from pydantic import Field
from . import users
from . import base


class OAuth2Token(base.BaseSchema, beanie.Document):
    id: beanie.PydanticObjectId = Field(
        default_factory=beanie.PydanticObjectId,
        alias="_id",
    )

    user: beanie.Link[users.User]
    name: str

    token_type: str
    access_token: str
    # refresh_token or access_token_secret
    refresh_token: str | None
    expires: datetime.datetime = Field(default_factory=datetime.datetime.now)

    class Settings:
        name = "oauth2_tokens"

    @property
    def expires_at(self):
        return self.expires.timestamp()

    def to_dict(self):
        return dict(
            access_token=self.access_token,
            token_type=self.token_type,
            refresh_token=self.refresh_token,
            expires_at=self.expires_at,
        )
