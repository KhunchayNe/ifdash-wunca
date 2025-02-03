from . import users
from . import telemetries
from . import equipments
from . import oauth2

from .users import User
from .oauth2 import OAuth2Token

from .telemetries import HostState, VMState, APState, ServiceState, Metadata
from .slas import SLA, SLAMetadata, GroupSLA, GroupSLAMetadata
from .equipments import Equipment


import sys
import motor
import beanie
import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Sequence, Type, TypeVar
from inspect import getmembers, isclass
from pydantic_settings import BaseSettings


# import nest_asyncio

# nest_asyncio.apply()

DocumentType = TypeVar("DocumentType", bound=beanie.Document)


class AppSettings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost/ifdashdb"
    MONGODB_CONNECT: bool = True

    class Config:
        env_file = ".env"
        extra = "allow"


async def gather_documents() -> Sequence[Type[DocumentType]]:
    """Returns a list of all MongoDB document models defined in `models` module."""

    class_models = getmembers(sys.modules[__name__], isclass)

    for key in [k for k in sys.modules if __name__ in k]:
        class_models.extend(getmembers(sys.modules[key], isclass))

    class_models = list(set(class_models))

    return [
        doc
        for _, doc in class_models
        if issubclass(doc, beanie.Document) and doc.__name__ != "Document"
    ]


class BeanieClient:
    def __init__(self, sync=False):
        self.settings = None
        self.client = None
        self.sync = sync
        if self.sync:
            # self.loop = asyncio.new_event_loop()
            self.loop = asyncio.get_event_loop()

            # asyncio.set_event_loop(self.loop)

    async def init_beanie(self, settings, multiprocessing_mode=False):
        self.settings = settings

        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            settings.MONGODB_URI, connect=settings.MONGODB_CONNECT, tz_aware=True
        )

        documents = await gather_documents()
        print("Documents >>>")
        for document in documents:
            print(document)

        print(self.client.get_default_database())
        await beanie.init_beanie(
            database=self.client.get_default_database(),
            document_models=documents,
            # recreate_views=True,
            multiprocessing_mode=multiprocessing_mode,
        )

    def get_loop(self):
        if not self.loop.is_running():
            self.loop = asyncio.get_event_loop()
            # self.loop = asyncio.new_event_loop()
            # asyncio.set_event_loop(self.loop)
            if self.settings:
                self.loop.run_until_complete(self.init_beanie(self.settings))

        return self.loop


async def init_beanie(app, settings, multiprocessing_mode=False):
    await beanie_client.init_beanie(settings, multiprocessing_mode)


async def init_default_beanie_client(
    beanie_client_local=None, multiprocessing_mode=False
):
    settings = AppSettings()
    # print("setings>>>", settings)
    if beanie_client_local:
        await beanie_client_local.init_beanie(settings, multiprocessing_mode)
    else:
        if beanie_client.sync and beanie_client.loop.is_closed():
            beanie_client.loop = asyncio.get_event_loop()
            asyncio.set_event_loop(beanie_client.loop)

        if not beanie_client.client:
            await beanie_client.init_beanie(settings, multiprocessing_mode)


beanie_client = BeanieClient()


def init_db(app):
    global beanie_client

    import nest_asyncio

    nest_asyncio.apply()

    with app.app_context():
        settings = AppSettings()
        settings.MONGODB_CONNECT = False
        beanie_client = BeanieClient(sync=True)
        loop = beanie_client.get_loop()
        loop.run_until_complete(init_beanie(app, settings, multiprocessing_mode=True))
