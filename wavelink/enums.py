import enum


__all__ = ("NodeStatus", "TrackSource", "DiscordVoiceCloseType", "AutoPlayMode", "QueueMode")


class NodeStatus(enum.Enum):
    """ノードの接続状態を表すEnum

    Attributes
    ----------
    DISCONNECTED
        ノードが切断されている、またはこれまで接続されたことがない状態
    CONNECTING
        ノードが現在接続を試みている状態
    CONNECTED
        ノードが現在接続されている状態
    """

    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2


class TrackSource(enum.Enum):
    """再生可能なソースを表すEnum

    Attributes
    ----------
    YouTube
        YouTubeからのトラックを表すソース
    YouTubeMusic
        YouTube Musicからのトラックを表すソース
    SoundCloud
        SoundCloudからのトラックを表すソース
    """

    YouTube = 0
    YouTubeMusic = 1
    SoundCloud = 2


class DiscordVoiceCloseType(enum.Enum):
    """いろいろなDiscord VoiceCloseTypeを表すEnum

    Attributes
    ----------
    CLOSE_NORMAL
        1000
    UNKNOWN_OPCODE
        4001
    FAILED_DECODE_PAYLOAD
        4002
    NOT_AUTHENTICATED
        4003
    AUTHENTICATION_FAILED
        4004
    ALREADY_AUTHENTICATED
        4005
    SESSION_INVALID
        4006
    SESSION_TIMEOUT
        4009
    SERVER_NOT_FOUND
        4011
    UNKNOWN_PROTOCOL
        4012
    DISCONNECTED
        4014
    VOICE_SERVER_CRASHED
        4015
    UNKNOWN_ENCRYPTION_MODE
        4016
    BAD_REQUEST
        4020
    RATE_LIMITED
        4021
    CALL_TERMINATED
        4022
    """

    CLOSE_NORMAL = 1000  # Not Discord but standard websocket
    UNKNOWN_OPCODE = 4001
    FAILED_DECODE_PAYLOAD = 4002
    NOT_AUTHENTICATED = 4003
    AUTHENTICATION_FAILED = 4004
    ALREADY_AUTHENTICATED = 4005
    SESSION_INVALID = 4006
    SESSION_TIMEOUT = 4009
    SERVER_NOT_FOUND = 4011
    UNKNOWN_PROTOCOL = 4012
    DISCONNECTED = 4014
    VOICE_SERVER_CRASHED = 4015
    UNKNOWN_ENCRYPTION_MODE = 4016
    BAD_REQUEST = 4020
    RATE_LIMITED = 4021
    CALL_TERMINATED = 4022


class AutoPlayMode(enum.Enum):
    """さまざまなAutoPlayモードを表すEnum

    Attributes
    ----------
    enabled
        有効の場合、AutoPlayは完全に自律的に動作し、auto_queueにおすすめトラックを追加します
        プレイヤーの標準キューに曲が追加された場合は、それを優先的に使用します
    partial
        部分的の場合、AutoPlayは完全に自律的に動作しますが、auto_queueにおすすめトラックを追加**しません**
    disabled
        無効の場合、AutoPlayは自動的な動作を一切行いません
    """

    enabled = 0
    partial = 1
    disabled = 2


class QueueMode(enum.Enum):
    """さまざまな :class:`wavelink.Queue` のモードを表すEnum

    Attributes
    ----------
    normal
        このモードでは、キューも履歴もループしません。デフォルトの設定です
    loop
        このモードでは、トラックが連続してループ再生されます
    loop_all
        このモードでは、キュー内のすべてのトラックが連続してループ再生されます
    """

    normal = 0
    loop = 1
    loop_all = 2
