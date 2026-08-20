from typing import TypedDict

from typing_extensions import NotRequired


class MemoryStats(TypedDict):
    free: int
    used: int
    allocated: int
    reservable: int


class CPUStats(TypedDict):
    cores: int
    systemLoad: float
    lavalinkLoad: NotRequired[float]
    nodelinkLoad: NotRequired[float]


class FrameStats(TypedDict):
    sent: int
    nulled: int
    deficit: int
