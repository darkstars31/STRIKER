from dataclasses import dataclass
from uuid import UUID

from bot import config
from domain.domain import Job


class Event:
    pass


@dataclass(frozen=True)
class TestEvent(Event):
    field: int


# MATCHINFO


@dataclass(frozen=True)
class MatchInfoSuccess(Event):
    id: int
    matchid: int
    matchtime: int
    url: str


@dataclass(frozen=True)
class MatchInfoFailure(Event):
    id: int
    reason: str


@dataclass(frozen=True)
class MatchInfoEnqueued(Event):
    id: int
    infront: int


@dataclass(frozen=True)
class MatchInfoProcessing(Event):
    id: int


# demoparse


# repr removed because it caused a fuckton of
# console spam
@dataclass(frozen=True, repr=config.DUMP_EVENTS)
class DemoParseSuccess(Event):
    id: int
    data: dict
    version: int


@dataclass(frozen=True)
class DemoParseFailure(Event):
    id: int
    reason: str


@dataclass(frozen=True)
class DemoParseEnqueued(Event):
    id: int
    infront: int


@dataclass(frozen=True)
class DemoParseProcessing(Event):
    id: int


# recorder


@dataclass(frozen=True)
class RecorderSuccess(Event):
    id: UUID


@dataclass(frozen=True)
class RecorderFailure(Event):
    id: UUID
    reason: str


@dataclass(frozen=True)
class RecorderEnqueued(Event):
    id: UUID
    infront: int


@dataclass(frozen=True)
class RecorderProcessing(Event):
    id: UUID


# uploader
@dataclass(frozen=True)
class UploaderSuccess(Event):
    id: UUID


@dataclass(frozen=True)
class UploaderFailure(Event):
    id: UUID
    reason: str


# job


@dataclass(frozen=True)
class JobEvent(Event):
    job: Job
    event: Event


@dataclass(frozen=True)
class JobMatchInfoFailed(Event):
    job: Job
    reason: str


@dataclass(frozen=True)
class JobDemoParseFailed(Event):
    job: Job
    reason: str


@dataclass(frozen=True)
class JobRecordingFailed(Event):
    job: Job
    reason: str


@dataclass(frozen=True)
class JobReadyForSelect(Event):
    job: Job


@dataclass(frozen=True)
class JobUploadSuccess(Event):
    job: Job


@dataclass(frozen=True)
class JobUploadFailed(Event):
    job: Job
    reason: str
