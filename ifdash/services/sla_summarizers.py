from .. import models

import datetime
import asyncio
import pprint
import zoneinfo


class SLASummarizerService:
    def __init__(self, sync=False, client=None):
        self.client = client
        self.STATE_INDEX = ["up", "down", "unreach", "downtime", "unknow", "total"]

        self.sync = sync
        self.client = client
        if self.sync and not self.client:
            self.client = models.beanie_client
            # self.client.get_loop().run_until_complete(models.init_default_beanie_client())

    def get_sla_hosts_granularity_sync(
        self, StateModel, started_date, ended_date, granularity="month", timezone="UTC"
    ):
        return self.client.get_loop().run_until_complete(
            self.get_sla_hosts_granularity(
                StateModel,
                started_date,
                ended_date,
                granularity=granularity,
                timezone=timezone,
            )
        )

    async def get_sla_hosts_granularity(
        self,
        StateModel,
        started_date,
        ended_date,
        granularity="month",
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

        metadata = dict(
            id="$metadata.id",
            name="$metadata.name",
            host_name="$metadata.host_name",
            groups="$metadata.groups",
            labels="$metadata.labels",
        )

        started_date_utc = started_date.astimezone(zoneinfo.ZoneInfo("UTC"))
        ended_date_utc = ended_date.astimezone(zoneinfo.ZoneInfo("UTC"))
        pipeline_group_id = dict(state="$state", date=date, metadata=metadata)
        pipelines = [
            {
                "$match": {
                    "timestamp": {"$gte": started_date_utc, "$lt": ended_date_utc},
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
            responses = await StateModel.aggregate(pipelines).to_list()
        except Exception as e:
            print("error", e)

        for response in responses:
            host_id = response["_id"]["metadata"]["id"]
            subdate = response["_id"]["date"]
            state = response["_id"]["state"]

            if host_id not in data.keys():
                data[host_id] = dict()

            date_key = subdate["year"]
            if granularity == "month":
                date_key = f"{subdate['year']}-{subdate['month']:02}"
            if granularity == "day":
                date_key = f"{subdate['year']}-{subdate['month']}-{subdate['day']:02}"

            if date_key not in data[host_id]:
                data[host_id][date_key] = dict(
                    up=0,
                    down=0,
                    unreach=0,
                    downtime=0,
                    unknow=0,
                )

                data[host_id][date_key]["metadata"] = response["_id"]["metadata"]

            state_data = data[host_id][date_key]
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

    def get_sla_sumarization_granularity_by_groups_sync(
        self,
        groups,
        started_date,
        ended_date,
        type="host",
        granularity="month",
        enable_host=False,
        timezone="UTC",
    ):
        return self.client.get_loop().run_until_complete(
            self.get_sla_sumarization_granularity_by_groups(
                groups,
                started_date,
                ended_date,
                type=type,
                granularity=granularity,
                enable_host=enable_host,
                timezone=timezone,
            )
        )

    async def get_sla_sumarization_granularity_by_groups(
        self,
        groups,
        started_date,
        ended_date,
        type="host",
        granularity="month",
        enable_host=False,
        timezone="UTC",
    ):
        # await models.init_default_beanie_client()
        # state_index = ["up", "down", "unreach", "downtime", "unknow", "total"]
        periodic_mapper = dict(month="monthly", day="daily")

        data = dict()

        date = dict(year="$date.year")
        if granularity == "month":
            date["month"] = "$date.month"
        elif granularity == "day":
            date["month"] = "$date.month"
            date["day"] = "$date.day"

        started_date_utc = started_date.astimezone(zoneinfo.ZoneInfo("UTC"))
        ended_date_utc = ended_date.astimezone(zoneinfo.ZoneInfo("UTC"))

        for group in groups:
            pipeline_group_id = dict(state="$state", date=date)

            if enable_host:
                pipeline_group_id["id"] = "$metadata.id"
                pipeline_group_id["name"] = "$metadata.name"
                pipeline_group_id["host_name"] = "$metadata.host_name"

            match_stage = {
                "$match": {
                    "timestamp": {"$gte": started_date_utc, "$lt": ended_date_utc},
                    "metadata.groups": group,
                    "metadata.type": type,
                    "metadata.periodicity": periodic_mapper.get(granularity),
                }
            }

            pipelines = [
                match_stage,
                {
                    "$project": {
                        "date": {
                            "$dateToParts": {"date": "$timestamp", "timezone": timezone}
                        },
                        "metadata": 1,
                        "sla": 1,
                    }
                },
                {
                    "$group": {
                        "_id": pipeline_group_id,
                        "count": {"$sum": 1},
                        "sla": {"$avg": "$sla"},
                    }
                },
            ]

            responses = []
            try:
                responses = await models.SLA.aggregate(pipelines).to_list()
            except Exception as e:
                print("error summarize", e)

            # print(group, responses)
            data[group] = dict()
            if not responses:
                continue

            for response in responses:
                host_id = response["_id"].get("id", "all")
                subdate = response["_id"]["date"]
                # state = response["_id"]["state"]

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
                        sla=0,
                        count=0,
                    )
                    if enable_host:
                        data[group][host_id][date_key]["id"] = response["_id"]["id"]
                        data[group][host_id][date_key]["name"] = response["_id"]["name"]
                        data[group][host_id][date_key]["host_name"] = response["_id"][
                            "host_name"
                        ]

                state_data = data[group][host_id][date_key]
                state_data["count"] = response["count"]
                state_data["sla"] = response["sla"]
                state_data["date"] = subdate

                state_data.update(subdate)

        return data

    def get_group_sla_sumarization_granularity_sync(
        self,
        groups,
        started_date,
        ended_date,
        type="host",
        granularity="month",
        timezone="UTC",
    ):
        return self.client.get_loop().run_until_complete(
            self.get_group_sla_sumarization_granularity(
                groups,
                started_date,
                ended_date,
                type=type,
                granularity=granularity,
                timezone=timezone,
            )
        )

    async def get_group_sla_sumarization_granularity(
        self,
        groups,
        started_date,
        ended_date,
        type="host",
        granularity="month",
        timezone="UTC",
    ):
        # await models.init_default_beanie_client()
        # state_index = ["up", "down", "unreach", "downtime", "unknow", "total"]
        periodic_mapper = dict(month="monthly", day="daily")

        data = dict()

        date = dict(year="$date.year")
        if granularity == "month":
            date["month"] = "$date.month"
        elif granularity == "day":
            date["month"] = "$date.month"
            date["day"] = "$date.day"

        started_date_utc = started_date.astimezone(zoneinfo.ZoneInfo("UTC"))
        ended_date_utc = ended_date.astimezone(zoneinfo.ZoneInfo("UTC"))

        print(
            type, "started_date_utc", started_date_utc, "ended_date_utc", ended_date_utc
        )

        for group in groups:
            pipeline_group_id = dict(date=date)

            match_stage = {
                "$match": {
                    "timestamp": {"$gte": started_date_utc, "$lt": ended_date_utc},
                    "metadata.name": group,
                    "metadata.type": type,
                    "metadata.periodicity": periodic_mapper.get(granularity, ""),
                }
            }

            pipelines = [
                match_stage,
                {
                    "$project": {
                        "date": {
                            "$dateToParts": {"date": "$timestamp", "timezone": timezone}
                        },
                        "metadata": 1,
                        "sla": 1,
                    }
                },
                {
                    "$group": {
                        "_id": pipeline_group_id,
                        "count": {"$sum": 1},
                        "sla": {"$avg": "$sla"},
                    }
                },
            ]

            responses = []
            # print("pipeline", pipelines)
            try:
                responses = await models.GroupSLA.aggregate(pipelines).to_list()
            except Exception as e:
                print("error summarize", e)

            # print("responses", responses)
            data[group] = dict()
            if not responses:
                continue

            for response in responses:
                host_id = response["_id"].get("id", "all")
                subdate = response["_id"]["date"]
                # state = response["_id"]["state"]

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
                        sla=0,
                        count=0,
                    )

                state_data = data[group][host_id][date_key]
                state_data["count"] = response["count"]
                state_data["sla"] = response["sla"]
                state_data["date"] = subdate

                state_data.update(subdate)

        return data
