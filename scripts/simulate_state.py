import asyncio
import datetime
from dotenv.main import dotenv_values

from ifdash import models


class StateSimulator:
    async def simulate(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        mapers = dict(
            host=models.HostState,
            AP=models.APState,
            service=models.ServiceState,
        )

        for host, Model in mapers.items():
            aggregates = [
                {
                    "$group": {
                        "_id": dict(
                            id="$metadata.id",
                            name="$metadata.name",
                            host_name="$metadata.host_name",
                            address="$metadata.address",
                            downtime="$metadata.downtime",
                            duration="$metadata.duration",
                            groups="$metadata.groups",
                            labels="$metadata.labels",
                        ),
                        "state": {"$last": "$state"},
                    }
                },
                # {
                #     "$setWindowFields": {
                #         "partitionBy": "$state",
                #         "sortBy": {"orderDate": 1},
                #         "output": {
                #             "lastOrderTypeForState": {
                #                 "$last": "$metadata.id",
                #                 "window": {"documents": ["current", "unbounded"]},
                #             }
                #         },
                #     }
                # }
            ]
            hosts = await Model.aggregate(aggregates).to_list()
            for i, host in enumerate(hosts):
                print(i, host)
                model = Model(metadata=host["_id"], state=host["state"])
                model.timestamp = now
                model.metadata.created_date = datetime.datetime.now()
                await model.insert()
                print(">>>", i, model.metadata.id)


async def simulate(config):
    await models.init_default_beanie_client()

    simulators = [StateSimulator()]
    while True:
        for simulator in simulators:
            await simulator.simulate()
            await asyncio.sleep(1)
        print("wait for next round")
        await asyncio.sleep(60)


if __name__ == "__main__":
    config = dotenv_values(".env")
    asyncio.run(simulate(config))
