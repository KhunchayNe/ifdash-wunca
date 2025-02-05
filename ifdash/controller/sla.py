import pprint
import datetime
import asyncio
import zoneinfo

from ifdash import models, services

import logging

logger = logging.getLogger(__name__)


class Summarizer:
    def __init__(self, settings: dict = dict()):
        self.settings = settings
        self.sla_summarizer_service = services.sla_summarizers.SLASummarizerService()
        self.models = dict(
            host=models.HostState, service=models.ServiceState, ap=models.APState
        )
        self.granularity_mapers = dict(daily="day", monthly="month")
        self.group_names = [
            "Service",
        ]

    async def initial(self):
        self.beanie_client = models.BeanieClient()
        await models.init_default_beanie_client(
            self.beanie_client, multiprocessing_mode=True
        )

    async def summarize(self, start_time, end_time, type, periodicity, timezone="UTC"):
        model = self.models[type]

        started_time_utc = start_time.astimezone(tz=zoneinfo.ZoneInfo("UTC"))
        ended_time_utc = end_time.astimezone(tz=zoneinfo.ZoneInfo("UTC"))

        hosts = await self.sla_summarizer_service.get_sla_hosts_granularity(
            model,
            started_date=started_time_utc,
            ended_date=ended_time_utc,
            granularity=self.granularity_mapers[periodicity],
            timezone=timezone,
        )

        for host_id, slas in hosts.items():
            for label, sla in slas.items():
                sla_record = await models.SLA.find_one(
                    models.SLA.metadata.id == host_id,
                    models.SLA.metadata.type == type,
                    models.SLA.metadata.periodicity == periodicity,
                    models.SLA.timestamp == started_time_utc,
                )

                if sla_record:
                    continue

                metadata = sla["metadata"]
                metadata["type"] = type
                metadata["periodicity"] = periodicity
                metadata["started_date"] = started_time_utc
                metadata["ended_date"] = ended_time_utc
                metadata["count"] = sla.get("count", 0)
                metadata.update(sla["date"])

                sla_record = models.SLA(
                    metadata=metadata,
                    sla=sla["sla"],
                    timestamp=started_time_utc,
                )

                await sla_record.insert()

    async def summarize_groups(
        self, start_time, end_time, type, periodicity, group_names, timezone="UTC"
    ):

        started_time_utc = start_time.astimezone(tz=zoneinfo.ZoneInfo("UTC"))
        ended_time_utc = end_time.astimezone(tz=zoneinfo.ZoneInfo("UTC"))
        groups = await self.sla_summarizer_service.get_sla_sumarization_granularity_by_groups(
            group_names,
            started_date=started_time_utc,
            ended_date=ended_time_utc,
            type=type,
            granularity=self.granularity_mapers[periodicity],
            timezone=timezone,
        )

        for group_name, slas in groups.items():
            for _, date_slas in slas.items():
                for date_label, sla in date_slas.items():
                    sla_record = await models.GroupSLA.find_one(
                        models.SLA.metadata.name == group_name,
                        models.SLA.metadata.type == type,
                        models.SLA.metadata.periodicity == periodicity,
                        models.SLA.timestamp == started_time_utc,
                    )

                    if sla_record:
                        continue

                    metadata = models.GroupSLAMetadata(
                        type=type,
                        name=group_name,
                        periodicity=periodicity,
                        started_date=started_time_utc,
                        ended_date=ended_time_utc,
                        count=sla.get("count", 0),
                    )
                    metadata.day = sla["date"].get("day", 0)
                    metadata.month = sla["date"].get("month", 0)
                    metadata.year = sla["date"].get("year", 0)

                    sla_record = models.GroupSLA(
                        metadata=metadata,
                        sla=sla["sla"],
                        timestamp=started_time_utc,
                    )

                    await sla_record.insert()

    async def summarize_daily(self, start_time, end_time, timezone="UTC"):
        print("summarize daily", start_time, end_time)
        iter_time = start_time
        while iter_time < end_time:
            for type, model in self.models.items():
                begin_time = iter_time
                before_time = iter_time + datetime.timedelta(days=1)

                print("summarize daily", type, begin_time, before_time)
                await self.summarize(begin_time, before_time, type, "daily", timezone)

            iter_time = before_time

    async def summarize_monthly(self, start_time, end_time, timezone="UTC"):
        print("summarize monthly", start_time, end_time)

        iter_month = datetime.datetime.combine(
            start_time.date(), datetime.datetime.min.time()
        )
        iter_month = iter_month.replace(day=1)

        end_month = datetime.datetime.combine(
            end_time.date(), datetime.datetime.min.time()
        )
        end_month = end_month.replace(day=1)

        # print("change summarize monthly", iter_month, end_month)

        while iter_month < end_month:
            for type, model in self.models.items():
                begin_month = iter_month
                before_month = iter_month + datetime.timedelta(days=32)
                before_month = before_month.replace(day=1)

                print("summarize monthly", type, begin_month, before_month)
                await self.summarize(
                    begin_month, before_month, type, "monthly", timezone
                )

            iter_month = before_month

    async def summarize_groups_daily(self, start_time, end_time, timezone="UTC"):
        print("summarize groups daily", start_time, end_time)

        iter_time = start_time
        while iter_time < end_time:
            for type, model in self.models.items():
                begin_time = iter_time
                before_time = iter_time + datetime.timedelta(days=1)

                print("summarize group daily", type, begin_time, before_time)
                await self.summarize_groups(
                    begin_time,
                    before_time,
                    type,
                    "daily",
                    self.group_names,
                    timezone,
                )

            iter_time = before_time

    async def summarize_groups_monthly(self, start_time, end_time, timezone="UTC"):
        print("summarize groups monthly", start_time, end_time)

        iter_month = datetime.datetime.combine(
            start_time.date(), datetime.datetime.min.time()
        )
        iter_month = iter_month.replace(day=1)

        end_month = datetime.datetime.combine(
            end_time.date(), datetime.datetime.min.time()
        )
        end_month = end_month.replace(day=1)

        while iter_month < end_month:
            for type, model in self.models.items():
                begin_month = iter_month
                before_month = iter_month + datetime.timedelta(days=32)
                before_month = before_month.replace(day=1)

                print("summarize group monthly", type, begin_month, before_month)
                await self.summarize_groups(
                    begin_month,
                    before_month,
                    type,
                    "monthly",
                    self.group_names,
                    timezone,
                )

            iter_month = before_month
