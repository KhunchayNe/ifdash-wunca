import asyncio
import concurrent.futures

import datetime
import logging

logger = logging.getLogger(__name__)


from ifdash import clients


class CheckMKManager:
    def __init__(self, config: dict, queues):
        self.config = config
        self.checkmk_client = clients.checkmk.CheckmkClient(
            username=self.config.get("CHECKMK_USERNAME", ""),
            password=self.config.get("CHECKMK_PASSWORD", ""),
            base_api_url=self.config.get("CHECKMK_BASE_API_URL", ""),
        )

        self.queues = queues

    async def get(self):
        responses = self.checkmk_client.hosts.get_hosts()

        response_date = datetime.datetime.now(tz=datetime.timezone.utc)

        print("get checkmk data", response_date)
        data = await self.transform_output(responses)
        for queue in self.queues:
            queue.put(dict(response_date=response_date, data=data, type="checkmk"))

    async def transform_output(self, response) -> list:
        # response = data["response"]
        # print("data date", data_date)

        results = dict(host=[], service=[], VM=[], AP=[])

        for r in response["value"]:
            id_ = r.get("id")
            extensions = r["extensions"]

            address = extensions.get("address")
            host_name = extensions.get("name")
            state = extensions.get("state")
            total_services = extensions.get("total_services")
            downtime = True if len(extensions.get("downtimes_with_info")) > 0 else False
            services = extensions.get("services_with_fullstate", [])
            duration = extensions.get("check_interval", 0) * 60
            labels = extensions.get("labels", {})

            last_check = datetime.datetime.fromtimestamp(
                extensions.get("last_check"), datetime.timezone.utc
            )

            groups = extensions.get("groups")
            data = dict(
                id=id_,
                address=address,
                name=host_name,
                state=state,
                total_services=total_services,
                downtime=downtime,
                checked_date=last_check,
                duration=duration,
                groups=groups,
                labels=labels,
            )

            results["host"].append(data)

            service_extensions = None

            for service in services:
                data = dict(
                    id=f"{id_} {service[0]}",
                    host_name=host_name,
                    address=address,
                    name=service[0],
                    state=service[1],
                    downtime=downtime,
                    checked_date=last_check,
                    groups=groups,
                    duration=duration,
                    labels=labels,
                )

                name = service[0].split(" ")[0]

                if name in ["AP", "VM", "LDAP"] and not service_extensions:
                    response = self.checkmk_client.services.get(service[0], host_name)
                    service_extensions = response["value"][0]["extensions"]

                if service_extensions:
                    data["groups"] = extensions.get("groups") + service_extensions.get(
                        "groups"
                    )

                if "AP" == name:
                    results["AP"].append(data)

                elif "VM" == name:
                    results["VM"].append(data)

                if "LDAP" == name:
                    data["name"] = name
                    results["service"].append(data)
            await asyncio.sleep(0)
        return results
