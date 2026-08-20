from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast

import aiohttp

from .tracks import Playable


if TYPE_CHECKING:
    from types import TracebackType

    from .node import Node
    from .types.nodelink import (
        ChapterPayload,
        LyricsLinePayload,
        LyricsPayload,
        MixPayload,
        SponsorBlockSegmentPayload,
        SponsorBlockStatePayload,
    )


__all__ = (
    "Chapter",
    "Lyrics",
    "LyricsLine",
    "Mix",
    "SponsorBlockSegment",
    "SponsorBlockState",
    "VoiceFrame",
    "VoiceReceiver",
)


class LyricsLine:
    def __init__(self, data: LyricsLinePayload) -> None:
        self.text: str = data["text"]
        self.time: int = data["time"]
        self.duration: int = data["duration"]


class Lyrics:
    def __init__(self, data: LyricsPayload) -> None:
        payload = data["data"]

        self.load_type: Literal["lyrics", "empty", "error"] = data["loadType"]
        self.name: str | None = payload.get("name")
        self.synced: bool = payload.get("synced", False)
        self.lines: list[LyricsLine] = [LyricsLine(line) for line in payload.get("lines", [])]
        self.provider: str | None = payload.get("provider")
        self.message: str | None = payload.get("message")
        self.severity: str | None = payload.get("severity")


class Chapter:
    def __init__(self, data: ChapterPayload) -> None:
        self.title: str = data["title"]
        self.start_time: int = data["startTime"]
        self.duration: int | None = data.get("duration")
        self.end_time: int | None = data.get("endTime")
        self.thumbnails: list[dict[str, object]] = [dict(thumbnail) for thumbnail in data["thumbnails"]]


class Mix:
    def __init__(self, data: MixPayload) -> None:
        self.id: str = data["id"]
        self.track: Playable = Playable(data["track"])
        self.volume: float = data["volume"]
        self.position: int | None = data.get("position")
        self.start_time: int | None = data.get("startTime")


class SponsorBlockSegment:
    def __init__(self, data: SponsorBlockSegmentPayload) -> None:
        self._raw_data = data
        self.uuid: str = data["uuid"]
        self.start: int = data["start"]
        self.end: int = data["end"]
        self.category: str = data["category"]
        self.action_type: str = data["actionType"]
        self.votes: int = data["votes"]
        self.locked: bool = data["locked"]
        self.video_duration: int = data["videoDuration"]
        self.description: str = data["description"]

    @property
    def raw_data(self) -> SponsorBlockSegmentPayload:
        return self._raw_data.copy()


class SponsorBlockState:
    def __init__(self, data: SponsorBlockStatePayload) -> None:
        self.enabled: bool = data["enabled"]
        self.categories: list[str] = data["categories"]
        self.action_types: list[str] = data["actionTypes"]
        self.segments: list[SponsorBlockSegment] = [SponsorBlockSegment(segment) for segment in data["segments"]]
        self.last_skipped_uuid: str | None = data["lastSkippedUuid"]
        self.skip_margin_ms: int = data["skipMarginMs"]


@dataclass(frozen=True)
class VoiceFrame:
    op: Literal[1, 2, 3]
    format: Literal[0, 1, 2]
    guild_id: int
    user_id: int
    ssrc: int
    timestamp: int
    data: bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> VoiceFrame:
        if len(data) < 12:
            raise ValueError("Voice frame is too short.")

        op, format_, guild_length = struct.unpack_from("!BBB", data)
        offset = 3
        user_length_offset = offset + guild_length

        if user_length_offset >= len(data):
            raise ValueError("Voice frame has an invalid guild ID length.")

        guild_id = data[offset:user_length_offset].decode("utf-8")
        user_length = cast("int", data[user_length_offset])
        offset = user_length_offset + 1
        header_end = offset + user_length + 8

        if header_end > len(data):
            raise ValueError("Voice frame has an invalid user ID length.")

        user_id = data[offset : offset + user_length].decode("utf-8")
        ssrc, timestamp = struct.unpack_from("!II", data, offset + user_length)

        if op not in (1, 2, 3) or format_ not in (0, 1, 2):
            raise ValueError("Voice frame has an unknown operation or format.")

        return cls(
            op=op,
            format=format_,
            guild_id=int(guild_id),
            user_id=int(user_id),
            ssrc=ssrc,
            timestamp=timestamp,
            data=data[header_end:],
        )


class VoiceReceiver:
    def __init__(self, *, node: Node, guild_id: int) -> None:
        self.node = node
        self.guild_id = guild_id
        self.socket: aiohttp.ClientWebSocketResponse[bool] | None = None

    async def connect(self) -> VoiceReceiver:
        headers = self.node.headers
        if self.node.session_id:
            headers["Session-Id"] = self.node.session_id

        uri = f"{self.node.uri}/v4/websocket/voice/{self.guild_id}"
        self.socket = await self.node._session.ws_connect(uri, headers=headers, heartbeat=self.node.heartbeat)
        return self

    async def receive(self) -> VoiceFrame:
        if self.socket is None:
            raise RuntimeError("VoiceReceiver is not connected.")

        message = await self.socket.receive()
        if message.type is aiohttp.WSMsgType.BINARY:
            return VoiceFrame.from_bytes(message.data)
        if message.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING):
            raise StopAsyncIteration

        raise ValueError(f"Unexpected voice websocket message type: {message.type!r}")

    async def close(self) -> None:
        if self.socket is not None:
            await self.socket.close()
            self.socket = None

    def __aiter__(self) -> VoiceReceiver:
        return self

    async def __anext__(self) -> VoiceFrame:
        return await self.receive()

    async def __aenter__(self) -> VoiceReceiver:
        return await self.connect()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()
