from __future__ import annotations

import logging
import secrets
import urllib.parse
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeAlias

import aiohttp
from discord.utils import classproperty

from . import __version__
from .enums import NodeStatus
from .exceptions import (
    AuthorizationFailedException,
    InvalidClientException,
    InvalidNodeException,
    LavalinkException,
    LavalinkLoadException,
    NodeException,
)
from .lfu import LFUCache
from .payloads import *
from .tracks import Playable, Playlist
from .websocket import Websocket


if TYPE_CHECKING:
    from collections.abc import Iterable

    import discord

    from .player import Player
    from .types.request import Request, UpdateSessionRequest
    from .types.response import (
        EmptyLoadedResponse,
        ErrorLoadedResponse,
        ErrorResponse,
        InfoResponse,
        PlayerResponse,
        PlaylistLoadedResponse,
        SearchLoadedResponse,
        StatsResponse,
        TrackLoadedResponse,
        UpdateResponse,
    )
    from .types.tracks import TrackPayload

    LoadedResponse: TypeAlias = (
        TrackLoadedResponse | SearchLoadedResponse | PlaylistLoadedResponse | EmptyLoadedResponse | ErrorLoadedResponse
    )


__all__ = ("Node", "Pool")


logger: logging.Logger = logging.getLogger(__name__)


Method = Literal["GET", "POST", "PATCH", "DELETE", "PUT", "OPTIONS"]


class Node:
    """NodeはLavalinkへの接続を表すクラス

    WebSocketの維持やセッションの再開、APIリクエストの送信、接続中の全 :class:`~wavelink.Player` の管理などを担当

    .. container:: operations

        .. describe:: node == other

            このNodeが他のNode参照と等しいかどうかを判定

        .. describe:: repr(node)

            このNodeの公式な文字列表現

    Parameters
    ----------
    identifier: str | None
        このNodeの一意な識別子。Noneの場合は自動生成
    uri: str
        Lavalinkに接続するためのURL/URI。例: ``http://localhost:2333`` やドメイン、IPアドレス+ポートなど
    password: str
        このNodeに接続・認証するためのパスワード
    session: aiohttp.ClientSession | None
        WebSocketやREST接続用の :class:`aiohttp.ClientSession`。Noneなら自動生成
    heartbeat: Optional[float]
        WebSocketのキープアライブ間隔（秒）。通常は変更不要
    retries: int | None
        接続や再接続時のリトライ回数。Noneなら無限リトライ。デフォルトはNone
    client: :class:`discord.Client` | None
        このNodeに接続する :class:`discord.Client` またはそのサブクラス（例: commands.Bot）。未指定の場合は :meth:`wavelink.Pool.connect` で指定が必要
    resume_timeout: Optional[int]
        ネットワーク障害時にセッション再開を有効にする秒数。0以下で無効。デフォルトは60
    inactive_player_timeout: int | None
        このNodeに接続する各Playerの :attr:`wavelink.Player.inactive_timeout` のデフォルト値。デフォルトは300
    inactive_channel_tokens: int | None
        このNodeに接続する各Playerの :attr:`wavelink.Player.inactive_channel_tokens` のデフォルト値。デフォルトは3

        詳細: :func:`on_wavelink_inactive_player` も参照
    """

    def __init__(
        self,
        *,
        identifier: str | None = None,
        uri: str,
        password: str,
        session: aiohttp.ClientSession | None = None,
        heartbeat: float = 15.0,
        retries: int | None = None,
        client: discord.Client | None = None,
        resume_timeout: int = 60,
        inactive_player_timeout: int | None = 300,
        inactive_channel_tokens: int | None = 3,
    ) -> None:
        self._identifier = identifier or secrets.token_urlsafe(12)
        self._uri = uri.removesuffix("/")
        self._password = password
        self._session = session or aiohttp.ClientSession()
        self._heartbeat = heartbeat
        self._retries = retries
        self._client = client
        self._resume_timeout = resume_timeout

        self._status: NodeStatus = NodeStatus.DISCONNECTED
        self._has_closed: bool = False
        self._session_id: str | None = None

        self._players: dict[int, Player] = {}
        self._total_player_count: int | None = None

        self._spotify_enabled: bool = False

        self._websocket: Websocket | None = None

        if inactive_player_timeout and inactive_player_timeout < 10:
            logger.warning('Setting "inactive_player_timeout" below 10 seconds may result in unwanted side effects.')

        self._inactive_player_timeout = (
            inactive_player_timeout if inactive_player_timeout and inactive_player_timeout > 0 else None
        )

        self._inactive_channel_tokens = inactive_channel_tokens

    def __repr__(self) -> str:
        return f"Node(identifier={self.identifier}, uri={self.uri}, status={self.status}, players={len(self.players)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return NotImplemented

        return other.identifier == self.identifier

    @property
    def headers(self) -> dict[str, str]:
        """A property that returns the headers configured for sending API and websocket requests.

        .. warning::

            This includes your Node password. Please be vigilant when using this property.
        """
        assert self.client is not None
        assert self.client.user is not None

        data = {
            "Authorization": self.password,
            "User-Id": str(self.client.user.id),
            "Client-Name": f"Wavelink/{__version__}",
        }

        return data

    @property
    def identifier(self) -> str:
        """この :class:`Node` の一意な識別子

        .. versionchanged:: 3.0.0

            このプロパティは以前 ``id`` という名前だった
        """
        return self._identifier

    @property
    def uri(self) -> str:
        """この :class:`Node` をLavalinkに接続するためのURI"""
        return self._uri

    @property
    def status(self) -> NodeStatus:
        """現在の :class:`Node` の状態

        参照: :class:`~wavelink.NodeStatus`
        """
        return self._status

    @property
    def players(self) -> dict[int, Player]:
        """:attr:`discord.Guild.id` と :class:`~wavelink.Player` のマッピング

        .. versionchanged:: 3.1.1

            このプロパティは内部マッピングのシャローコピーを返すようになった
        """
        return self._players.copy()

    @property
    def client(self) -> discord.Client | None:
        """この :class:`Node` に紐づく :class:`discord.Client` を返す

        未設定の場合は ``None`` となる

        .. versionadded:: 3.0.0
        """
        return self._client

    @property
    def password(self) -> str:
        """この :class:`Node` をLavalinkに接続する際のパスワードを返す

        .. versionadded:: 3.0.0
        """
        return self._password

    @property
    def heartbeat(self) -> float:
        """この :class:`Node` のWebSocketが送信するハートビート間隔（秒）を返す

        .. versionadded:: 3.0.0
        """
        return self._heartbeat

    @property
    def session_id(self) -> str | None:
        """LavalinkのセッションIDを返す。未接続の場合はNone

        .. versionadded:: 3.0.0
        """
        return self._session_id

    async def _pool_closer(self) -> None:
        try:
            await self._session.close()
        except Exception:
            pass

        if not self._has_closed:
            await self.close()

    async def close(self, eject: bool = False) -> None:
        """このNodeをクローズしクリーンアップするメソッド

        このメソッドの完了後、 ``on_wavelink_node_closed`` イベントが発火される

        このメソッドはNodeのWebSocketを切断し、全てのPlayerも切断状態にする

        Parameters
        ----------
        eject: bool
            ``True`` の場合、このNodeをPoolから除外する。デフォルトは ``False``

        .. versionchanged:: 3.2.1

            ``eject`` パラメータを追加。接続中のPlayerが切断されないバグを修正
        """
        disconnected: list[Player] = []

        for player in self._players.copy().values():
            try:
                await player.disconnect()
            except Exception as e:
                logger.debug("An error occured while disconnecting a player in the close method of %r: %s", self, e)
                pass

            disconnected.append(player)

        if self._websocket is not None:
            await self._websocket.cleanup()

        self._status = NodeStatus.DISCONNECTED
        self._session_id = None
        self._players = {}

        self._has_closed = True

        if eject:
            getattr(Pool, "_Pool__nodes").pop(self.identifier, None)

        # Dispatch Node Closed Event... node, list of disconnected players
        if self.client is not None:
            self.client.dispatch("wavelink_node_closed", self, disconnected)

    async def _connect(self, *, client: discord.Client | None) -> None:
        client_ = self._client or client

        if not client_:
            raise InvalidClientException(f"Unable to connect {self!r} as you have not provided a valid discord.Client.")

        self._client = client_

        self._has_closed = False
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()

        websocket: Websocket = Websocket(node=self)
        self._websocket = websocket
        await websocket.connect()

    async def send(
        self, method: Method = "GET", *, path: str, data: Any | None = None, params: dict[str, Any] | None = None
    ) -> Any:
        """Lavalinkノードへリクエストを送信するメソッド

        .. warning::

            通常このメソッドは直接使わない。 :class:`~Node`、:class:`~Pool`、:class:`~wavelink.Player` の組み込みメソッドを利用すること
            特定のプラグインデータをLavalinkへ送信したい場合のみ使用

            このメソッドの利用はPlayerやNodeに予期しない副作用をもたらす可能性がある

        Parameters
        ----------
        method: Optional[str]
            このリクエストで使用するHTTPメソッド。"GET"、"POST"、"PATCH"、"PUT"、"DELETE"、"OPTIONS" から選択。デフォルトは"GET"
        path: str
            リクエスト先のパス。例: "/v4/stats"
        data: Any | None
            リクエストに付与するJSONデータ（dict[str, Any]形式でJSON変換可能なもの）
        params: Optional[dict[str, Any]]
            クエリパラメータのdict。 ``path`` にクエリを含める場合はここに渡さないこと。例: {"thing": 1, "other": 2} → "?thing=1&other=2"

        Returns
        -------
        Any
            Lavalinkからのレスポンス。None、str、またはJSON

        Raises
        ------
        LavalinkException
            リクエスト時にエラーが発生した場合
        NodeException
            リクエスト時にエラーが発生し、Lavalinkからエラー情報が返されなかった場合

        .. versionadded:: 3.0.0
        """
        clean_path: str = path.removesuffix("/")
        uri: str = f"{self.uri}/{clean_path}"

        if params is None:
            params = {}

        async with self._session.request(
            method=method, url=uri, params=params, json=data, headers=self.headers
        ) as resp:
            if resp.status == 204:
                return

            if resp.status >= 300:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

            try:
                rdata: Any = await resp.json()
            except aiohttp.ContentTypeError:
                pass
            else:
                return rdata

            try:
                body: str = await resp.text()
            except aiohttp.ClientError:
                return

            return body

    async def _fetch_players(self) -> list[PlayerResponse]:
        uri: str = f"{self.uri}/v4/sessions/{self.session_id}/players"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: list[PlayerResponse] = await resp.json()
                return resp_data

            else:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

    async def fetch_players(self) -> list[PlayerResponsePayload]:
        """このノードに接続中の全プレイヤー情報をLavalinkから取得するメソッド

        .. warning::

            このペイロードは :class:`wavelink.Player` クラスとは異なる。Lavalinkから受信した生データ

        Returns
        -------
        list[:class:`PlayerResponsePayload`]
            このノードに接続中の各プレイヤーを表す :class:`PlayerResponsePayload` のリスト

        Raises
        ------
        LavalinkException
            リクエスト時にエラーが発生した場合
        NodeException
            リクエスト時にエラーが発生し、Lavalinkからエラー情報が返されなかった場合

        .. versionadded:: 3.1.0
        """
        data: list[PlayerResponse] = await self._fetch_players()

        payload: list[PlayerResponsePayload] = [PlayerResponsePayload(p) for p in data]
        return payload

    async def _fetch_player(self, guild_id: int, /) -> PlayerResponse:
        uri: str = f"{self.uri}/v4/sessions/{self.session_id}/players/{guild_id}"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: PlayerResponse = await resp.json()
                return resp_data

            else:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

    async def fetch_player_info(self, guild_id: int, /) -> PlayerResponsePayload | None:
        """指定したギルドのプレイヤー情報をLavalinkから取得するメソッド

        .. warning::

            このペイロードは :class:`wavelink.Player` クラスとは異なる。Lavalinkから受信した生データ。:meth:`~wavelink.Node.get_player` も参照

        Parameters
        ----------
        guild_id: int
            情報を取得したいギルドのID

        Returns
        -------
        :class:`PlayerResponsePayload` | None
            指定ギルドIDに紐づくプレイヤー情報。該当がなければ ``None``

        Raises
        ------
        LavalinkException
            リクエスト時にエラーが発生した場合
        NodeException
            リクエスト時にエラーが発生し、Lavalinkからエラー情報が返されなかった場合

        .. versionadded:: 3.1.0
        """
        try:
            data: PlayerResponse = await self._fetch_player(guild_id)
        except LavalinkException as e:
            if e.status == 404:
                return None

            raise e

        payload: PlayerResponsePayload = PlayerResponsePayload(data)
        return payload

    async def _update_player(self, guild_id: int, /, *, data: Request, replace: bool = False) -> PlayerResponse:
        no_replace: bool = not replace

        uri: str = f"{self.uri}/v4/sessions/{self.session_id}/players/{guild_id}?noReplace={no_replace}"

        async with self._session.patch(url=uri, json=data, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: PlayerResponse = await resp.json()
                return resp_data

            else:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

    async def _destroy_player(self, guild_id: int, /) -> None:
        uri: str = f"{self.uri}/v4/sessions/{self.session_id}/players/{guild_id}"

        async with self._session.delete(url=uri, headers=self.headers) as resp:
            if resp.status == 204:
                return

            try:
                exc_data: ErrorResponse = await resp.json()
            except Exception as e:
                logger.warning("An error occured making a request on %r: %s", self, e)
                raise NodeException(status=resp.status)

            raise LavalinkException(data=exc_data)

    async def _update_session(self, *, data: UpdateSessionRequest) -> UpdateResponse:
        uri: str = f"{self.uri}/v4/sessions/{self.session_id}"

        async with self._session.patch(url=uri, json=data, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: UpdateResponse = await resp.json()
                return resp_data

            else:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

    async def _fetch_tracks(self, query: str) -> LoadedResponse:
        uri: str = f"{self.uri}/v4/loadtracks?identifier={query}"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: LoadedResponse = await resp.json()
                return resp_data

            else:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

    async def _decode_track(self) -> TrackPayload: ...

    async def _decode_tracks(self) -> list[TrackPayload]: ...

    async def _fetch_info(self) -> InfoResponse:
        uri: str = f"{self.uri}/v4/info"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: InfoResponse = await resp.json()
                return resp_data

            else:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

    async def fetch_info(self) -> InfoResponsePayload:
        """このLavalinkノードのinfoレスポンスデータを取得するメソッド

        Returns
        -------
        :class:`InfoResponsePayload`
            このNodeに紐づく :class:`InfoResponsePayload`

        Raises
        ------
        LavalinkException
            リクエスト時にエラーが発生した場合
        NodeException
            リクエスト時にエラーが発生し、Lavalinkからエラー情報が返されなかった場合

        .. versionadded:: 3.1.0
        """
        data: InfoResponse = await self._fetch_info()

        payload: InfoResponsePayload = InfoResponsePayload(data)
        return payload

    async def _fetch_stats(self) -> StatsResponse:
        uri: str = f"{self.uri}/v4/stats"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: StatsResponse = await resp.json()
                return resp_data

            else:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

    async def fetch_stats(self) -> StatsResponsePayload:
        """このLavalinkノードのstatsレスポンスデータを取得するメソッド

        Returns
        -------
        :class:`StatsResponsePayload`
            このNodeに紐づく :class:`StatsResponsePayload`

        Raises
        ------
        LavalinkException
            リクエスト時にエラーが発生した場合
        NodeException
            リクエスト時にエラーが発生し、Lavalinkからエラー情報が返されなかった場合

        .. versionadded:: 3.1.0
        """
        data: StatsResponse = await self._fetch_stats()

        payload: StatsResponsePayload = StatsResponsePayload(data)
        return payload

    async def _fetch_version(self) -> str:
        uri: str = f"{self.uri}/version"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                return await resp.text()

            try:
                exc_data: ErrorResponse = await resp.json()
            except Exception as e:
                logger.warning("An error occured making a request on %r: %s", self, e)
                raise NodeException(status=resp.status)

            raise LavalinkException(data=exc_data)

    async def fetch_version(self) -> str:
        """このLavalinkノードのバージョン文字列を取得するメソッド

        Returns
        -------
        str
            このLavalinkノードのバージョン文字列

        Raises
        ------
        LavalinkException
            リクエスト時にエラーが発生した場合
        NodeException
            リクエスト時にエラーが発生し、Lavalinkからエラー情報が返されなかった場合

        .. versionadded:: 3.1.0
        """
        data: str = await self._fetch_version()
        return data

    def get_player(self, guild_id: int, /) -> Player | None:
        """指定した :attr:`discord.Guild.id` に紐づく :class:`~wavelink.Player` を返す

        Parameters
        ----------
        guild_id: int
            :attr:`discord.Guild.id` を指定し、そのギルドの :class:`~wavelink.Player` を取得

        Returns
        -------
        Optional[:class:`~wavelink.Player`]
            指定ギルドIDに紐づくPlayer。該当がなければNone
        """
        return self._players.get(guild_id, None)


class Pool:
    """wavelinkのPoolは :class:`~wavelink.Node` のコレクションとトラック検索用のヘルパーメソッドをまとめたクラス

    :class:`~wavelink.Node` への接続はこのPoolを使う

    .. note::

        このクラスの全メソッド・属性はクラスレベル。インスタンス化しないこと
    """

    __nodes: ClassVar[dict[str, Node]] = {}
    __cache: LFUCache | None = None

    @classmethod
    async def connect(
        cls, *, nodes: Iterable[Node], client: discord.Client | None = None, cache_capacity: int | None = None
    ) -> dict[str, Node]:
        """指定したIterable[:class:`Node`]をLavalinkに接続するクラスメソッド

        Parameters
        ----------
        nodes: Iterable[:class:`Node`]
            Lavalinkに接続する :class:`Node` のIterable
        client: :class:`discord.Client` | None
            :class:`Node` の接続に使用する :class:`discord.Client`。Node側でclientが既に設定されている場合は上書きしない。デフォルトはNone
        cache_capacity: int | None
            トラック検索結果のキャッシュ数（実験的機能）。Noneでキャッシュ無効。デフォルトはNone

        Returns
        -------
        dict[str, :class:`Node`]
            :attr:`Node.identifier` をキー、:class:`Node` を値とする :class:`Pool` のマッピング

        Raises
        ------
        AuthorizationFailedException
            ノードのパスワードが間違っている場合に発生
        InvalidClientException
            渡された :class:`discord.Client` が不正な場合に発生
        NodeException
            ノードの接続に失敗した場合に発生。Lavalinkのバージョンが4であることやポート設定を確認

        .. versionchanged:: 3.0.0
            ``client`` パラメータが必須でなくなった。``cache_capacity`` パラメータが追加
        """
        for node in nodes:
            client_ = node.client or client

            if node.identifier in cls.__nodes:
                msg: str = f'Unable to connect {node!r} as you already have a node with identifier "{node.identifier}"'
                logger.error(msg)

                continue

            if node.status in (NodeStatus.CONNECTING, NodeStatus.CONNECTED):
                logger.error("Unable to connect %r as it is already in a connecting or connected state.", node)
                continue

            try:
                await node._connect(client=client_)
            except InvalidClientException as e:
                logger.error(e)
            except AuthorizationFailedException:
                logger.error("Failed to authenticate %r on Lavalink with the provided password.", node)
            except NodeException:
                logger.error(
                    "Failed to connect to %r. Check that your Lavalink major version is '4' and that you are trying to connect to Lavalink on the correct port.",
                    node,
                )
            else:
                cls.__nodes[node.identifier] = node

        if cache_capacity is not None and cls.nodes:
            if cache_capacity <= 0:
                logger.warning("LFU Request cache capacity must be > 0. Not enabling cache.")

            else:
                cls.__cache = LFUCache(capacity=cache_capacity)
                logger.info("Experimental request caching has been toggled ON. To disable run Pool.toggle_cache()")

        return cls.nodes

    @classmethod
    async def reconnect(cls) -> dict[str, Node]:
        for node in cls.__nodes.values():
            if node.status is not NodeStatus.DISCONNECTED:
                continue

            try:
                await node._connect(client=None)
            except InvalidClientException as e:
                logger.error(e)
            except AuthorizationFailedException:
                logger.error("Failed to authenticate %r on Lavalink with the provided password.", node)
            except NodeException:
                logger.error(
                    "Failed to connect to %r. Check that your Lavalink major version is '4' and that you are trying to connect to Lavalink on the correct port.",
                    node,
                )

        return cls.nodes

    @classmethod
    async def close(cls) -> None:
        """このPool上の全 :class:`~wavelink.Node` をクローズ・クリーンアップするクラスメソッド

        各ノードに対して :meth:`wavelink.Node.close` を呼び出す

        .. versionadded:: 3.0.0
        """
        for node in cls.__nodes.values():
            await node.close()

    @classproperty
    def nodes(cls) -> dict[str, Node]:
        """:attr:`Node.identifier` をキー、:class:`Node` を値とする、これまでに正常接続されたノードのマッピングを返すプロパティ

        .. versionchanged:: 3.0.0
            このプロパティはコピーを返すようになった
        """
        nodes = cls.__nodes.copy()
        return nodes

    @classmethod
    def get_node(cls, identifier: str | None = None, /) -> Node:
        """指定したidentifierの :class:`Node` を :class:`Pool` から取得するクラスメソッド

        identifierを指定しない場合は「最適」なノードを返す

        Parameters
        ----------
        identifier: str | None
            取得したい :class:`Node` のidentifier（省略可）

        Raises
        ------
        InvalidNodeException
            指定したidentifierのNodeが見つからない場合、またはPoolにNodeが存在しない場合に発生

        .. versionchanged:: 3.0.0
            ``id`` パラメータが ``identifier`` へ変更され、位置専用引数になった
        """
        if identifier:
            if identifier not in cls.__nodes:
                raise InvalidNodeException(f'A Node with the identifier "{identifier}" does not exist.')

            return cls.__nodes[identifier]

        nodes: list[Node] = [n for n in cls.__nodes.values() if n.status is NodeStatus.CONNECTED]
        if not nodes:
            raise InvalidNodeException("No nodes are currently assigned to the wavelink.Pool in a CONNECTED state.")

        return sorted(nodes, key=lambda n: n._total_player_count or len(n.players))[0]

    @classmethod
    async def fetch_tracks(cls, query: str, /, *, node: Node | None = None) -> list[Playable] | Playlist:
        """指定したクエリで :class:`~wavelink.Playable` または :class:`~wavelink.Playlist` を検索するクラスメソッド

        Parameters
        ----------
        query: str
            検索クエリ。URLでない場合は "ytsearch:曲名" など適切なプレフィックスを付与
        node: :class:`~wavelink.Node` | None
            検索に使用する :class:`~wavelink.Node`（省略時は自動選択）

        Returns
        -------
        list[Playable] | Playlist
            検索結果の :class:`~wavelink.Playable` のリスト、または :class:`~wavelink.Playlist`。該当なしの場合は空リスト

        Raises
        ------
        LavalinkLoadException
            クエリに基づくLavalinkのロード失敗時に発生

        .. versionchanged:: 3.0.0
            以前は ``.get_tracks`` および ``.get_playlist`` という名称だったが統合。検索結果に応じて型が変わるようになった
            ``cls`` パラメータは廃止
        .. versionadded:: 3.4.0
            ``node`` キーワード専用引数を追加
        """

        # TODO: Documentation Extension for `.. positional-only::` marker.
        encoded_query: str = urllib.parse.quote(query)

        if cls.__cache is not None:
            potential: list[Playable] | Playlist = cls.__cache.get(encoded_query, None)

            if potential:
                return potential

        node_: Node = node or cls.get_node()
        resp: LoadedResponse = await node_._fetch_tracks(encoded_query)

        if resp["loadType"] == "track":
            track = Playable(data=resp["data"])

            if cls.__cache is not None and not track.is_stream:
                cls.__cache.put(encoded_query, [track])

            return [track]

        elif resp["loadType"] == "search":
            tracks = [Playable(data=tdata) for tdata in resp["data"]]

            if cls.__cache is not None:
                cls.__cache.put(encoded_query, tracks)

            return tracks

        if resp["loadType"] == "playlist":
            playlist: Playlist = Playlist(data=resp["data"])

            if cls.__cache is not None:
                cls.__cache.put(encoded_query, playlist)

            return playlist

        elif resp["loadType"] == "empty":
            return []

        elif resp["loadType"] == "error":
            raise LavalinkLoadException(data=resp["data"])

        else:
            return []

    @classmethod
    def cache(cls, capacity: int | None | bool = None) -> None:
        if capacity in (None, False) or capacity <= 0:
            cls.__cache = None
            return

        if not isinstance(capacity, int):  # type: ignore
            raise ValueError("The LFU cache expects an integer, None or bool.")

        cls.__cache = LFUCache(capacity=capacity)

    @classmethod
    def has_cache(cls) -> bool:
        return cls.__cache is not None
