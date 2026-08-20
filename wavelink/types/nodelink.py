from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, TypedDict

from typing_extensions import NotRequired


if TYPE_CHECKING:
    from .tracks import TrackPayload


class LyricsLinePayload(TypedDict):
    text: str
    time: int
    duration: int


class LyricsDataPayload(TypedDict, total=False):
    name: str
    synced: bool
    lines: list[LyricsLinePayload]
    provider: str
    message: str
    severity: str


class LyricsPayload(TypedDict):
    loadType: Literal["lyrics", "empty", "error"]
    data: LyricsDataPayload


class ThumbnailPayload(TypedDict):
    url: str
    width: NotRequired[int]
    height: NotRequired[int]


class ChapterPayload(TypedDict):
    title: str
    startTime: int
    thumbnails: list[ThumbnailPayload]
    duration: NotRequired[int]
    endTime: NotRequired[int]


class MixPayload(TypedDict):
    id: str
    track: TrackPayload
    volume: float
    position: NotRequired[int]
    startTime: NotRequired[int]


class MixesPayload(TypedDict):
    mixes: list[MixPayload]


class SponsorBlockSegmentPayload(TypedDict):
    uuid: str
    start: int
    end: int
    category: str
    actionType: str
    votes: int
    locked: bool
    videoDuration: int
    description: str


class SponsorBlockStatePayload(TypedDict):
    enabled: bool
    categories: list[str]
    actionTypes: list[str]
    segments: list[SponsorBlockSegmentPayload]
    lastSkippedUuid: str | None
    skipMarginMs: int


class SponsorBlockUpdatePayload(TypedDict, total=False):
    enabled: bool
    categories: list[str]
    actionTypes: list[str]
    skipMarginMs: int


class NodeLinkPluginPayload(TypedDict):
    name: str
    version: str
    author: NotRequired[str | None]
    path: NotRequired[str | None]


class NodeLinkInfoPayload(TypedDict, total=False):
    node: str
    voice: dict[str, Any]
    isNodelink: bool
