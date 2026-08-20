import asyncio
import struct
import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import wavelink


class NodeLinkTests(unittest.TestCase):
    def test_stats_cpu_load(self) -> None:
        lavalink = wavelink.StatsEventCPU({"cores": 4, "systemLoad": 0.25, "lavalinkLoad": 0.1})
        nodelink = wavelink.StatsEventPayload(
            {
                "op": "stats",
                "players": 1,
                "playingPlayers": 1,
                "uptime": 1000,
                "memory": {"free": 1, "used": 2, "allocated": 3, "reservable": 4},
                "cpu": {"cores": 4, "systemLoad": 0.25, "nodelinkLoad": 0.1},
            }
        )

        self.assertEqual(lavalink.lavalink_load, 0.1)
        self.assertIsNone(lavalink.nodelink_load)
        self.assertIsNone(nodelink.cpu.lavalink_load)
        self.assertEqual(nodelink.cpu.nodelink_load, 0.1)

    def test_voice_frame(self) -> None:
        guild_id = b"12345678901234567"
        user_id = b"23456789012345678"
        payload = b"opus"
        data = (
            struct.pack("!BBB", 3, 0, len(guild_id))
            + guild_id
            + struct.pack("!B", len(user_id))
            + user_id
            + struct.pack("!II", 42, 1000)
            + payload
        )

        frame = wavelink.VoiceFrame.from_bytes(data)

        self.assertEqual(frame.guild_id, int(guild_id))
        self.assertEqual(frame.user_id, int(user_id))
        self.assertEqual(frame.ssrc, 42)
        self.assertEqual(frame.data, payload)

    def test_nodelink_filters(self) -> None:
        filters = wavelink.Filters()
        filters.echo.set(delay=250, feedback=0.3, mix=0.2)
        filters.chorus.set(rate=1.5, depth=0.5)
        filters.compressor.set(threshold=-20, ratio=4, makeup_gain=2)
        filters.high_pass.set(smoothing=0.5)
        filters.phaser.set(rate=1, stages=4, min_frequency=300)
        filters.spatial.set(depth=0.8, rate=0.5)

        self.assertEqual(
            filters(),
            {
                "equalizer": [{"band": band, "gain": 0.0} for band in range(15)],
                "echo": {"delay": 250, "feedback": 0.3, "mix": 0.2},
                "chorus": {"rate": 1.5, "depth": 0.5},
                "compressor": {"threshold": -20, "ratio": 4, "makeupGain": 2},
                "highpass": {"smoothing": 0.5},
                "phaser": {"rate": 1, "stages": 4, "minFrequency": 300},
                "spatial": {"depth": 0.8, "rate": 0.5},
            },
        )

    def test_nodelink_info(self) -> None:
        payload = wavelink.InfoResponsePayload(
            {
                "version": {"semver": "3.5.0", "major": 3, "minor": 5, "patch": 0},
                "buildTime": 0,
                "git": {"branch": "v3", "commit": "abcdef", "commitTime": 0},
                "node": "v24.0.0",
                "isNodelink": True,
                "sourceManagers": ["youtube"],
                "filters": ["echo"],
                "plugins": [],
            }
        )

        self.assertTrue(payload.is_nodelink)
        self.assertEqual(payload.node, "v24.0.0")
        self.assertIsNone(payload.jvm)
        self.assertIsNone(payload.lavaplayer)


class NodeLinkAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_voice_update_when_server_event_arrives_first(self) -> None:
        player: Any = object.__new__(wavelink.Player)
        player._guild = SimpleNamespace(id=123)
        player._voice_state = {"voice": {"token": "token", "endpoint": "voice.discord.media"}}
        player._node = SimpleNamespace(_update_player=AsyncMock(return_value={}))
        player._connection_event = asyncio.Event()
        player._connected = False

        def get_channel(channel_id: int) -> int:
            return channel_id

        player.client = SimpleNamespace(get_channel=get_channel)

        await player.on_voice_state_update({"channel_id": "456", "session_id": "session"})

        player.node._update_player.assert_awaited_once_with(
            123,
            data={
                "voice": {
                    "sessionId": "session",
                    "token": "token",
                    "endpoint": "voice.discord.media",
                    "channelId": "456",
                }
            },
        )
        self.assertTrue(player._connection_event.is_set())


if __name__ == "__main__":
    unittest.main()
