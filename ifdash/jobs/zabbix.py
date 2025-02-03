from ifdash import client
from rq import Queue, Connection
from redis import Redis
from rq.job import Job
from ifdash.utils import config
from datetime import datetime
import json

host_url = "localhost"
port = 6379
redis_conn = Redis(host_url, port)
q = Queue(connection=redis_conn)
settings = config.get_settings()
zabbix_url = settings.get("ZABBIX_URL")
zabbix_token = settings.get("ZABBIX_TOKEN")


def get_event_count(event):
    zabbix_client = client.zabbix_client.ZabbixClient(
        zabbix_url,
        zabbix_token,
    )
    print("begin work")
    data = zabbix_client.get_event_count(event)
    print("xxx", data)
    return data


def get_event(groupid, start_date, end_date):
    print(zabbix_url)
    zabbix_client = client.zabbix_client.ZabbixClient(
        zabbix_url,
        zabbix_token,
    )
    print("begin work")
    data = zabbix_client.get_event(groupid, start_date, end_date)
    print(">>>>>>done", type(data))
    return data


def get_duration(events):
    zabbix_client = client.zabbix_client.ZabbixClient(
        zabbix_url,
        zabbix_token,
    )

    print("begin work")
    data = zabbix_client.get_duration(events)
    print(">>>>>>done")
    return data


def get_duration(event_id_list, r_event_id_list):
    zabbix_client = client.zabbix_client.ZabbixClient(
        zabbix_url,
        zabbix_token,
    )
    events = zabbix_client.get_r_event(event_id_list)
    r_events = zabbix_client.get_r_event(r_event_id_list)
    result = []
    for event in events.result:
        if event.r_eventid == "0":
            duration = {"eventid": event.eventid, "duration": "0"}
            result.append(duration)
            continue
        for r_event in r_events.result:
            # print(event.r_eventid, r_event.eventid)
            if event.r_eventid == r_event.eventid:
                duration = {
                    "eventid": event.eventid,
                    "duration": datetime.fromtimestamp(int(r_event.clock))
                    - datetime.fromtimestamp(int(event.clock)),
                }
                result.append(duration)
    return result


def get_r_event(eventid):
    zabbix_client = client.zabbix_client.ZabbixClient(
        zabbix_url,
        zabbix_token,
    )
    print("begin work")
    data = zabbix_client.get_event(eventid)
    print(">>>>>>done")
    return data


def get_status(task_id):
    job = Job.fetch(task_id, connection=redis_conn)
    status = job.get_status()
    result = job.result

    if status == "finished":
        return json.dumps({"status": "success", "result": result})
    elif status == "failed":
        return json.dumps({"status": "failed", "result": result})

    return json.dumps({"status": "processing"})
