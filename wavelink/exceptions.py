from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .types.response import ErrorResponse, LoadedErrorPayload


__all__ = (
    "WavelinkException",
    "NodeException",
    "InvalidClientException",
    "AuthorizationFailedException",
    "InvalidNodeException",
    "LavalinkException",
    "LavalinkLoadException",
    "InvalidChannelStateException",
    "ChannelTimeoutException",
    "QueueEmpty",
)


class WavelinkException(Exception):
    """wavelinkの全ての例外の基底クラス
    """


class NodeException(WavelinkException):
    """ノードで不明または一般的なエラーが発生したときに使う例外

    ノードへの接続時にエラーが起きた場合などに発生

    Attributes
    ----------
    status: int | None
        リクエスト時に受信したステータスコード。Noneの場合もある
    """

    def __init__(self, msg: str | None = None, status: int | None = None) -> None:
        super().__init__(msg)

        self.status = status


class InvalidClientException(WavelinkException):
    """無効な :class:`discord.Client` を :class:`wavelink.Node` に接続しようとしたときに使う例外
    """


class AuthorizationFailedException(WavelinkException):
    """Lavalinkが指定されたパスワードで :class:`~wavelink.Node` の認証に失敗したときに使う例外
    """


class InvalidNodeException(WavelinkException):
    """:class:`Pool` から存在しない :class:`Node` を取得しようとした場合や ``Pool`` が空のときに使う例外

    :meth:`~wavelink.Player.switch_node` に無効なノードを指定した場合にも発生
    """


class LavalinkException(WavelinkException):
    """Lavalinkが無効なレスポンスを返した場合に発生する例外

    Attributes
    ----------
    status: int
        レスポンスのステータスコード
    reason: str | None
        レスポンスの理由。理由が提供されていない場合は ``None`` 
    """

    def __init__(self, msg: str | None = None, /, *, data: ErrorResponse) -> None:
        self.timestamp: int = data["timestamp"]
        self.status: int = data["status"]
        self.error: str = data["error"]
        self.trace: str | None = data.get("trace")
        self.path: str = data["path"]

        if not msg:
            msg = f"Lavalinkへのリクエストに失敗しました: status={self.status}, reason={self.error}, path={self.path}"

        super().__init__(msg)


class LavalinkLoadException(WavelinkException):
    """Lavalinkでトラックの読み込み中にエラーが発生した場合に発生する例外

    Attributes
    ----------
    error: str
        Lavalinkからのエラーメッセージ
    severity: str
        Lavalinkから送信されたこのエラーの重大度
    cause: str
        Lavalinkから送信されたこのエラーの原因
    """

    def __init__(self, msg: str | None = None, /, *, data: LoadedErrorPayload) -> None:
        self.error: str = data["message"]
        self.severity: str = data["severity"]
        self.cause: str = data["cause"]

        if not msg:
            msg = f"トラックの読み込みに失敗しました: error={self.error}, severity={self.severity}, cause={self.cause}"

        super().__init__(msg)


class InvalidChannelStateException(WavelinkException):
    """:class:`~wavelink.Player` が無効なチャンネルに接続しようとした場合、またはそのチャンネルを使用する権限がない場合に発生する例外"""


class ChannelTimeoutException(WavelinkException):
    """ボイスチャンネルへの接続がタイムアウトした場合に発生する例外"""


class QueueEmpty(WavelinkException):
    """空のキューから取得しようとした場合に発生する例外"""
