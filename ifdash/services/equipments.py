from .. import models

import datetime
import asyncio
import pprint


class EquipmentService:
    def __init__(self, sync=False, client=None):
        self.MODEL_MAPPERS = {
            "outside-psu": models.HostState,
            "ISP": models.HostState,
            "PSU-CORE-NETWORK": models.HostState,
            "PSU-HDY-NETWORK": models.HostState,
            "PSU-HDY-Backbone": models.HostState,
            "PSU-HDY-Wireless": models.APState,
            "PSU-HDY-All-Unit": models.HostState,
            "AD": models.ServiceState,
            "HTTP": models.ServiceState,
            "PSU Web": models.ServiceState,
        }

        self.sync = sync
        self.client = client
        if self.sync and not self.client:
            self.client = models.beanie_client
            # self.client.loop.run_until_complete(models.init_default_beanie_client())

    def get_equipment_by_host_id_sync(self, host_id):
        return self.client.get_loop().run_until_complete(
            self.get_equipment_by_host_id(host_id)
        )

    async def get_equipment_by_host_id(self, groups):
        equipment = await models.Equipment.find_one(models.Equipment.host_id == groups)

        return equipment
