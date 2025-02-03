import datetime

from beanie import Document, TimeSeriesConfig, Granularity, Indexed
from pydantic import Field, BaseModel


class Metadata(BaseModel):
    id: Indexed(str)
    name: Indexed(str)
    host_name: str | None = None
    address: str | None = None
    downtime: bool = False
    duration: float | None = None

    groups: list = []
    labels: dict = {}
    created_date: datetime.datetime = Field(default_factory=datetime.datetime.now)


class BaseTelemety(Document):
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    metadata: Metadata = Field(default_factory=Metadata)
    state: int


class HostState(BaseTelemety):
    class Settings:
        name = "host_states"
        timeseries = TimeSeriesConfig(time_field="timestamp", meta_field="metadata")


class VMState(BaseTelemety):
    class Settings:
        name = "vm_states"
        timeseries = TimeSeriesConfig(time_field="timestamp", meta_field="metadata")


class APState(BaseTelemety):
    class Settings:
        name = "ap_states"
        timeseries = TimeSeriesConfig(time_field="timestamp", meta_field="metadata")


class ServiceState(BaseTelemety):
    class Settings:
        name = "service_states"
        timeseries = TimeSeriesConfig(time_field="timestamp", meta_field="metadata")
