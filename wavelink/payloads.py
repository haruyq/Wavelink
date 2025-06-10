from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, cast

import wavelink

from .enums import DiscordVoiceCloseType
from .filters import Filters
from .tracks import Playable


if TYPE_CHECKING:
    from .node import Node
    from .player import Player
    from .types.filters import *
    from .types.response import *
    from .types.state import PlayerState
    from .types.stats import CPUStats, FrameStats, MemoryStats
    from .types.websocket import StatsOP, TrackExceptionPayload


__all__ = (
    "TrackStartEventPayload",
    "TrackEndEventPayload",
    "TrackExceptionEventPayload",
    "TrackStuckEventPayload",
    "WebsocketClosedEventPayload",
    "PlayerUpdateEventPayload",
    "StatsEventPayload",
    "NodeReadyEventPayload",
    "NodeDisconnectedEventPayload",
    "StatsEventMemory",
    "StatsEventCPU",
    "StatsEventFrames",
    "StatsResponsePayload",
    "GitResponsePayload",
    "VersionResponsePayload",
    "PluginResponsePayload",
    "InfoResponsePayload",
    "PlayerStatePayload",
    "VoiceStatePayload",
    "PlayerResponsePayload",
    "ExtraEventPayload",
)


class NodeReadyEventPayload:
    """:func:`on_wavelink_node_ready` イベントで受け取るペイロード

    Attributes
    ----------
    node: :class:`~wavelink.Node`
        接続または再接続したノード
    resumed: bool
        このノードが正常にレジューム（再開）できたかどうか
    session_id: str
        このノードに紐づくセッションID
    """

    def __init__(self, node: Node, resumed: bool, session_id: str) -> None:
        self.node = node
        self.resumed = resumed
        self.session_id = session_id


class NodeDisconnectedEventPayload:
    """:func:`on_wavelink_node_disconnected` イベントで受け取るペイロード

    Attributes
    ----------
    node: :class:`~wavelink.Node`
        切断されたノード
    """

    def __init__(self, node: Node) -> None:
        self.node = node


class TrackStartEventPayload:
    """:func:`on_wavelink_track_start` イベントで受け取るペイロード

    Attributes
    ----------
    player: :class:`~wavelink.Player` | None
        このイベントに紐づくプレイヤー。Noneの場合もある
    track: :class:`~wavelink.Playable`
        このイベントでLavalinkから受け取ったトラック
    original: :class:`~wavelink.Playable` | None
        このイベントに紐づく元のトラック。:meth:`~wavelink.Player.play` で渡したり、キューに追加したトラックなど。Noneの場合もある
    """

    def __init__(self, player: Player | None, track: Playable) -> None:
        self.player = player
        self.track = track
        self.original: Playable | None = None

        if player:
            self.original = player._original


class TrackEndEventPayload:
    """:func:`on_wavelink_track_end` イベントで受け取るペイロード

    Attributes
    ----------
    player: :class:`~wavelink.Player` | None
        このイベントに紐づくプレイヤー。Noneの場合もある
    track: :class:`~wavelink.Playable`
        このイベントでLavalinkから受け取ったトラック
    reason: str
        このトラックが終了した理由
    original: :class:`~wavelink.Playable` | None
        このイベントに紐づく元のトラック。:meth:`~wavelink.Player.play` で渡したり、キューに追加したトラックなど。Noneの場合もある
    """

    def __init__(self, player: Player | None, track: Playable, reason: str) -> None:
        self.player = player
        self.track = track
        self.reason = reason
        self.original: Playable | None = None

        if player:
            self.original = player._previous


class TrackExceptionEventPayload:
    """:func:`on_wavelink_track_exception` イベントで受け取るペイロード

    Attributes
    ----------
    player: :class:`~wavelink.Player` | None
        このイベントに紐づくプレイヤー。Noneの場合もある
    track: :class:`~wavelink.Playable`
        このイベントでLavalinkから受け取ったトラック
    exception: TrackExceptionPayload
        Lavalinkから受け取った例外データ
    """

    def __init__(self, player: Player | None, track: Playable, exception: TrackExceptionPayload) -> None:
        self.player = cast(wavelink.Player, player)
        self.track = track
        self.exception = exception


class TrackStuckEventPayload:
    """:func:`on_wavelink_track_stuck` イベントで受け取るペイロード

    Attributes
    ----------
    player: :class:`~wavelink.Player` | None
        このイベントに紐づくプレイヤー。Noneの場合もある
    track: :class:`~wavelink.Playable`
        このイベントでLavalinkから受け取ったトラック
    threshold: int
        このイベントに紐づくLavalinkのしきい値
    """

    def __init__(self, player: Player | None, track: Playable, threshold: int) -> None:
        self.player = cast(wavelink.Player, player)
        self.track = track
        self.threshold = threshold


class WebsocketClosedEventPayload:
    """:func:`on_wavelink_websocket_closed` イベントで受け取るペイロード

    Attributes
    ----------
    player: :class:`~wavelink.Player` | None
        このイベントに紐づくプレイヤー。Noneの場合もある
    code: :class:`wavelink.DiscordVoiceCloseType`
        WebSocketのクローズコード(enum)
    reason: str
        WebSocketが閉じられた理由
    by_remote: bool
        Discord側でWebSocketが閉じられた場合はTrue、それ以外はFalse
    """

    def __init__(self, player: Player | None, code: int, reason: str, by_remote: bool) -> None:
        self.player = player
        self.code: DiscordVoiceCloseType = DiscordVoiceCloseType(code)
        self.reason = reason
        self.by_remote = by_remote


class PlayerUpdateEventPayload:
    """:func:`on_wavelink_player_update` イベントで受け取るペイロード

    Attributes
    ----------
    player: :class:`~wavelink.Player` | None
        このイベントに紐づくプレイヤー。Noneの場合もある
    time: int
        このイベントが発火した時刻（UNIXミリ秒）
    position: int
        現在再生中のトラックの位置（ミリ秒）
    connected: bool
        Lavalinkがボイスゲートウェイに接続しているかどうか
    ping: int
        ノードからDiscordボイスサーバーへのping（ミリ秒、未接続時は-1）
    """

    def __init__(self, player: Player | None, state: PlayerState) -> None:
        self.player = cast(wavelink.Player, player)
        self.time: int = state["time"]
        self.position: int = state["position"]
        self.connected: bool = state["connected"]
        self.ping: int = state["ping"]


class StatsEventMemory:
    """メモリ統計情報を表現するクラス

    Attributes
    ----------
    free: int
        空きメモリ量（バイト単位）
    used: int
        使用中メモリ量（バイト単位）
    allocated: int
        割り当て済みメモリ量（バイト単位）
    reservable: int
        予約可能なメモリ量（バイト単位）
    """

    def __init__(self, data: MemoryStats) -> None:
        self.free: int = data["free"]
        self.used: int = data["used"]
        self.allocated: int = data["allocated"]
        self.reservable: int = data["reservable"]


class StatsEventCPU:
    """CPU統計情報を表現するクラス

    Attributes
    ----------
    cores: int
        このノードで利用可能なCPUコア数
    system_load: float
        ノード全体のシステム負荷
    lavalink_load: float
        ノード上のLavalinkの負荷
    """

    def __init__(self, data: CPUStats) -> None:
        self.cores: int = data["cores"]
        self.system_load: float = data["systemLoad"]
        self.lavalink_load: float = data["lavalinkLoad"]


class StatsEventFrames:
    """フレーム統計情報を表現するクラス

    Attributes
    ----------
    sent: int
        Discordへ送信されたフレーム数
    nulled: int
        無効化されたフレーム数
    deficit: int
        送信フレーム数と期待されるフレーム数との差分
    """

    def __init__(self, data: FrameStats) -> None:
        self.sent: int = data["sent"]
        self.nulled: int = data["nulled"]
        self.deficit: int = data["deficit"]


class StatsEventPayload:
    """:func:`on_wavelink_stats_update` イベントで受け取るペイロード

    Attributes
    ----------
    players: int
        このノード（Lavalink）に接続されているプレイヤー数
    playing: int
        トラックを再生中のプレイヤー数
    uptime: int
        ノードの稼働時間（ミリ秒）
    memory: :class:`wavelink.StatsEventMemory`
        詳細は :class:`wavelink.StatsEventMemory` を参照
    cpu: :class:`wavelink.StatsEventCPU`
        詳細は :class:`wavelink.StatsEventCPU` を参照
    frames: :class:`wavelink.StatsEventFrames` | None
        詳細は :class:`wavelink.StatsEventFrames` を参照。Noneの場合もある
    """

    def __init__(self, data: StatsOP) -> None:
        self.players: int = data["players"]
        self.playing: int = data["playingPlayers"]
        self.uptime: int = data["uptime"]

        self.memory: StatsEventMemory = StatsEventMemory(data=data["memory"])
        self.cpu: StatsEventCPU = StatsEventCPU(data=data["cpu"])
        self.frames: StatsEventFrames | None = None

        if frames := data.get("frameStats", None):
            self.frames = StatsEventFrames(frames)


class StatsResponsePayload:
    """:meth:`~wavelink.Node.fetch_stats` で受け取るペイロード

    Attributes
    ----------
    players: int
        このノード（Lavalink）に接続されているプレイヤー数
    playing: int
        トラックを再生中のプレイヤー数
    uptime: int
        ノードの稼働時間（ミリ秒）
    memory: :class:`wavelink.StatsEventMemory`
        詳細は :class:`wavelink.StatsEventMemory` を参照
    cpu: :class:`wavelink.StatsEventCPU`
        詳細は :class:`wavelink.StatsEventCPU` を参照
    frames: :class:`wavelink.StatsEventFrames` | None
        詳細は :class:`wavelink.StatsEventFrames` を参照。Noneの場合もある
    """

    def __init__(self, data: StatsResponse) -> None:
        self.players: int = data["players"]
        self.playing: int = data["playingPlayers"]
        self.uptime: int = data["uptime"]

        self.memory: StatsEventMemory = StatsEventMemory(data=data["memory"])
        self.cpu: StatsEventCPU = StatsEventCPU(data=data["cpu"])
        self.frames: StatsEventFrames | None = None

        if frames := data.get("frameStats", None):
            self.frames = StatsEventFrames(frames)


class PlayerStatePayload:
    """:meth:`~wavelink.Node.fetch_player_info` または :meth:`~wavelink.Node.fetch_players` で受け取るPlayerState情報を表現するクラス

    Attributes
    ----------
    time: int
        Lavalinkから受信したUNIXタイムスタンプ（ミリ秒）
    position: int
        Lavalinkから受信したトラックの再生位置（ミリ秒）
    connected: bool
        Lavalinkがボイスゲートウェイに接続しているかどうか
    ping: int
        ノードからDiscordボイスサーバーへのping（ミリ秒、未接続時は-1）
    """

    def __init__(self, data: PlayerState) -> None:
        self.time: int = data["time"]
        self.position: int = data["position"]
        self.connected: bool = data["connected"]
        self.ping: int = data["ping"]


class VoiceStatePayload:
    """:meth:`~wavelink.Node.fetch_player_info` または :meth:`~wavelink.Node.fetch_players` で受け取るVoiceState情報を表現するクラス
    Discordから受信しLavalinkノードへ送信されるボイス状態情報

    Attributes
    ----------
    token: str | None
        Discordのボイストークン（Botトークンとは異なる）。Noneの場合もある
    endpoint: str | None
        接続中のDiscordボイスエンドポイント。Noneの場合もある
    session_id: str | None
        DiscordのボイスセッションID。Noneの場合もある
    """

    def __init__(self, data: VoiceStateResponse) -> None:
        self.token: str | None = data.get("token")
        self.endpoint: str | None = data.get("endpoint")
        self.session_id: str | None = data.get("sessionId")


class PlayerResponsePayload:
    """:meth:`~wavelink.Node.fetch_player_info` または :meth:`~wavelink.Node.fetch_players` で受け取るペイロード

    Attributes
    ----------
    guild_id: int
        このプレイヤーが接続しているギルドID（int型）
    track: :class:`wavelink.Playable` | None
        現在Lavalinkで再生中のトラック。再生中でない場合はNone
    volume: int
        プレイヤーの現在の音量
    paused: bool
        プレイヤーが一時停止中かどうか
    state: :class:`wavelink.PlayerStatePayload`
        プレイヤーの現在の状態。:class:`wavelink.PlayerStatePayload` を参照
    voice_state: :class:`wavelink.VoiceStatePayload`
        Discordから受信しLavalinkへ送信されたボイス状態。:class:`wavelink.VoiceStatePayload` を参照
    filters: :class:`wavelink.Filters`
        このプレイヤーに現在適用されている :class:`wavelink.Filters`
    """

    def __init__(self, data: PlayerResponse) -> None:
        self.guild_id: int = int(data["guildId"])
        self.track: Playable | None = None

        if track := data.get("track"):
            self.track = Playable(track)

        self.volume: int = data["volume"]
        self.paused: bool = data["paused"]
        self.state: PlayerStatePayload = PlayerStatePayload(data["state"])
        self.voice_state: VoiceStatePayload = VoiceStatePayload(data["voice"])
        self.filters: Filters = Filters(data=data["filters"])


class GitResponsePayload:
    """:meth:`wavelink.Node.fetch_info` で受け取るGit情報を表現するクラス

    Attributes
    ----------
    branch: str
        このLavalinkサーバーがビルドされたブランチ名
    commit: str
        このLavalinkサーバーがビルドされたコミット
    commit_time: :class:`datetime.datetime`
        このコミットが作成されたタイムスタンプ
    """

    def __init__(self, data: GitPayload) -> None:
        self.branch: str = data["branch"]
        self.commit: str = data["commit"]
        self.commit_time: datetime.datetime = datetime.datetime.fromtimestamp(
            data["commitTime"] / 1000, tz=datetime.timezone.utc
        )


class VersionResponsePayload:
    """:meth:`wavelink.Node.fetch_info` で受け取るバージョン情報を表現するクラス

    Attributes
    ----------
    semver: str
        このLavalinkサーバーの完全なバージョン文字列
    major: int
        このLavalinkサーバーのメジャーバージョン
    minor: int
        このLavalinkサーバーのマイナーバージョン
    patch: int
        このLavalinkサーバーのパッチバージョン
    pre_release: str
        semverに従ったプレリリースバージョン（ドット区切りの識別子リスト）
    build: str | None
        semverに従ったビルドメタデータ（ドット区切りの識別子リスト）。Noneの場合もある
    """

    def __init__(self, data: VersionPayload) -> None:
        self.semver: str = data["semver"]
        self.major: int = data["major"]
        self.minor: int = data["minor"]
        self.patch: int = data["patch"]
        self.pre_release: str | None = data.get("preRelease")
        self.build: str | None = data.get("build")


class PluginResponsePayload:
    """:meth:`wavelink.Node.fetch_info` で受け取るプラグイン情報を表現するクラス

    Attributes
    ----------
    name: str
        プラグイン名
    version: str
        プラグインのバージョン
    """

    def __init__(self, data: PluginPayload) -> None:
        self.name: str = data["name"]
        self.version: str = data["version"]


class InfoResponsePayload:
    """:meth:`~wavelink.Node.fetch_info` で受け取るペイロード

    Attributes
    ----------
    version: :class:`VersionResponsePayload`
        このLavalinkノードのバージョン情報（:class:`VersionResponsePayload` オブジェクト）
    build_time: :class:`datetime.datetime`
        このLavalink jarがビルドされたタイムスタンプ
    git: :class:`GitResponsePayload`
        このLavalinkノードのGit情報（:class:`GitResponsePayload` オブジェクト）
    jvm: str
        このLavalinkノードが動作しているJVMのバージョン
    lavaplayer: str
        このLavalinkノードで使用されているLavaplayerのバージョン
    source_managers: list[str]
        このノードで有効なソースマネージャー
    filters: list[str]
        このノードで有効なフィルター
    plugins: list[:class:`PluginResponsePayload`]
        このノードで有効なプラグイン
    """

    def __init__(self, data: InfoResponse) -> None:
        self.version: VersionResponsePayload = VersionResponsePayload(data["version"])
        self.build_time: datetime.datetime = datetime.datetime.fromtimestamp(
            data["buildTime"] / 1000, tz=datetime.timezone.utc
        )
        self.git: GitResponsePayload = GitResponsePayload(data["git"])
        self.jvm: str = data["jvm"]
        self.lavaplayer: str = data["lavaplayer"]
        self.source_managers: list[str] = data["sourceManagers"]
        self.filters: list[str] = data["filters"]
        self.plugins: list[PluginResponsePayload] = [PluginResponsePayload(p) for p in data["plugins"]]


class ExtraEventPayload:
    """:func:`on_wavelink_extra_event` イベントで受け取るペイロード

    このペイロードはLavalinkから ``Unknown`` または ``Unhandled`` なイベント（主にプラグイン経由）を受信した際に作成される

    .. note::
        これらのイベントで送信されるデータの詳細は、該当プラグインのドキュメントを参照

    Attributes
    ----------
    node: :class:`~wavelink.Node`
        このイベントに関連するノード
    player: :class:`~wavelink.Player` | None
        このイベントに関連するプレイヤー。Noneの場合もある
    data: dict[str, Any]
        このイベントでLavalinkから送信された生データ

    .. versionadded:: 3.1.0
    """

    def __init__(self, *, node: Node, player: Player | None, data: dict[str, Any]) -> None:
        self.node = node
        self.player = player
        self.data = data
