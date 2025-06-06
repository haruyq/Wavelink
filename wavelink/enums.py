import enum


__all__ = ("NodeStatus", "TrackSource", "DiscordVoiceCloseType", "AutoPlayMode", "QueueMode")


class NodeStatus(enum.Enum):
    """Enum representing the connection status of a Node.

    Attributes
    ----------
    DISCONNECTED
        The Node has been disconnected or has never been connected previously.
    CONNECTING
        The Node is currently attempting to connect.
    CONNECTED
        The Node is currently connected.
    """

    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2


class TrackSource(enum.Enum):
    """Enum representing a :class:`Playable` source.

    Attributes
    ----------
    YouTube
        A source representing a track that comes from YouTube.
    YouTubeMusic
        A source representing a track that comes from YouTube Music.
    SoundCloud
        A source representing a track that comes from SoundCloud.
    """

    YouTube = 0
    YouTubeMusic = 1
    SoundCloud = 2


class DiscordVoiceCloseType(enum.Enum):
    """Enum representing the various Discord Voice Websocket Close Codes.

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
    """Enum representing the various AutoPlay modes.

    Attributes
    ----------
    enabled
        When enabled, AutoPlay will work fully autonomously and fill the auto_queue with recommended tracks.
        If a song is put into a players standard queue, AutoPlay will use it as a priority.
    partial
        When partial, AutoPlay will work fully autonomously but **will not** fill the auto_queue with
        recommended tracks.
    disabled
        When disabled, AutoPlay will not do anything automatically.
    """

    enabled = 0
    partial = 1
    disabled = 2


class QueueMode(enum.Enum):
    """Enum representing the various modes on :class:`wavelink.Queue`

    Attributes
    ----------
    normal
        When set, the queue will not loop either track or history. This is the default.
    loop
        When set, the track will continuously loop.
    loop_all
        When set, the queue will continuously loop through all tracks.
    """

    normal = 0
    loop = 1
    loop_all = 2
