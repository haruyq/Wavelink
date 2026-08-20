from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeAlias, TypedDict


if TYPE_CHECKING:
    from typing_extensions import NotRequired

    from .nodelink import SponsorBlockSegmentPayload
    from .state import PlayerState
    from .stats import CPUStats, FrameStats, MemoryStats
    from .tracks import TrackPayload


class TrackExceptionPayload(TypedDict):
    message: NotRequired[str]
    severity: str
    cause: str


class ReadyOP(TypedDict):
    op: Literal["ready"]
    resumed: bool
    sessionId: str


class PlayerUpdateOP(TypedDict):
    op: Literal["playerUpdate"]
    guildId: str
    state: PlayerState


class StatsOP(TypedDict):
    op: Literal["stats"]
    players: int
    playingPlayers: int
    uptime: int
    memory: MemoryStats
    cpu: CPUStats
    frameStats: NotRequired[FrameStats | None]


class TrackStartEvent(TypedDict):
    op: Literal["event"]
    guildId: str
    type: Literal["TrackStartEvent"]
    track: TrackPayload


class TrackEndEvent(TypedDict):
    op: Literal["event"]
    guildId: str
    type: Literal["TrackEndEvent"]
    track: TrackPayload
    reason: str


class TrackExceptionEvent(TypedDict):
    op: Literal["event"]
    guildId: str
    type: Literal["TrackExceptionEvent"]
    track: TrackPayload
    exception: TrackExceptionPayload


class TrackStuckEvent(TypedDict):
    op: Literal["event"]
    guildId: str
    type: Literal["TrackStuckEvent"]
    track: TrackPayload
    thresholdMs: int


class WebsocketClosedEvent(TypedDict):
    op: Literal["event"]
    guildId: str
    type: Literal["WebSocketClosedEvent"]
    code: int
    reason: str
    byRemote: bool


class MixStartedEvent(TypedDict):
    op: Literal["event"]
    guildId: str
    type: Literal["MixStartedEvent"]
    mixId: str
    track: TrackPayload
    volume: float


class MixEndedEvent(TypedDict):
    op: Literal["event"]
    guildId: str
    type: Literal["MixEndedEvent"]
    mixId: str
    reason: str


class SponsorBlockSegmentsLoadedEvent(TypedDict):
    op: Literal["event"]
    guildId: str
    type: Literal["SponsorBlockSegmentsLoadedEvent"]
    segments: list[SponsorBlockSegmentPayload]


class SponsorBlockSegmentSkippedEvent(TypedDict):
    op: Literal["event"]
    guildId: str
    type: Literal["SponsorBlockSegmentSkippedEvent"]
    segment: SponsorBlockSegmentPayload
    skippedMs: int


WebsocketOP: TypeAlias = (
    ReadyOP
    | PlayerUpdateOP
    | StatsOP
    | TrackStartEvent
    | TrackEndEvent
    | TrackExceptionEvent
    | TrackStuckEvent
    | WebsocketClosedEvent
    | MixStartedEvent
    | MixEndedEvent
    | SponsorBlockSegmentsLoadedEvent
    | SponsorBlockSegmentSkippedEvent
)
