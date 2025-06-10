from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypedDict, TypeVar

from .types.filters import (
    ChannelMix as ChannelMixPayload,
    Distortion as DistortionPayload,
    Equalizer as EqualizerPayload,
    FilterPayload,
    Karaoke as KaraokePayload,
    LowPass as LowPassPayload,
    Rotation as RotationPayload,
    Timescale as TimescalePayload,
    Tremolo as TremoloPayload,
    Vibrato as VibratoPayload,
)


if TYPE_CHECKING:
    from typing_extensions import Self, Unpack


FT = TypeVar("FT")


__all__ = (
    "FiltersOptions",
    "Filters",
    "Equalizer",
    "Karaoke",
    "Timescale",
    "Tremolo",
    "Vibrato",
    "Rotation",
    "Distortion",
    "ChannelMix",
    "LowPass",
    "PluginFilters",
)


class FiltersOptions(TypedDict, total=False):
    volume: float
    equalizer: Equalizer
    karaoke: Karaoke
    timescale: Timescale
    tremolo: Tremolo
    vibrato: Vibrato
    rotation: Rotation
    distortion: Distortion
    channel_mix: ChannelMix
    low_pass: LowPass
    plugin_filters: PluginFilters
    reset: bool


class EqualizerOptions(TypedDict):
    bands: list[EqualizerPayload] | None


class KaraokeOptions(TypedDict):
    level: float | None
    mono_level: float | None
    filter_band: float | None
    filter_width: float | None


class RotationOptions(TypedDict):
    rotation_hz: float | None


class DistortionOptions(TypedDict):
    sin_offset: float | None
    sin_scale: float | None
    cos_offset: float | None
    cos_scale: float | None
    tan_offset: float | None
    tan_scale: float | None
    offset: float | None
    scale: float | None


class ChannelMixOptions(TypedDict):
    left_to_left: float | None
    left_to_right: float | None
    right_to_left: float | None
    right_to_right: float | None


class _BaseFilter(Generic[FT]):
    _payload: FT

    def __init__(self, payload: FT) -> None:
        self._payload = payload
        self._remove_none()

    def _remove_none(self) -> None:
        # Lavalink doesn't allow nullable types in any filters, but they are still not required...
        # Passing None makes it easier for the user to remove a field...
        self._payload = {k: v for k, v in self._payload.items() if v is not None}  # type: ignore


class Equalizer:
    """イコライザーフィルタークラス

    0から14までの15バンドを調整できる
    各バンドには "gain"（増幅率）があり、デフォルトは0

    有効な "gain" の値は-0.25から1.0まで
    -0.25はそのバンドが完全にミュート、0.25は2倍になるイメージ

    "gain" を調整すると出力音量も変わることがある
    """

    def __init__(self, payload: list[EqualizerPayload] | None = None) -> None:
        if payload and len(payload) == 15:
            self._payload = self._set(payload)

        else:
            payload_: dict[int, EqualizerPayload] = {n: {"band": n, "gain": 0.0} for n in range(15)}
            self._payload = payload_

    def _set(self, payload: list[EqualizerPayload]) -> dict[int, EqualizerPayload]:
        default: dict[int, EqualizerPayload] = {n: {"band": n, "gain": 0.0} for n in range(15)}

        for eq in payload:
            band: int = eq["band"]
            if band > 14 or band < 0:
                continue

            default[band] = eq

        return default

    def set(self, **options: Unpack[EqualizerOptions]) -> Self:
        """イコライザーのバンドをまとめて設定する

        キーワード引数 "bands" で、"band" と "gain" を持つ辞書のリストを渡す

        "band" は0から14のint、"gain" は-0.25から1.0のfloat
        -0.25でそのバンドがミュート、0.25で2倍になる

        このメソッドを使うと全バンドがリセットされ、指定しなかったバンドも初期化される
        特定のバンドだけ変えたい場合は :attr:`~wavelink.Equalizer.payload` を直接編集するのがおすすめ
        """
        default: dict[int, EqualizerPayload] = {n: {"band": n, "gain": 0.0} for n in range(15)}
        payload: list[EqualizerPayload] | None = options.get("bands", None)

        if payload is None:
            self._payload = default
            return self

        self._payload = self._set(payload)
        return self

    def reset(self) -> Self:
        """このフィルターを初期状態にリセットする
        """
        self._payload: dict[int, EqualizerPayload] = {n: {"band": n, "gain": 0.0} for n in range(15)}
        return self

    @property
    def payload(self) -> dict[int, EqualizerPayload]:
        """このフィルターの生のペイロードを返す

        戻り値はコピー
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "Equalizer"

    def __repr__(self) -> str:
        return f"<Equalizer: {self._payload}>"


class Karaoke(_BaseFilter[KaraokePayload]):
    """カラオケフィルタークラス

    イコライザーで特定のバンド（主にボーカル）を除去する効果
    """

    def __init__(self, payload: KaraokePayload) -> None:
        super().__init__(payload=payload)

    def set(self, **options: Unpack[KaraokeOptions]) -> Self:
        """このフィルターのプロパティを設定する

        キーワード引数で設定可能
        指定しなかった値は上書きされない

        Parameters
        ----------
        level: Optional[float]
            効果の強さ。0.0で無効、1.0で最大
        mono_level: Optional[float]
            モノラル成分の強さ。0.0で無効、1.0で最大
        filter_band: Optional[float]
            除去するバンドの周波数（Hz）
        filter_width: Optional[float]
            バンド幅
        """
        self._payload: KaraokePayload = {
            "level": options.get("level", self._payload.get("level")),
            "monoLevel": options.get("mono_level", self._payload.get("monoLevel")),
            "filterBand": options.get("filter_band", self._payload.get("filterBand")),
            "filterWidth": options.get("filter_width", self._payload.get("filterWidth")),
        }
        self._remove_none()
        return self

    def reset(self) -> Self:
        """このフィルターを初期状態にリセットする
        """
        self._payload: KaraokePayload = {}
        return self

    @property
    def payload(self) -> KaraokePayload:
        """このフィルターの生のペイロードを返す

        戻り値はコピー
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "Karaoke"

    def __repr__(self) -> str:
        return f"<Karaoke: {self._payload}>"


class Timescale(_BaseFilter[TimescalePayload]):
    """タイムスケールフィルタークラス

    再生速度・ピッチ・レートを変更できる
    """

    def __init__(self, payload: TimescalePayload) -> None:
        super().__init__(payload=payload)

    def set(self, **options: Unpack[TimescalePayload]) -> Self:
        """このフィルターのプロパティを設定する

        キーワード引数で設定可能
        指定しなかった値は上書きされない

        Parameters
        ----------
        speed: Optional[float]
            再生速度
        pitch: Optional[float]
            ピッチ
        rate: Optional[float]
            レート
        """
        self._payload.update(options)
        self._remove_none()
        return self

    def reset(self) -> Self:
        """このフィルターを初期状態にリセットする
        """
        self._payload: TimescalePayload = {}
        return self

    @property
    def payload(self) -> TimescalePayload:
        """このフィルターの生のペイロードを返す

        戻り値はコピー
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "Timescale"

    def __repr__(self) -> str:
        return f"<Timescale: {self._payload}>"


class Tremolo(_BaseFilter[TremoloPayload]):
    """トレモロフィルタークラス

    音量を周期的に揺らして震えるような効果を出す
    例: https://en.wikipedia.org/wiki/File:Fuse_Electronics_Tremolo_MK-III_Quick_Demo.ogv
    """

    def __init__(self, payload: TremoloPayload) -> None:
        super().__init__(payload=payload)

    def set(self, **options: Unpack[TremoloPayload]) -> Self:
        """このフィルターのプロパティを設定する

        キーワード引数で設定可能
        指定しなかった値は上書きされない

        Parameters
        ----------
        frequency: Optional[float]
            周波数
        depth: Optional[float]
            揺れの深さ
        """
        self._payload.update(options)
        self._remove_none()
        return self

    def reset(self) -> Self:
        """このフィルターを初期状態にリセットする
        """
        self._payload: TremoloPayload = {}
        return self

    @property
    def payload(self) -> TremoloPayload:
        """このフィルターの生のペイロードを返す

        戻り値はコピー
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "Tremolo"

    def __repr__(self) -> str:
        return f"<Tremolo: {self._payload}>"


class Vibrato(_BaseFilter[VibratoPayload]):
    """ビブラートフィルタークラス

    トレモロが音量を揺らすのに対し、ビブラートはピッチを揺らす
    """

    def __init__(self, payload: VibratoPayload) -> None:
        super().__init__(payload=payload)

    def set(self, **options: Unpack[VibratoPayload]) -> Self:
        """このフィルターのプロパティを設定する

        キーワード引数で設定可能
        指定しなかった値は上書きされない

        Parameters
        ----------
        frequency: Optional[float]
            周波数
        depth: Optional[float]
            揺れの深さ
        """
        self._payload.update(options)
        self._remove_none()
        return self

    def reset(self) -> Self:
        """このフィルターを初期状態にリセットする
        """
        self._payload: VibratoPayload = {}
        return self

    @property
    def payload(self) -> VibratoPayload:
        """このフィルターの生のペイロードを返す

        戻り値はコピー
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "Vibrato"

    def __repr__(self) -> str:
        return f"<Vibrato: {self._payload}>"


class Rotation(_BaseFilter[RotationPayload]):
    """ローテーションフィルタークラス

    ステレオ左右やヘッドホンで音が回転するような効果（パンニング）
    例: https://youtu.be/QB9EB8mTKcc（リバーブなし）
    """

    def __init__(self, payload: RotationPayload) -> None:
        super().__init__(payload=payload)

    def set(self, **options: Unpack[RotationOptions]) -> Self:
        """このフィルターのプロパティを設定する

        キーワード引数で設定可能
        指定しなかった値は上書きされない

        Parameters
        ----------
        rotation_hz: Optional[float]
            音が回転する周波数（Hz）。0.2で上記動画のような効果
        """
        self._payload: RotationPayload = {"rotationHz": options.get("rotation_hz", self._payload.get("rotationHz"))}
        self._remove_none()
        return self

    def reset(self) -> Self:
        """このフィルターを初期状態にリセットする
        """
        self._payload: RotationPayload = {}
        return self

    @property
    def payload(self) -> RotationPayload:
        """このフィルターの生のペイロードを返す

        戻り値はコピー
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "Rotation"

    def __repr__(self) -> str:
        return f"<Rotation: {self._payload}>"


class Distortion(_BaseFilter[DistortionPayload]):
    """ディストーションフィルタークラス

    Lavalink曰く「かなりユニークな音響効果を生み出せる」
    """

    def __init__(self, payload: DistortionPayload) -> None:
        super().__init__(payload=payload)

    def set(self, **options: Unpack[DistortionOptions]) -> Self:
        """このフィルターのプロパティを設定する

        キーワード引数で設定可能
        指定しなかった値は上書きされない

        Parameters
        ----------
        sin_offset: Optional[float]
            サインオフセット
        sin_scale: Optional[float]
            サインスケール
        cos_offset: Optional[float]
            コサインオフセット
        cos_scale: Optional[float]
            コサインスケール
        tan_offset: Optional[float]
            タンジェントオフセット
        tan_scale: Optional[float]
            タンジェントスケール
        offset: Optional[float]
            オフセット
        scale: Optional[float]
            スケール
        """
        self._payload: DistortionPayload = {
            "sinOffset": options.get("sin_offset", self._payload.get("sinOffset")),
            "sinScale": options.get("sin_scale", self._payload.get("sinScale")),
            "cosOffset": options.get("cos_offset", self._payload.get("cosOffset")),
            "cosScale": options.get("cos_scale", self._payload.get("cosScale")),
            "tanOffset": options.get("tan_offset", self._payload.get("tanOffset")),
            "tanScale": options.get("tan_scale", self._payload.get("tanScale")),
            "offset": options.get("offset", self._payload.get("offset")),
            "scale": options.get("scale", self._payload.get("scale")),
        }
        self._remove_none()
        return self

    def reset(self) -> Self:
        """このフィルターを初期状態にリセットする
        """
        self._payload: DistortionPayload = {}
        return self

    @property
    def payload(self) -> DistortionPayload:
        """このフィルターの生のペイロードを返す

        戻り値はコピー
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "Distortion"

    def __repr__(self) -> str:
        return f"<Distortion: {self._payload}>"


class ChannelMix(_BaseFilter[ChannelMixPayload]):
    """チャンネルミックスフィルタークラス

    左右チャンネルを混ぜる。各チャンネルがどれだけ影響し合うかを調整できる
    デフォルトでは左右独立

    全て0.5にすると両チャンネルが同じ音になる
    """

    def __init__(self, payload: ChannelMixPayload) -> None:
        super().__init__(payload=payload)

    def set(self, **options: Unpack[ChannelMixOptions]) -> Self:
        """このフィルターのプロパティを設定する

        キーワード引数で設定可能
        指定しなかった値は上書きされない

        Parameters
        ----------
        left_to_left: Optional[float]
            左→左のミックス係数（0.0～1.0）
        left_to_right: Optional[float]
            左→右のミックス係数（0.0～1.0）
        right_to_left: Optional[float]
            右→左のミックス係数（0.0～1.0）
        right_to_right: Optional[float]
            右→右のミックス係数（0.0～1.0）
        """
        self._payload: ChannelMixPayload = {
            "leftToLeft": options.get("left_to_left", self._payload.get("leftToLeft")),
            "leftToRight": options.get("left_to_right", self._payload.get("leftToRight")),
            "rightToLeft": options.get("right_to_left", self._payload.get("rightToLeft")),
            "rightToRight": options.get("right_to_right", self._payload.get("rightToRight")),
        }
        self._remove_none()
        return self

    def reset(self) -> Self:
        """このフィルターを初期状態にリセットする
        """
        self._payload: ChannelMixPayload = {}
        return self

    @property
    def payload(self) -> ChannelMixPayload:
        """このフィルターの生のペイロードを返す

        戻り値はコピー
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "ChannelMix"

    def __repr__(self) -> str:
        return f"<ChannelMix: {self._payload}>"


class LowPass(_BaseFilter[LowPassPayload]):
    """ローパスフィルタークラス

    高い周波数を抑え、低い周波数だけ通す（ローパス）
    smoothingが1.0以下だとフィルターは無効
    """

    def __init__(self, payload: LowPassPayload) -> None:
        super().__init__(payload=payload)

    def set(self, **options: Unpack[LowPassPayload]) -> Self:
        """このフィルターのプロパティを設定する

        キーワード引数で設定可能
        指定しなかった値は上書きされない

        Parameters
        ----------
        smoothing: Optional[float]
            スムージング係数
        """
        self._payload.update(options)
        self._remove_none()
        return self

    def reset(self) -> Self:
        """このフィルターを初期状態にリセットする
        """
        self._payload: LowPassPayload = {}
        return self

    @property
    def payload(self) -> LowPassPayload:
        """このフィルターの生のペイロードを返す

        戻り値はコピー
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "LowPass"

    def __repr__(self) -> str:
        return f"<LowPass: {self._payload}>"


class PluginFilters(_BaseFilter[dict[str, Any]]):
    """プラグインフィルタークラス

    プラグインでフィルター値を設定する場合に使う
    詳細はLavalinkプラグインのドキュメント参照

    通常は ``dict[str, Any]`` 形式で渡す:

    .. code:: python3

        {"pluginName": {"filterKey": "filterValue"}, ...}

    .. warning::

        このクラスで値を設定する際は ``"pluginFilters"`` というトップレベルキーは含めないこと
    """

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(payload=payload)

    def set(self, **options: dict[str, Any]) -> Self:
        """このフィルターのプロパティを設定する

        キーワード引数または辞書のアンパックで設定可能
        詳細はLavalinkプラグインのドキュメント参照

        Examples
        --------

        .. code:: python3

            plugin_filters: PluginFilters = PluginFilters()
            plugin_filters.set(pluginName={"filterKey": "filterValue", ...})

            # または...

            plugin_filters.set(**{"pluginName": {"filterKey": "filterValue", ...}})
        """
        self._payload.update(options)
        self._remove_none()
        return self

    def reset(self) -> Self:
        """このフィルターを初期状態にリセットする
        """
        self._payload: dict[str, Any] = {}
        return self

    @property
    def payload(self) -> dict[str, Any]:
        """このフィルターの生のペイロードを返す

        戻り値はコピー
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "PluginFilters"

    def __repr__(self) -> str:
        return f"<PluginFilters: {self._payload}"


class Filters:
    """wavelinkのフィルター管理クラス

    各LavalinkフィルターをPythonクラスとしてまとめて管理できる
    各フィルターは個別に ``set`` や ``reset`` 可能

    個別の ``set`` は指定した値だけ更新、``reset`` はそのフィルターを初期化
    :meth:`~wavelink.Filters.reset` で全フィルターを一括リセットできる

    新しい :class:`~wavelink.Player` には自動で適用される

    :meth:`~wavelink.Player.set_filters` でプレイヤーに適用、:attr:`~wavelink.Player.filters` で取得

    このFiltersクラスの ``payload`` を取得したい場合はインスタンスを呼び出す

    Examples
    --------

    .. code:: python3

        import wavelink

        # 新しいFiltersを作って適用
        # player.set_filters() を使うと簡単にリセットできる
        filters: wavelink.Filters = wavelink.Filters()
        await player.set_filters(filters)

        # Filtersインスタンスのpayloadを取得
        filters: wavelink.Filters = player.filters
        print(filters())

        # フィルターを個別に設定・リセット
        filters: wavelink.Filters = player.filters
        filters.timescale.set(pitch=1.2, speed=1.1, rate=1)
        filters.rotation.set(rotation_hz=0.2)
        filters.equalizer.reset()

        await player.set_filters(filters)

        # フィルターをリセット
        filters: wavelink.Filters = player.filters
        filters.timescale.reset()

        await player.set_filters(filters)

        # 全フィルターをリセット
        filters: wavelink.Filters = player.filters
        filters.reset()

        await player.set_filters(filters)

        # 一括リセット・適用の簡易メソッド
        await player.set_filters()
    """

    def __init__(self, *, data: FilterPayload | None = None) -> None:
        self._volume: float | None = None
        self._equalizer: Equalizer = Equalizer(None)
        self._karaoke: Karaoke = Karaoke({})
        self._timescale: Timescale = Timescale({})
        self._tremolo: Tremolo = Tremolo({})
        self._vibrato: Vibrato = Vibrato({})
        self._rotation: Rotation = Rotation({})
        self._distortion: Distortion = Distortion({})
        self._channel_mix: ChannelMix = ChannelMix({})
        self._low_pass: LowPass = LowPass({})
        self._plugin_filters: PluginFilters = PluginFilters({})

        if data:
            self._create_from(data)

    def _create_from(self, data: FilterPayload) -> None:
        self._volume = data.get("volume")
        self._equalizer = Equalizer(data.get("equalizer", None))
        self._karaoke = Karaoke(data.get("karaoke", {}))
        self._timescale = Timescale(data.get("timescale", {}))
        self._tremolo = Tremolo(data.get("tremolo", {}))
        self._vibrato = Vibrato(data.get("vibrato", {}))
        self._rotation = Rotation(data.get("rotation", {}))
        self._distortion = Distortion(data.get("distortion", {}))
        self._channel_mix = ChannelMix(data.get("channelMix", {}))
        self._low_pass = LowPass(data.get("lowPass", {}))
        self._plugin_filters = PluginFilters(data.get("pluginFilters", {}))

    def _set_with_reset(self, filters: FiltersOptions) -> None:
        self._volume = filters.get("volume")
        self._equalizer = filters.get("equalizer", Equalizer(None))
        self._karaoke = filters.get("karaoke", Karaoke({}))
        self._timescale = filters.get("timescale", Timescale({}))
        self._tremolo = filters.get("tremolo", Tremolo({}))
        self._vibrato = filters.get("vibrato", Vibrato({}))
        self._rotation = filters.get("rotation", Rotation({}))
        self._distortion = filters.get("distortion", Distortion({}))
        self._channel_mix = filters.get("channel_mix", ChannelMix({}))
        self._low_pass = filters.get("low_pass", LowPass({}))
        self._plugin_filters = filters.get("plugin_filters", PluginFilters({}))

    def set_filters(self, **filters: Unpack[FiltersOptions]) -> None:
        """Set multiple filters at once to a standalone Filter object.
        To set the filters to the player directly see :meth:`wavelink.Player.set_filters`

        Parameters
        ----------
        volume: float
            The Volume filter to apply to the player.
        equalizer: :class:`wavelink.Equalizer`
            The Equalizer filter to apply to the player.
        karaoke: :class:`wavelink.Karaoke`
            The Karaoke filter to apply to the player.
        timescale: :class:`wavelink.Timescale`
            The Timescale filter to apply to the player.
        tremolo: :class:`wavelink.Tremolo`
            The Tremolo filter to apply to the player.
        vibrato: :class:`wavelink.Vibrato`
            The Vibrato filter to apply to the player.
        rotation: :class:`wavelink.Rotation`
            The Rotation filter to apply to the player.
        distortion: :class:`wavelink.Distortion`
            The Distortion filter to apply to the player.
        channel_mix: :class:`wavelink.ChannelMix`
            The ChannelMix filter to apply to the player.
        low_pass: :class:`wavelink.LowPass`
            The LowPass filter to apply to the player.
        plugin_filters: :class:`wavelink.PluginFilters`
            The extra Plugin Filters to apply to the player. See :class:`~wavelink.PluginFilters` for more details.
        reset: bool
            Whether to reset all filters that were not specified.
        """

        reset: bool = filters.get("reset", False)
        if reset:
            self._set_with_reset(filters)
            return

        self._volume = filters.get("volume", self._volume)
        self._equalizer = filters.get("equalizer", self._equalizer)
        self._karaoke = filters.get("karaoke", self._karaoke)
        self._timescale = filters.get("timescale", self._timescale)
        self._tremolo = filters.get("tremolo", self._tremolo)
        self._vibrato = filters.get("vibrato", self._vibrato)
        self._rotation = filters.get("rotation", self._rotation)
        self._distortion = filters.get("distortion", self._distortion)
        self._channel_mix = filters.get("channel_mix", self._channel_mix)
        self._low_pass = filters.get("low_pass", self._low_pass)
        self._plugin_filters = filters.get("plugin_filters", self._plugin_filters)

    def _reset(self) -> None:
        self._volume = None
        self._equalizer = Equalizer(None)
        self._karaoke = Karaoke({})
        self._timescale = Timescale({})
        self._tremolo = Tremolo({})
        self._vibrato = Vibrato({})
        self._rotation = Rotation({})
        self._distortion = Distortion({})
        self._channel_mix = ChannelMix({})
        self._low_pass = LowPass({})
        self._plugin_filters = PluginFilters({})

    def reset(self) -> None:
        """Method which resets this object to an original state.

        This method will clear all individual filters, and assign the wavelink default classes.
        """
        self._reset()

    @classmethod
    def from_filters(cls, **filters: Unpack[FiltersOptions]) -> Self:
        """Creates a Filters object with specified filters.

        Parameters
        ----------
        volume: float
            The Volume filter to apply to the player.
        equalizer: :class:`wavelink.Equalizer`
            The Equalizer filter to apply to the player.
        karaoke: :class:`wavelink.Karaoke`
            The Karaoke filter to apply to the player.
        timescale: :class:`wavelink.Timescale`
            The Timescale filter to apply to the player.
        tremolo: :class:`wavelink.Tremolo`
            The Tremolo filter to apply to the player.
        vibrato: :class:`wavelink.Vibrato`
            The Vibrato filter to apply to the player.
        rotation: :class:`wavelink.Rotation`
            The Rotation filter to apply to the player.
        distortion: :class:`wavelink.Distortion`
            The Distortion filter to apply to the player.
        channel_mix: :class:`wavelink.ChannelMix`
            The ChannelMix filter to apply to the player.
        low_pass: :class:`wavelink.LowPass`
            The LowPass filter to apply to the player.
        plugin_filters: :class:`wavelink.PluginFilters`
            The extra Plugin Filters to apply to the player. See :class:`~wavelink.PluginFilters` for more details.
        reset: bool
            Whether to reset all filters that were not specified.
        """

        self = cls()
        self._set_with_reset(filters)

        return self

    @property
    def volume(self) -> float | None:
        """Property which returns the volume ``float`` associated with this Filters payload.

        Adjusts the player volume from 0.0 to 5.0, where 1.0 is 100%. Values >1.0 may cause clipping.
        """
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = value

    @property
    def equalizer(self) -> Equalizer:
        """Property which returns the :class:`~wavelink.Equalizer` filter associated with this Filters payload."""
        return self._equalizer

    @property
    def karaoke(self) -> Karaoke:
        """Property which returns the :class:`~wavelink.Karaoke` filter associated with this Filters payload."""
        return self._karaoke

    @property
    def timescale(self) -> Timescale:
        """Property which returns the :class:`~wavelink.Timescale` filter associated with this Filters payload."""
        return self._timescale

    @property
    def tremolo(self) -> Tremolo:
        """Property which returns the :class:`~wavelink.Tremolo` filter associated with this Filters payload."""
        return self._tremolo

    @property
    def vibrato(self) -> Vibrato:
        """Property which returns the :class:`~wavelink.Vibrato` filter associated with this Filters payload."""
        return self._vibrato

    @property
    def rotation(self) -> Rotation:
        """Property which returns the :class:`~wavelink.Rotation` filter associated with this Filters payload."""
        return self._rotation

    @property
    def distortion(self) -> Distortion:
        """Property which returns the :class:`~wavelink.Distortion` filter associated with this Filters payload."""
        return self._distortion

    @property
    def channel_mix(self) -> ChannelMix:
        """Property which returns the :class:`~wavelink.ChannelMix` filter associated with this Filters payload."""
        return self._channel_mix

    @property
    def low_pass(self) -> LowPass:
        """Property which returns the :class:`~wavelink.LowPass` filter associated with this Filters payload."""
        return self._low_pass

    @property
    def plugin_filters(self) -> PluginFilters:
        """Property which returns the :class:`~wavelink.PluginFilters` filters associated with this Filters payload."""
        return self._plugin_filters

    def __call__(self) -> FilterPayload:
        payload: FilterPayload = {
            "volume": self._volume,
            "equalizer": list(self._equalizer._payload.values()),
            "karaoke": self._karaoke._payload,
            "timescale": self._timescale._payload,
            "tremolo": self._tremolo._payload,
            "vibrato": self._vibrato._payload,
            "rotation": self._rotation._payload,
            "distortion": self._distortion._payload,
            "channelMix": self._channel_mix._payload,
            "lowPass": self._low_pass._payload,
            "pluginFilters": self._plugin_filters._payload,
        }

        for key, value in payload.copy().items():
            if not value:
                del payload[key]

        return payload

    def __repr__(self) -> str:
        return (
            f"<Filters: volume={self._volume}, equalizer={self._equalizer!r}, karaoke={self._karaoke!r},"
            f" timescale={self._timescale!r}, tremolo={self._tremolo!r}, vibrato={self._vibrato!r},"
            f" rotation={self._rotation!r}, distortion={self._distortion!r}, channel_mix={self._channel_mix!r},"
            f" low_pass={self._low_pass!r}, plugin_filters={self._plugin_filters!r}>"
        )
