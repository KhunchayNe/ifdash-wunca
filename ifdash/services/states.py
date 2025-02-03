from .. import models

import datetime
import asyncio
import pprint


class StateService:
    def __init__(self, sync=False, client=None):
        self.STATE_INDEX = ["up", "down", "unreach", "downtime", "unknow", "total"]

        self.sync = sync
        self.client = client
        if self.sync and not self.client:
            self.client = models.beanie_client

    def get_current_state_sync(self, groups, StateModel=None):
        return self.client.get_loop().run_until_complete(
            self.get_current_state(groups, StateModel)
        )

    async def get_current_state(self, groups, StateModel=None):

        # await models.init_default_beanie_client()
        state_index = ["up", "down", "unreach", "downtime", "unknow", "total"]

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        started_date = now - datetime.timedelta(minutes=2)

        data = dict()
        for group in groups:

            pipelines = [
                {
                    "$match": {
                        "timestamp": {"$gte": started_date},
                        "metadata.groups": group,
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "state": "$state",
                            "id": "$metadata.id",
                            "name": "$metadata.name",
                        },
                        "timestamp": {"$last": "$timestamp"},
                        # "count": {"$sum": 1},
                    }
                },
            ]

            responses = []

            try:
                if StateModel:
                    CurrentStateModel = StateModel
                else:
                    CurrentStateModel = self.MODEL_MAPPERS.get(group)

                responses = await CurrentStateModel.aggregate(pipelines).to_list()
            except Exception as e:
                print("error", e)

            # print(group, model)
            # pprint.pprint(responses)
            if responses:
                data[group] = dict(
                    up=0, down=0, unreach=0, downtime=0, unknow=0, total=0
                )
                for response in responses:
                    data[group][state_index[response["_id"]["state"]]] += 1

                data[group]["total"] = sum(data[group].values())

        return data
