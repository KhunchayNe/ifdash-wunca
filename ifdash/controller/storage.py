import pprint
import datetime
import asyncio
import copy

from ifdash import models

import logging

logger = logging.getLogger(__name__)


class StorageManager:
    def __init__(self, config):
        self.config = config
    async def initial(self):
        self.beanie_client = models.BeanieClient()
        await models.init_default_beanie_client(
            self.beanie_client, multiprocessing_mode=True
        )

    async def save(self, results: dict):
        model_mappers = dict(
            host=models.HostState,
            VM=models.VMState,
            AP=models.APState,
            service=models.ServiceState,
        )

        state_data = results.get("data")
        type_ = results.get("type")
        response_date = results.get("response_date")

        print("start save data:", type_, response_date)
        points = []
        counter = 0
        for name, datas in state_data.items():
            for data in datas:
                # print("->", name, data)
                data = copy.deepcopy(data)
                checked_date = data.pop("checked_date")
                state = data.pop("state")
                # print(">>> ", model_mappers.get(name))
                counter += 1
                Model = model_mappers.get(name)
                try:
                    metadata = models.Metadata(**data)
                    model = Model(
                        timestamp=checked_date, state=state, metadata=metadata
                    )
                    await model.insert()
                except Exception as e:
                    print("insert error", e)

        print(
            "end save data:",
            type_,
            counter,
            datetime.datetime.now(tz=datetime.timezone.utc),
        )
