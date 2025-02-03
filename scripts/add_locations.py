import asyncio
import datetime
from dotenv.main import dotenv_values

from ifdash import models


async def add_default_location(type, model):

    host_ids = await model.distinct("metadata.id")
    for host_id in host_ids:
        print(host_id)


async def migrate(config):
    await models.init_default_beanie_client()

    collections = dict(
        host=models.HostState,
        AP=models.APState,
    )
    for type, model in collections.items():
        await add_default_location(type, model)


if __name__ == "__main__":
    config = dotenv_values(".env")
    asyncio.run(migrate(config))
