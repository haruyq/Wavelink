from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias, overload

import yarl

import wavelink

from .enums import TrackSource
from .utils import ExtrasNamespace


if TYPE_CHECKING:
    from collections.abc import Iterator

    from .node import Node
    from .types.tracks import (
        PlaylistInfoPayload,
        PlaylistPayload,
        TrackInfoPayload,
        TrackPayload,
    )


__all__ = ("Search", "Album", "Artist", "Playable", "Playlist", "PlaylistInfo")


_source_mapping: dict[TrackSource | str | None, str] = {
    TrackSource.YouTube: "ytsearch",
    TrackSource.SoundCloud: "scsearch",
    TrackSource.YouTubeMusic: "ytmsearch",
}


Search: TypeAlias = "list[Playable] | Playlist"


class Album:
    """Lavalinkから受信したアルバムデータを表現するコンテナクラス

    Attributes
    ----------
    name: str | None
        アルバム名。Noneの場合もある
    url: str | None
        アルバムのURL。Noneの場合もある
    """

    def __init__(self, *, data: dict[Any, Any]) -> None:
        self.name: str | None = data.get("albumName")
        self.url: str | None = data.get("albumUrl")


class Artist:
    """Lavalinkから受信したアーティストデータを表現するコンテナクラス

    Attributes
    ----------
    url: str | None
        アーティストのURL。Noneの場合もある
    artwork: str | None
        アーティストのアートワークURL。Noneの場合もある
    """

    def __init__(self, *, data: dict[Any, Any]) -> None:
        self.url: str | None = data.get("artistUrl")
        self.artwork: str | None = data.get("artistArtworkUrl")


class Playable:
    """Wavelink 3における全トラックを表現するWavelinkのPlayableオブジェクト

    .. note::
        このクラスを手動でインスタンス化しないこと

    .. container:: operations

        .. describe:: str(track)
            このPlayableのタイトル

        .. describe:: repr(track)
            このPlayableの公式な文字列表現

        .. describe:: track == other
            このトラックが他と等しいかどうか（エンコード値とidentifierで判定）
    """

    def __init__(self, data: TrackPayload, *, playlist: PlaylistInfo | None = None) -> None:
        info: TrackInfoPayload = data["info"]

        self._encoded: str = data["encoded"]
        self._identifier: str = info["identifier"]
        self._is_seekable: bool = info["isSeekable"]
        self._author: str = info["author"]
        self._length: int = info["length"]
        self._is_stream: bool = info["isStream"]
        self._position: int = info["position"]
        self._title: str = info["title"]
        self._uri: str | None = info.get("uri")
        self._artwork: str | None = info.get("artworkUrl")
        self._isrc: str | None = info.get("isrc")
        self._source: str = info["sourceName"]

        plugin: dict[Any, Any] = data["pluginInfo"]
        self._album: Album = Album(data=plugin)
        self._artist: Artist = Artist(data=plugin)

        self._preview_url: str | None = plugin.get("previewUrl")
        self._is_preview: bool | None = plugin.get("isPreview")

        self._playlist = playlist
        self._recommended: bool = False

        self._extras: ExtrasNamespace = ExtrasNamespace(data.get("userData", {}))

        self._raw_data = data

    def __hash__(self) -> int:
        return hash(self.encoded)

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f"Playable(source={self.source}, title={self.title}, identifier={self.identifier})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Playable):
            return NotImplemented

        return self.encoded == other.encoded or self.identifier == other.identifier

    @property
    def encoded(self) -> str:
        """Lavalinkから受信したエンコード済みトラック文字列を返すプロパティ"""
        return self._encoded

    @property
    def identifier(self) -> str:
        """このトラックのソース上の識別子を返すプロパティ

        例: YouTube IDやSpotify ID
        """
        return self._identifier

    @property
    def is_seekable(self) -> bool:
        """このトラックがシーク可能かどうかを返すプロパティ"""
        return self._is_seekable

    @property
    def author(self) -> str:
        """このトラックの作者名を返すプロパティ"""
        return self._author

    @property
    def length(self) -> int:
        """このトラックの長さ（ミリ秒）をintで返すプロパティ"""
        return self._length

    @property
    def is_stream(self) -> bool:
        """このトラックがストリームかどうかを返すプロパティ"""
        return self._is_stream

    @property
    def position(self) -> int:
        """このトラックの開始位置（ミリ秒）をintで返すプロパティ"""
        return self._position

    @property
    def title(self) -> str:
        """このトラックのタイトル/名前を返すプロパティ"""
        return self._title

    @property
    def uri(self) -> str | None:
        """このトラックのURLを返すプロパティ。Noneの場合もある"""
        return self._uri

    @property
    def artwork(self) -> str | None:
        """このトラックのアートワークURLを返すプロパティ。Noneの場合もある"""
        return self._artwork

    @property
    def isrc(self) -> str | None:
        """このトラックのISRC（国際標準レコーディングコード）を返すプロパティ。Noneの場合もある"""
        return self._isrc

    @property
    def source(self) -> str:
        """このトラックのソース名（例: "spotify" や "youtube"）をstrで返すプロパティ"""
        return self._source

    @property
    def album(self) -> Album:
        """このトラックのアルバムデータを返すプロパティ"""
        return self._album

    @property
    def artist(self) -> Artist:
        """このトラックのアーティストデータを返すプロパティ"""
        return self._artist

    @property
    def preview_url(self) -> str | None:
        """このトラックのプレビューURLを返すプロパティ。Noneの場合もある"""
        return self._preview_url

    @property
    def is_preview(self) -> bool | None:
        """このトラックがプレビューかどうかを返すプロパティ。判別不能な場合はNone"""
        return self._is_preview

    @property
    def playlist(self) -> PlaylistInfo | None:
        """このトラックが属する :class:`wavelink.PlaylistInfo` を返すプロパティ。プレイリスト未所属ならNone
        """
        return self._playlist

    @property
    def recommended(self) -> bool:
        """このトラックがAutoPlayで推奨されたものかどうかを返すプロパティ"""
        return self._recommended

    @property
    def extras(self) -> ExtrasNamespace:
        """:class:`~wavelink.ExtrasNamespace` 型の追加情報を返すプロパティ

        このプロパティには有効な ``str`` キーと任意のJSON値を持つdict、または :class:`~wavelink.ExtrasNamespace` を設定可能
        dictを渡すと自動的に :class:`~wavelink.ExtrasNamespace` に変換される
        extrasはLavalinkの ``userData`` フィールドとして送信される

        .. warning::
            この機能はLavalink 4+（BETA以外）でのみ利用可能

        Examples
        --------
            .. code:: python
                track: wavelink.Playable = wavelink.Playable.search("QUERY")
                track.extras = {"requester_id": 1234567890}
                # 後で...
                print(track.extras.requester_id)
                # または
                print(dict(track.extras)["requester_id"])

        .. versionadded:: 3.1.0
        """
        return self._extras

    @extras.setter
    def extras(self, __value: ExtrasNamespace | dict[str, Any]) -> None:
        if isinstance(__value, ExtrasNamespace):
            self._extras = __value
        else:
            self._extras = ExtrasNamespace(__value)

    @property
    def raw_data(self) -> TrackPayload:
        """この ``Playable`` の生データ（Lavalinkから受信）

        このデータを使って ``Playable`` オブジェクトを再構築可能

        Examples
        --------
            .. code:: python3
                # 例...
                old_data = track.raw_data

                # 後で...
                track: wavelink.Playable = wavelink.Playable(old_data)


        .. versionadded:: 3.2.0
        """
        return self._raw_data

    @classmethod
    async def search(
        cls, query: str, /, *, source: TrackSource | str | None = TrackSource.YouTubeMusic, node: Node | None = None
    ) -> Search:
        """指定クエリで :class:`~wavelink.Playable` または :class:`~wavelink.Playlist` を検索するクラスメソッド

        .. note::
            このメソッドは :meth:`wavelink.Pool.fetch_tracks` と異なり、URLでない場合は適切な検索プレフィックスを自動付与する（source引数で制御可能）
        .. note::
            検索にはこのメソッドの利用を推奨

        Parameters
        ----------
        query: str
            検索クエリ。URLでない場合は ``source`` キーワード引数に応じたプレフィックスが自動付与される
            URLの場合はプレフィックスは付与されない
        source: :class:`TrackSource` | str | None
            検索時のプレフィックスを指定。Noneの場合は付与しない（ただしURLの場合は常に付与しない）
            基本的な検索（YouTube, YouTubeMusic, SoundCloud）は :class:`wavelink.TrackSource` を参照
            プラグイン検索時は ``str`` で "spsearch:" などを指定
            デフォルトは :attr:`wavelink.TrackSource.YouTubeMusic`（"ytmsearch:" 相当）
        node: :class:`~wavelink.Node` | None
            検索に使用する :class:`~wavelink.Node`。省略時は自動選択

        Returns
        -------
        :class:`wavelink.Search`
            :class:`Playable` のリストまたは :class:`Playlist` のいずれか。該当なしの場合は空リスト

        Raises
        ------
        LavalinkLoadException
            クエリに基づくLavalinkのロード失敗時に発生

        Examples
        --------
        .. code:: python3
            # デフォルト（ytsearch:）で検索
            tracks: wavelink.Search = await wavelink.Playable.search("Ocean Drive")
            if not tracks:
                # トラックが見つからない場合の処理
                ...

            # URLで検索
            tracks: wavelink.Search = await wavelink.Playable.search("https://www.youtube.com/watch?v=KDxJlW6cxRk")
            ...

            # Spotify/LavaSrcプラグインで検索
            tracks: wavelink.Search = await wavelink.Playable.search("4b93D55xv3YCH5mT4p6HPn", source="spsearch")
            ...

            # Spotify/LavaSrcプラグインでURL検索
            tracks: wavelink.Search = await wavelink.Playable.search("https://open.spotify.com/track/4b93D55xv3YCH5mT4p6HPn")
            ...

            # プレイリスト検索
            tracks: wavelink.Search = await wavelink.Playable.search("https://open.spotify.com/playlist/37i9dQZF1DWXRqgorJj26U")
            ...


        .. versionchanged:: 3.0.0
            v3.0.0で大幅に仕様変更。ノード指定は自動選択に統一
        """
        prefix: TrackSource | str | None = _source_mapping.get(source, source)
        check = yarl.URL(query)

        if check.host:
            tracks: Search = await wavelink.Pool.fetch_tracks(query, node=node)
            return tracks

        if not prefix:
            term: str = query
        else:
            assert not isinstance(prefix, TrackSource)
            term: str = f"{prefix.removesuffix(':')}:{query}"

        tracks: Search = await wavelink.Pool.fetch_tracks(term, node=node)
        return tracks


class Playlist:
    """wavelinkのプレイリストコンテナクラス

    このクラスは :meth:`Playable.search` や :meth:`wavelink.Pool.fetch_tracks` で生成・返却される

    プレイリスト情報と :class:`Playable` のリストを保持し、:meth:`wavelink.Player.play` で直接利用可能

    .. warning::
        このクラスを手動でインスタンス化しないこと。:meth:`Playable.search` または :meth:`wavelink.Pool.fetch_tracks` を利用
    .. warning::
        このクラスで ``.search`` を直接呼び出すことはできない。:meth:`Playable.search` を参照
    .. note::
        このクラスは :class:`Playable` と同様に :class:`wavelink.Queue` へ直接追加可能。追加時は全トラックが個別にキューへ追加される

    .. container:: operations

        .. describe:: str(x)
            プレイリスト名を返す
        .. describe:: repr(x)
            プレイリストの公式な文字列表現
        .. describe:: x == y
            プレイリストの等価比較
        .. describe:: len(x)
            プレイリスト内のトラック数を返す
        .. describe:: x[0]
            指定インデックスのトラックを返す
        .. describe:: x[0:2]
            指定スライスのトラックリストを返す
        .. describe:: for x in y
            プレイリスト内のトラックをイテレート
        .. describe:: reversed(x)
            プレイリスト内のトラックを逆順イテレート
        .. describe:: x in y
            プレイリストに :class:`Playable` が含まれるか判定

    Attributes
    ----------
    name: str
        プレイリスト名
    selected: int
        Lavalinkで選択されたトラックのインデックス
    tracks: list[:class:`Playable`]
        プレイリスト内の :class:`Playable` のリスト
    type: str | None
        プレイリスト種別（プラグイン利用時のみ）
    url: str | None
        プレイリストのURL（プラグイン利用時のみ）
    artwork: str | None
        プレイリストのアートワークURL（プラグイン利用時のみ）
    author: str | None
        プレイリストの作者（プラグイン利用時のみ）
    """

    def __init__(self, data: PlaylistPayload) -> None:
        info: PlaylistInfoPayload = data["info"]
        self.name: str = info["name"]
        self.selected: int = info["selectedTrack"]

        playlist_info: PlaylistInfo = PlaylistInfo(data)
        self.tracks: list[Playable] = [Playable(data=track, playlist=playlist_info) for track in data["tracks"]]

        plugin: dict[Any, Any] = data["pluginInfo"]
        self.type: str | None = plugin.get("type")
        self.url: str | None = plugin.get("url")
        self.artwork: str | None = plugin.get("artworkUrl")
        self.author: str | None = plugin.get("author")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Playlist(name={self.name}, tracks={len(self.tracks)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Playlist):
            return NotImplemented

        return self.name == other.name and self.tracks == other.tracks

    def __len__(self) -> int:
        return len(self.tracks)

    @overload
    def __getitem__(self, index: int) -> Playable: ...

    @overload
    def __getitem__(self, index: slice) -> list[Playable]: ...

    def __getitem__(self, index: int | slice) -> Playable | list[Playable]:
        return self.tracks[index]

    def __iter__(self) -> Iterator[Playable]:
        return self.tracks.__iter__()

    def __reversed__(self) -> Iterator[Playable]:
        return self.tracks.__reversed__()

    def __contains__(self, item: Playable) -> bool:
        return item in self.tracks

    def pop(self, index: int = -1) -> Playable:
        return self.tracks.pop(index)

    def track_extras(self, **attrs: object) -> None:
        """このプレイリスト内の全 :class:`Playable` に指定キーワード属性を一括付与するメソッド

        :class:`Playable` に状態（例: requester属性）を付与したい場合に便利

        .. warning::
            :class:`Playable` の既存プロパティを上書きしようとすると失敗する

        Parameters
        ----------
        **attrs
            各 :class:`Playable` に付与する属性名=値

        Examples
        --------
        .. code:: python3
            playlist.track_extras(requester=ctx.author)
            track: wavelink.Playable = playlist[0]
            print(track.requester)
        """
        for track in self.tracks:
            for name, value in attrs.items():
                setattr(track, name, value)

    @property
    def extras(self) -> ExtrasNamespace:
        """:class:`~wavelink.ExtrasNamespace` 型の追加情報を返すプロパティ

        このプロパティには有効な ``str`` キーと任意のJSON値を持つdict、または :class:`~wavelink.ExtrasNamespace` を設定可能
        dictを渡すと自動的に :class:`~wavelink.ExtrasNamespace` に変換される
        extrasはプレイリスト内各トラックの ``userData`` フィールドとしてLavalinkに送信される

        .. warning::
            この機能はLavalink 4+（BETA以外）でのみ利用可能

        Examples
        --------
            .. code:: python
                playlist: wavelink.Search = wavelink.Playable.search("QUERY")
                playlist.extras = {"requester_id": 1234567890}
                # 後で...
                print(track.extras.requester_id)
                # または
                print(dict(track.extras)["requester_id"])

        .. versionadded:: 3.2.0
        """
        return self._extras

    @extras.setter
    def extras(self, __value: ExtrasNamespace | dict[str, Any]) -> None:
        if isinstance(__value, ExtrasNamespace):
            self._extras = __value
        else:
            self._extras = ExtrasNamespace(__value)

        for track in self.tracks:
            track.extras = __value


class PlaylistInfo:
    """wavelinkのPlaylistInfoコンテナクラス

    プレイリストの各種情報を保持するが、トラック自体は含まない

    このクラスはトラックに元の :class:`wavelink.Playlist` 情報を付与するために利用される

    Attributes
    ----------
    name: str
        プレイリスト名
    selected: int
        Lavalinkで選択されたトラックのインデックス
    tracks: int
        プレイリストが元々含んでいたトラック数
    type: str | None
        プレイリスト種別（プラグイン利用時のみ）
    url: str | None
        プレイリストのURL（プラグイン利用時のみ）
    artwork: str | None
        プレイリストのアートワークURL（プラグイン利用時のみ）
    author: str | None
        プレイリストの作者（プラグイン利用時のみ）
    """

    __slots__ = ("name", "selected", "tracks", "type", "url", "artwork", "author")

    def __init__(self, data: PlaylistPayload) -> None:
        info: PlaylistInfoPayload = data["info"]
        self.name: str = info["name"]
        self.selected: int = info["selectedTrack"]

        self.tracks: int = len(data["tracks"])

        plugin: dict[Any, Any] = data["pluginInfo"]
        self.type: str | None = plugin.get("type")
        self.url: str | None = plugin.get("url")
        self.artwork: str | None = plugin.get("artworkUrl")
        self.author: str | None = plugin.get("author")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"PlaylistInfo(name={self.name}, tracks={self.tracks})"

    def __len__(self) -> int:
        return self.tracks
