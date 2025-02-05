from .. import models

import datetime
import asyncio
import pprint
import zoneinfo


class SLAService:
    def __init__(self, sync=False, client=None):
        self.MODEL_MAPPERS = {
            "NETWORK": models.HostState,
            "Wireless": models.APState,
            "Service": models.ServiceState,
            "HTTP": models.ServiceState,
        }

        self.STATE_INDEX = ["up", "down", "unreach", "downtime", "unknow", "total"]

        self.sync = sync
        self.client = client
        if self.sync and not self.client:
            self.client = models.beanie_client
            # self.client.get_loop().run_until_complete(models.init_default_beanie_client())

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

    def get_sla_by_groups_sync(
        self,
        groups,
        started_date,
        ended_date,
        enable_host=False,
        StateModel=None,
        timezone="UTC",
    ):
        return self.client.get_loop().run_until_complete(
            self.get_sla_by_groups(
                groups,
                started_date,
                ended_date,
                enable_host=enable_host,
                StateModel=StateModel,
                timezone=timezone,
            )
        )

    async def get_sla_by_groups(
        self,
        groups,
        started_date,
        ended_date,
        enable_host=False,
        StateModel=None,
        timezone="UTC",
    ):
        # await models.init_default_beanie_client()

        data = dict()

        started_date_utc = started_date.astimezone(zoneinfo.ZoneInfo("UTC"))
        ended_date_utc = ended_date.astimezone(zoneinfo.ZoneInfo("UTC"))
        for group in groups:

            pipeline_group_id = dict(
                state="$state",
            )

            if enable_host:
                pipeline_group_id["id"] = "$metadata.id"
                pipeline_group_id["name"] = "$metadata.name"
                pipeline_group_id["host_name"] = "$metadata.host_name"

            pipelines = [
                {
                    "$match": {
                        "timestamp": {"$gte": started_date_utc, "$lt": ended_date_utc},
                        "metadata.groups": group,
                    }
                },
                {
                    "$group": {
                        "_id": pipeline_group_id,
                        "count": {"$sum": 1},
                    }
                },
            ]

            responses = []
            try:
                if not StateModel:
                    StateModel = self.MODEL_MAPPERS.get(group)
                responses = await StateModel.aggregate(pipelines).to_list()
            except Exception as e:
                print("error", e)
                return dict(group=dict())

            # print(group, responses)
            data[group] = dict()
            if not responses:
                continue

            for response in responses:
                host_id = response["_id"].get("id", "all")
                if host_id not in data[group]:
                    data[group][host_id] = dict(
                        up=0,
                        down=0,
                        unreach=0,
                        downtime=0,
                        unknow=0,
                    )

                    if enable_host:
                        data[group][host_id]["id"] = response["_id"]["id"]
                        data[group][host_id]["name"] = response["_id"]["name"]
                        data[group][host_id]["host_name"] = response["_id"]["host_name"]

                state_data = data[group][host_id]

                state_data[self.STATE_INDEX[response["_id"]["state"]]] = response[
                    "count"
                ]

                state_data["total"] = sum(
                    [
                        d
                        for k, d in state_data.items()
                        if k in ["up", "down", "unreach", "unknow"]
                    ]
                )

                state_data["sla"] = 0
                if state_data["total"]:
                    state_data["sla"] = state_data["up"] / state_data["total"] * 100

                # state_data["sla"] = (
                #     data[group][host_id]["up"] / data[group][host_id]["total"] * 100
                # )

        return data

    def get_sla_granularity_by_groups_sync(
        self,
        groups,
        started_date,
        ended_date,
        granularity="month",
        enable_host=False,
        StateModel=None,
        timezone="UTC",
    ):
        return self.client.get_loop().run_until_complete(
            self.get_sla_granularity_by_groups(
                groups,
                started_date,
                ended_date,
                granularity=granularity,
                enable_host=enable_host,
                StateModel=StateModel,
                timezone=timezone,
            )
        )

    async def get_sla_granularity_by_groups(
        self,
        groups,
        started_date,
        ended_date,
        granularity="month",
        enable_host=False,
        StateModel=None,
        timezone="UTC",
    ):
        # await models.init_default_beanie_client()
        # state_index = ["up", "down", "unreach", "downtime", "unknow", "total"]

        data = dict()

        date = dict(year="$date.year")
        if granularity == "month":
            date["month"] = "$date.month"
        elif granularity == "day":
            date["month"] = "$date.month"
            date["day"] = "$date.day"

        started_date_utc = started_date.astimezone(datetime.timezone.utc)
        ended_date_utc = ended_date.astimezone(datetime.timezone.utc)

        for group in groups:
            pipeline_group_id = dict(state="$state", date=date)

            if enable_host:
                pipeline_group_id["id"] = "$metadata.id"
                pipeline_group_id["name"] = "$metadata.name"
                pipeline_group_id["host_name"] = "$metadata.host_name"

            pipelines = [
                {
                    "$match": {
                        "timestamp": {"$gte": started_date_utc, "$lt": ended_date_utc},
                        "metadata.groups": group,
                    }
                },
                {
                    "$project": {
                        "date": {
                            "$dateToParts": {"date": "$timestamp", "timezone": timezone}
                        },
                        "metadata": 1,
                        "state": 1,
                    }
                },
                {
                    "$group": {
                        "_id": pipeline_group_id,
                        "count": {"$sum": 1},
                    }
                },
            ]

            responses = []
            try:
                if not StateModel:
                    StateModel = self.MODEL_MAPPERS.get(group)

                responses = await StateModel.aggregate(pipelines).to_list()
            except Exception as e:
                print("error SLA", e, group)

            # print(group, responses)
            data[group] = dict()
            if not responses:
                continue

            for response in responses:
                host_id = response["_id"].get("id", "all")
                subdate = response["_id"]["date"]
                state = response["_id"]["state"]

                if host_id not in data[group].keys():
                    data[group][host_id] = dict()

                date_key = subdate["year"]
                if granularity == "month":
                    date_key = f"{subdate['year']}-{subdate['month']:02}"
                if granularity == "day":
                    date_key = (
                        f"{subdate['year']}-{subdate['month']}-{subdate['day']:02}"
                    )

                if date_key not in data[group][host_id]:
                    data[group][host_id][date_key] = dict(
                        up=0,
                        down=0,
                        unreach=0,
                        downtime=0,
                        unknow=0,
                    )
                    if enable_host:
                        data[group][host_id][date_key]["id"] = response["_id"]["id"]
                        data[group][host_id][date_key]["name"] = response["_id"]["name"]
                        data[group][host_id][date_key]["host_name"] = response["_id"][
                            "host_name"
                        ]

                state_data = data[group][host_id][date_key]
                state_data[self.STATE_INDEX[state]] = response["count"]
                state_data["total"] = sum(
                    [
                        d
                        for k, d in state_data.items()
                        if k in ["up", "down", "unreach", "unknow"]
                    ]
                )
                state_data["sla"] = 0
                if state_data["total"]:
                    state_data["sla"] = state_data["up"] / state_data["total"] * 100

                state_data["date"] = subdate

                state_data.update(subdate)

        return data
