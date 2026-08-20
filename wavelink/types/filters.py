from typing import Any, TypedDict


class Equalizer(TypedDict):
    band: int
    gain: float


class Karaoke(TypedDict, total=False):
    level: float | None
    monoLevel: float | None
    filterBand: float | None
    filterWidth: float | None


class Timescale(TypedDict, total=False):
    speed: float | None
    pitch: float | None
    rate: float | None


class Tremolo(TypedDict, total=False):
    frequency: float | None
    depth: float | None


class Vibrato(TypedDict, total=False):
    frequency: float | None
    depth: float | None


class Rotation(TypedDict, total=False):
    rotationHz: float | None


class Distortion(TypedDict, total=False):
    sinOffset: float | None
    sinScale: float | None
    cosOffset: float | None
    cosScale: float | None
    tanOffset: float | None
    tanScale: float | None
    offset: float | None
    scale: float | None


class ChannelMix(TypedDict, total=False):
    leftToLeft: float | None
    leftToRight: float | None
    rightToLeft: float | None
    rightToRight: float | None


class LowPass(TypedDict, total=False):
    smoothing: float | None


class Echo(TypedDict, total=False):
    delay: float | None
    feedback: float | None
    mix: float | None


class Chorus(TypedDict, total=False):
    rate: float | None
    depth: float | None
    feedback: float | None
    delay: float | None
    mix: float | None


class Compressor(TypedDict, total=False):
    threshold: float | None
    ratio: float | None
    attack: float | None
    release: float | None
    gain: float | None
    makeupGain: float | None


class HighPass(TypedDict, total=False):
    smoothing: float | None


class Phaser(TypedDict, total=False):
    rate: float | None
    depth: float | None
    feedback: float | None
    delay: float | None
    mix: float | None
    stages: int | None
    minFrequency: float | None
    maxFrequency: float | None


class Spatial(TypedDict, total=False):
    x: float | None
    y: float | None
    z: float | None
    depth: float | None
    rate: float | None


class FilterPayload(TypedDict, total=False):
    volume: float | None
    equalizer: list[Equalizer] | None
    karaoke: Karaoke
    timescale: Timescale
    tremolo: Tremolo
    vibrato: Vibrato
    rotation: Rotation
    distortion: Distortion
    channelMix: ChannelMix
    lowPass: LowPass
    echo: Echo
    chorus: Chorus
    compressor: Compressor
    highpass: HighPass
    phaser: Phaser
    spatial: Spatial
    pluginFilters: dict[str, Any]
