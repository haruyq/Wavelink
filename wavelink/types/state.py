from typing import TypedDict

from typing_extensions import NotRequired

from ..filters import Filters
from ..tracks import Playable


class PlayerState(TypedDict):
    time: int
    position: int
    connected: bool
    ping: int


class VoiceState(TypedDict, total=False):
    token: str
    endpoint: str | None
    session_id: str


class PlayerVoiceState(TypedDict):
    voice: VoiceState
    channel_id: NotRequired[str]
    track: NotRequired[str]
    position: NotRequired[int]


class PlayerBasicState(TypedDict):
    """A dictionary of basic state for the Player.

    Attributes
    ----------
    voice_state: :class:`PlayerVoiceState`
        The voice state received via Discord. Includes the voice connection ``token``, ``endpoint`` and ``session_id``.
    position: int
        The player position.
    connected: bool
        Whether the player is currently connected to a channel.
    current: :class:`~wavelink.Playable` | None
        The currently playing track or `None` if no track is playing.
    paused: bool
        The players paused state.
    volume: int
        The players current volume.
    filters: :class:`~wavelink.Filters`
        The filters currently assigned to the Player.
    """

    voice_state: PlayerVoiceState
    position: int
    connected: bool
    current: Playable | None
    paused: bool
    volume: int
    filters: Filters
