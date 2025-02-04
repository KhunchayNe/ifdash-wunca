import asyncio
import concurrent.futures

import uptime_kuma_api
import datetime
import logging

logger = logging.getLogger(__name__)


class UptimeKumaManager:
    def __init__(self, config: dict, queues):
        self.config = config
        self.uptime_kuma_client = uptime_kuma_api.UptimeKumaApi(
            self.config.get("UPTIME_KUMA_BASE_API_URL")
        )
        self.uptime_kuma_client.login(
            self.config.get("UPTIME_KUMA_USERNAME"),
            self.config.get("UPTIME_KUMA_PASSWORD"),
        )

        self.queues = queues

    async def get(self):
        response_date = datetime.datetime.now(tz=datetime.timezone.utc)
        print(f"get uptime kuma data", response_date)
        monitors = self.uptime_kuma_client.get_monitors()

        responses = []

        groups = {
            monitor["id"]: monitor
            for monitor in monitors
            if monitor["type"] == uptime_kuma_api.MonitorType.GROUP
        }

        for monitor in monitors:

            if monitor["type"] == uptime_kuma_api.MonitorType.GROUP:
                continue

            check_responses = self.uptime_kuma_client.get_monitor_beats(
                monitor["id"], 0.1
            )
            if check_responses:
                response = check_responses[-1]
                response["monitor"] = monitor
                response["groups"] = []
                if monitor["parent"]:
                    response["groups"] = [groups[monitor["parent"]]["name"]]

                response["groups"].append(monitor["type"].name)
                responses.append(response)
                # print(">>>", response)
            await asyncio.sleep(0)

        data = await self.transform_output(responses)
        for queue in self.queues:
            queue.put(
                dict(
                    response_date=response_date,
                    data=data,
                    type="uptime-kuma",
                )
            )

    async def transform_output(self, responses) -> list:
        # print("response", responses)

        results = dict(service=[])

        for service in responses:
            # print("service", service)
            monitor = service["monitor"]

            if monitor["type"] == uptime_kuma_api.MonitorType.GROUP:
                continue

            if service["status"] == uptime_kuma_api.MonitorStatus.PENDING:
                continue

            checked_date = datetime.datetime.now(tz=datetime.timezone.utc)
            if "time" in service:
                checked_date = datetime.datetime.strptime(
                    service["time"], "%Y-%m-%d %H:%M:%S.%f"
                ).astimezone(datetime.timezone.utc)

            data = dict(
                id=f'{monitor["id"]}',
                host_name=monitor["name"],
                # address=address,
                name=monitor["type"].name,
                checked_date=checked_date,
                duration=service["duration"],
            )

            # print(type(monitor["type"]))
            if "groups" in service:
                data["groups"] = service["groups"]

            if monitor["url"]:
                data["url"] = monitor["url"]

            # services: 0/1/2/3 for OK/WARN/CRIT/UNKNOWN
            if service["status"] == uptime_kuma_api.MonitorStatus.UP:
                data["state"] = 0
            elif service["status"] == uptime_kuma_api.MonitorStatus.DOWN:
                data["state"] = 2

            if service["status"] == uptime_kuma_api.MonitorStatus.MAINTENANCE:
                data["state"] = 3
                data["downtime"] = True
            else:
                data["downtime"] = False

            results["service"].append(data)

        await asyncio.sleep(0)

        return results
