import datetime

from beanie import Document, TimeSeriesConfig, Granularity, Indexed
from pydantic import Field, BaseModel


class SLAMetadata(BaseModel):
    type: str
    periodicity: str = "daily"

    year: int = 0
    month: int = 0
    day: int = 0
    count: int = 0

    started_date: datetime.datetime = Field(default_factory=datetime.datetime.now)
    ended_date: datetime.datetime = Field(default_factory=datetime.datetime.now)

    created_date: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_date: datetime.datetime = Field(default_factory=datetime.datetime.now)


class HostSLAMetadata(SLAMetadata):
    id: str
    name: str | None = None
    host_name: str | None = None
    groups: list = []
    labels: dict = dict()


class GroupSLAMetadata(SLAMetadata):
    name: str | None = None


class HostBaseSLA(Document):
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    metadata: HostSLAMetadata = Field(default_factory=HostSLAMetadata)
    sla: float


class GroupBaseSLA(HostBaseSLA):
    metadata: GroupSLAMetadata = Field(default_factory=GroupSLAMetadata)


class SLA(HostBaseSLA):
    class Settings:
        name = "slas"
        timeseries = TimeSeriesConfig(time_field="timestamp", meta_field="metadata")


class GroupSLA(GroupBaseSLA):
    class Settings:
        name = "group_slas"
        timeseries = TimeSeriesConfig(time_field="timestamp", meta_field="metadata")
