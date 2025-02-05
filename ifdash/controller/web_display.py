import pprint
import datetime
import zoneinfo
import asyncio
import time
import copy

from ifdash import models, services
import redis.asyncio as redis
from redis.commands.json.path import Path

import logging

logger = logging.getLogger(__name__)

CACHE_SLA_GROUP = 10 * 60
CACHE_STATE = 10 * 60
CACHE_CAMPUS_STATE = CACHE_SLA_GROUP


class WebDisplay:
    def __init__(self, settings: dict = dict()):
        self.settings = settings
        redis_pool = redis.ConnectionPool.from_url(
            settings.get("REDIS_URL", "redis://localhost")
        )
        self.redis_client = redis.Redis.from_pool(redis_pool)
        # self.sla_summarizer_service = services.sla_summarizers.SLASummarizerService()
        # self.models = dict(
        #     host=models.HostState, service=models.ServiceState, ap=models.APState
        # )
        self.granularity_mapers = dict(daily="day", monthly="month")

    async def process_current_state(self, datas):
        type_ = datas.get("type")

        state_map = dict(
            host=["up", "down", "warning", "unknow"],
            service=["up", "warning", "down", "unknow"],
            VM=["up", "warning", "down", "unknow"],
            AP=["up", "warning", "down", "unknow"],
        )

        for state_type, states in datas.get("data").items():
            groups = dict()
            for state in states:

                state = copy.deepcopy(state)
                state["checked_date"] = state["checked_date"].isoformat()
                state["state_name"] = state_map[state_type][state["state"]]
                state["type"] = state_type
                key = f"ifdash:state:{state.get('id', state.get('name', 'unknow'))}"
                # print("state", state)
                # print(key)
                await self.redis_client.json().set(key, Path.root_path(), state)
                await self.redis_client.expire(key, CACHE_STATE)

                for group_name in state.get("groups", []):
                    if group_name not in groups:
                        groups[group_name] = dict(
                            up=0,
                            down=0,
                            warning=0,
                            downtime=0,
                            unknow=0,
                            sla=0,
                            total=0,
                            hosts=[],
                        )

                    groups[group_name]["hosts"].append(
                        state.get("id", state.get("name", "unknow"))
                    )
                    groups[group_name][state_map[state_type][state["state"]]] += 1
                    if state["downtime"]:
                        groups[group_name][state_map[downtime]] += 1

            for name, status in groups.items():
                available = status["up"] + status["warning"]
                status["total"] = available + status["down"]
                if status["total"] > 0:
                    status["sla"] = available / status["total"] * 100

                group_key = f"ifdash:sla:group:{name}"
                await self.redis_client.json().set(group_key, Path.root_path(), status)
                await self.redis_client.expire(group_key, CACHE_SLA_GROUP)

    async def get_campuses_states(self):
        ISP_NAMES = ["Uninet", "NT", "3BB"]
        CAMPUS_PREFIXS = {
            "HDY": "hatyai",
            "PTN": "pattani",
            "SRT": "suratthani",
            "PKT": "phuket",
            "TRG": "trang",
        }

        now = datetime.datetime.now(datetime.timezone.utc)
        started_date = now - datetime.timedelta(minutes=2)
        ended_date = now

        group_name = "PSU-CORE-NETWORK"

        state_key = f"ifdash:sla:group:{group_name}"
        result = await self.redis_client.json().get(state_key)
        if not result:
            return

        data = {}
        for host_id in result.get("hosts", []):
            host_key = f"ifdash:state:{host_id}"
            host_state = await self.redis_client.json().get(host_key)
            data[host_id] = host_state

        # print("->", data)

        campus_state_count = {k: 0 for k in CAMPUS_PREFIXS.values()}

        for key, value in data.items():
            if not value:
                continue

            if key == "CSW":
                campus_state_count["hatyai"] += 2 if value.get("state") == 0 else 0
                continue

            name = ""
            for prefix, cname in CAMPUS_PREFIXS.items():
                if prefix in key:
                    name = cname
                    break

            if not name:
                continue

            campus_state_count[name] += 1 if value.get("state") == 0 else 0

        campus_state = dict()
        for key, value in campus_state_count.items():
            if value == 0:
                campus_state[key] = 1
            elif value == 1:
                campus_state[key] = 2
            elif value == 2:
                campus_state[key] = 0

        group_name = "ISP"

        state_key = f"ifdash:sla:group:{group_name}"
        result = await self.redis_client.json().get(state_key)
        if not result:
            return

        data = {}
        for host_id in result.get("hosts", []):
            host_key = f"ifdash:state:{host_id}"
            host_state = await self.redis_client.json().get(host_key)
            if not host_state:
                continue
            data[host_id] = host_state

        for key, value in data.items():
            if key in ISP_NAMES:
                campus_state[key] = value.get("state", 0)

        campus_state_key = f"ifdash:campus:state"
        await self.redis_client.json().set(
            campus_state_key, Path.root_path(), campus_state
        )
        await self.redis_client.expire(campus_state_key, CACHE_CAMPUS_STATE)

    async def get_groups_sla(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        print("Get groups SLA", now.astimezone(tz=zoneinfo.ZoneInfo("Asia/Bangkok")))

        group_names = []
