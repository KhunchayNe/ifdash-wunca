import asyncio
from dotenv import dotenv_values

import datetime
import json
import pathlib
import logging
import threading
import queue
import time

logger = logging.getLogger(__name__)


from ifdash import models, clients

from . import storage
from . import checkmk
from . import uptime_kuma
from . import sla
from . import web_display

import json

# from crontab import Crontab


class Controller:
    def __init__(self, name="Controller", settings: dict = dict()):
        self.name = name
        self.settings = settings
        self.running = False

    async def run(self):
        self.running = True
        while self.running:
            print("Controller Running")
            await asyncio.sleep(1)

    async def start(self):
        self.running = True
        await self.run()

    async def stop(self):
        self.running = False


class TaskController(Controller):
    def __init__(self, name="TaskController", settings: dict = dict()):
        super().__init__(name, settings)
        self.tasks = []
        self.monitor_task = None

    async def monitor(self):
        while self.running:
            await asyncio.sleep(1)

            done_tasks = [t for t in self.tasks if t.done()]
            for task in done_tasks:
                result = await task
                self.tasks.remove(task)

            if len(done_tasks) > 0:
                print(f"{self.name} remove task: {len(done_tasks)}")

    async def create_task(self):
        self.monitor_task = asyncio.create_task(self.monitor())

    async def start(self):
        self.running = True
        await self.create_task()
        await self.run()

    async def stop(self):
        self.running = False
        await self.monitor_task


class MonitorController(TaskController):
    def __init__(self, settings: dict = dict(), queues: list[asyncio.Queue] = []):
        super().__init__("Monitor Controller", settings)

        self.queues = queues

        self.managers = []

    async def register_monitors(self):
        self.managers = []
        for monitor in self.settings.get("MONITORS", []):
            match monitor:
                case "checkmk":
                    self.managers.append(
                        checkmk.CheckMKManager(self.settings, self.queues)
                    )
                case "uptime-kuma":
                    self.managers.append(
                        uptime_kuma.UptimeKumaManager(self.settings, self.queues)
                    )

        print("monitors:", self.settings.get("MONITORS"))

    async def initial(self):
        await self.register_monitors()

    async def create_aquisition_task(self):
        for manager in self.managers:
            self.tasks.append(asyncio.create_task(manager.get()))

    async def run(self):
        time_to_sleep = 60

        await self.initial()

        while self.running:
            weakup_time = datetime.datetime.now()

            await self.create_aquisition_task()

            diff_time = datetime.datetime.now() - weakup_time
            sleep_time = time_to_sleep - (
                diff_time.seconds + (diff_time.microseconds * 1e-6)
            )

            print("monitor sleep time >", sleep_time)

            await asyncio.sleep(sleep_time)

        self.running = False


class DataStoreController(TaskController):
    def __init__(self, settings: dict = dict(), queue=None):
        super().__init__("DataStoreController", settings)

        self.queue = queue

        self.storage_manager = None

    async def initial(self):
        self.storage_manager = storage.StorageManager(self.settings)
        await self.storage_manager.initial()

    async def database_task(self, queue):
        while self.running:
            if queue.empty():
                await asyncio.sleep(1)
                continue

            print(
                self.name,
                "process",
                queue.qsize(),
                datetime.datetime.now(tz=datetime.timezone.utc),
            )

            while not self.queue.empty():
                data = self.queue.get()

                await self.storage_manager.save(data)

    async def run(self):
        await self.initial()

        database_task = asyncio.create_task(self.database_task(self.queue))

        await database_task


class SummaryController(Controller):
    def __init__(self, settings: dict = dict()):
        super().__init__("SummaryController", settings)

        self.sla_summarizer = None

    async def initial(self):
        self.sla_summarizer = sla.Summarizer()
        await self.sla_summarizer.initial()

    async def run(self):
        await self.initial()
        # time_to_sleep = 24 * 60 * 60
        time_to_work = "01:00"

        time_part = time_to_work.split(":")
        hour = int(time_part[0])
        minute = int(time_part[1])

        while self.running:
            if not self.sla_summarizer:
                print("wait for summarizer")
                await asyncio.sleep(1)
                continue

            weakup_time = datetime.datetime.now()
            # if weakup_time.hour < hour and weakup_time.minute < minute:
            #     continue

            end_time = datetime.datetime.combine(
                weakup_time.date(), datetime.datetime.min.time()
            )
            start_time = end_time - datetime.timedelta(days=1)

            print(
                "SLA summarizer",
                start_time,
                end_time,
            )
            await self.sla_summarizer.summarize_daily(
                start_time, end_time, "Asia/Bangkok"
            )

            await self.sla_summarizer.summarize_groups_daily(
                start_time, end_time, "Asia/Bangkok"
            )

            # if weakup_time.day == 1:
            end_time = datetime.datetime.combine(
                weakup_time.date(), datetime.datetime.min.time()
            )
            start_time = (end_time - datetime.timedelta(days=1)).replace(day=1)

            await self.sla_summarizer.summarize_monthly(
                start_time, end_time, "Asia/Bangkok"
            )
            await self.sla_summarizer.summarize_groups_monthly(
                start_time, end_time, "Asia/Bangkok"
            )

            current_time = datetime.datetime.now()
            next_time = weakup_time + datetime.timedelta(days=1)
            next_time = next_time.replace(hour=hour, minute=minute)
            sleep_time = (next_time - current_time).total_seconds()

            print("SLA sleep time >", sleep_time)

            await asyncio.sleep(sleep_time)


class WebDisplayController(Controller):
    def __init__(self, settings: dict = dict(), queue=asyncio.Queue()):
        super().__init__("WebDisplayController", settings)
        self.running = False
        self.queue = queue

        self.web_display = web_display.WebDisplay(self.settings)

    async def run(self):
        time_to_sleep = 60
        self.running = True

        # sla_task = asyncio.create_task(self.process_slas_task())

        # await self.web_display.get_groups_sla()
        while self.running:
            weakup_time = datetime.datetime.now()
            seconds = int(weakup_time.timestamp())

            if not self.queue.empty():
                data = self.queue.get()
                print(self.name, weakup_time)
                await self.web_display.process_current_state(data)

            await self.web_display.get_campuses_states()

            # if seconds % (10 * 60) == 0:
            #     await self.web_display.get_groups_sla()

            await asyncio.sleep(1)


class ControllerServer:
    def __init__(self, settings: dict = dict()):
        self.settings = settings
        self.data_store_queue = queue.Queue()
        self.web_display_queue = queue.Queue()

    async def get_config(self):
        self.settings = dotenv_values(".env")
        for k in self.settings:
            if self.settings[k].strip()[0] in ["[", "{"]:
                self.settings[k] = json.loads(self.settings[k])

    async def initial(self):
        if not self.settings:
            await self.get_config()

    def run_monitor_thread(self):
        print("start monitor controller")
        monitor = MonitorController(
            self.settings, [self.data_store_queue, self.web_display_queue]
        )
        asyncio.run(monitor.start())

    def run_data_store_thread(self):
        print("start data store controller")
        data_store = DataStoreController(self.settings, self.data_store_queue)
        asyncio.run(data_store.start())

    def run_summary_thread(self):
        print("start summary controller")
        summary = SummaryController(self.settings)
        asyncio.run(summary.start())

    def run_display_process_thread(self):
        print("start display process controller")
        web_display = WebDisplayController(self.settings, self.web_display_queue)
        asyncio.run(web_display.start())

    def run(self):

        asyncio.run(self.initial())

        print("intitial worker thread")
        self.monitor_thread = threading.Thread(target=self.run_monitor_thread)
        self.data_store_thread = threading.Thread(target=self.run_data_store_thread)
        self.summary_thread = threading.Thread(target=self.run_summary_thread)
        self.web_display_thread = threading.Thread(
            target=self.run_display_process_thread
        )

        threads = [
            self.monitor_thread,
            self.data_store_thread,
            self.summary_thread,
            self.web_display_thread,
        ]

        print("start worker thread")
        for thread in threads:
            thread.start()
            thread.deamon = True
            time.sleep(1)

        print("join worker thread")
        try:
            for thread in threads:
                thread.join()

        except Exception as e:
            print("Error >>> ", e)
            for thread in threads:
                thread.stop()

        print("end worker thread")
