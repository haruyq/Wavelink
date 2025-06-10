from __future__ import annotations

import asyncio
import random
from collections import deque
from collections.abc import Iterable, Iterator
from typing import SupportsIndex, TypeGuard, overload

from .enums import QueueMode
from .exceptions import QueueEmpty
from .tracks import Playable, Playlist


__all__ = ("Queue",)


class Queue:
    """デフォルトのカスタムwavelinkキュー。:class:`wavelink.Player` 用に設計されたクラス

    .. note::
        :class:`~wavelink.Player` はデフォルトでこのキューを実装している
        :attr:`wavelink.Player.queue` からアクセス可能

    .. container:: operations

        .. describe:: str(queue)
            このキューの文字列表現

        .. describe:: repr(queue)
            このキューの公式な文字列表現

        .. describe:: if queue
            キューにアイテムが存在するかどうかの真偽値判定

        .. describe:: queue(track)
            トラックをキューに追加

        .. describe:: len(queue)
            キュー内のトラック数

        .. describe:: queue[1]
            キュー内のアイテムを参照（キューの状態は変化しない）

        .. describe:: for item in queue
            キューをイテレート

        .. describe:: if item in queue
            特定のトラックがキューに含まれるか判定

        .. describe:: queue[1] = track
            指定インデックスのトラックを設定

        .. describe:: del queue[1]
            指定インデックスのトラックを削除

        .. describe:: reversed(queue)
            キューの逆順イテレータを返す

    Attributes
    ----------
    history: :class:`wavelink.Queue`
        再生済みトラックの履歴キュー。トラックが再生されると履歴に追加される
    """

    def __init__(self, *, history: bool = True) -> None:
        self._items: list[Playable] = []

        self._history: Queue | None = Queue(history=False) if history else None
        self._mode: QueueMode = QueueMode.normal
        self._loaded: Playable | None = None

        self._waiters: deque[asyncio.Future[None]] = deque()
        self._lock = asyncio.Lock()

    @property
    def mode(self) -> QueueMode:
        """:class:`~wavelink.QueueMode` で現在のキューのモードを返すプロパティ

        このプロパティは :class:`~wavelink.QueueMode` で設定可能


        .. versionadded:: 3.0.0
        """
        return self._mode

    @mode.setter
    def mode(self, value: QueueMode) -> None:
        self._mode = value

    @property
    def history(self) -> Queue | None:
        return self._history

    @property
    def count(self) -> int:
        """キュー内のトラック数を返すプロパティ

        Returns
        -------
        int
            キュー内のトラック数


        .. versionadded:: 3.2.0
        """

        return len(self)

    @property
    def is_empty(self) -> bool:
        """キューが空かどうかを返すプロパティ

        Returns
        -------
        bool
            キューが空ならTrue


        .. versionadded:: 3.2.0
        """

        return not bool(self)

    def __str__(self) -> str:
        joined: str = ", ".join([f'"{p}"' for p in self])
        return f"Queue([{joined}])"

    def __repr__(self) -> str:
        return f"Queue(items={len(self)}, history={self.history!r})"

    def __call__(self, item: Playable) -> None:
        self.put(item)

    def __bool__(self) -> bool:
        return bool(self._items)

    @overload
    def __getitem__(self, __index: SupportsIndex, /) -> Playable: ...

    @overload
    def __getitem__(self, __index: slice, /) -> list[Playable]: ...

    def __getitem__(self, __index: SupportsIndex | slice, /) -> Playable | list[Playable]:
        return self._items[__index]

    def __setitem__(self, __index: SupportsIndex, __value: Playable, /) -> None:
        self._check_compatibility(__value)
        self._items[__index] = __value
        self._wakeup_next()

    def __delitem__(self, __index: int | slice, /) -> None:
        del self._items[__index]

    def __contains__(self, __other: Playable) -> bool:
        return __other in self._items

    def __len__(self) -> int:
        return len(self._items)

    def __reversed__(self) -> Iterator[Playable]:
        return reversed(self._items)

    def __iter__(self) -> Iterator[Playable]:
        return iter(self._items)

    def _wakeup_next(self) -> None:
        while self._waiters:
            waiter = self._waiters.popleft()

            if not waiter.done():
                waiter.set_result(None)
                break

    @staticmethod
    def _check_compatibility(item: object) -> TypeGuard[Playable]:
        if not isinstance(item, Playable):
            raise TypeError("This queue is restricted to Playable objects.")
        return True

    @classmethod
    def _check_atomic(cls, item: Iterable[object]) -> TypeGuard[Iterable[Playable]]:
        for track in item:
            cls._check_compatibility(track)
        return True

    def get(self) -> Playable:
        """キューの先頭（左端）からトラックを取得するメソッド

        このメソッドはブロックしない

        .. warning::
            ループモード時は同じトラックを返す。スキップには :meth:`wavelink.Player.skip`（force=True）を推奨
            このメソッドでキューからトラックを削除しないこと。削除には以下を利用:
            - ``del queue[index]``
            - :meth:`wavelink.Queue.remove`
            - :meth:`wavelink.Queue.delete`

        Returns
        -------
        :class:`wavelink.Playable`
            取得したトラック

        Raises
        ------
        QueueEmpty
            キューが空の場合に発生
        """

        if self.mode is QueueMode.loop and self._loaded:
            return self._loaded

        if self.mode is QueueMode.loop_all and not self:
            assert self.history is not None

            self._items.extend(self.history._items)
            self.history.clear()

        if not self:
            raise QueueEmpty("There are no items currently in this queue.")

        track: Playable = self._items.pop(0)
        self._loaded = track

        return track

    def get_at(self, index: int, /) -> Playable:
        """指定インデックスのトラックを取得するメソッド

        .. warning::
            ループモードの都合上、取得したトラックがループ対象としてロードされる
            このメソッドでキューからトラックを削除しないこと。削除には以下を利用:
            - ``del queue[index]``
            - :meth:`wavelink.Queue.remove`
            - :meth:`wavelink.Queue.delete`

        Parameters
        ----------
        index: int
            取得したいトラックのインデックス

        Returns
        -------
        :class:`wavelink.Playable`
            取得したトラック

        Raises
        ------
        QueueEmpty
            キューが空の場合に発生
        IndexError
            インデックスが範囲外の場合に発生


        .. versionadded:: 3.2.0
        """

        if not self:
            raise QueueEmpty("There are no items currently in this queue.")

        track: Playable = self._items.pop(index)
        self._loaded = track

        return track

    def put_at(self, index: int, value: Playable, /) -> None:
        """指定インデックスにトラックを挿入するメソッド

        .. note::
            指定インデックスのトラックを置換せず、リストのinsertのように挿入する

        Parameters
        ----------
        index: int
            挿入位置のインデックス
        value: :class:`wavelink.Playable`
            挿入するトラック

        Raises
        ------
        TypeError
            valueが :class:`wavelink.Playable` でない場合に発生

        .. versionadded:: 3.2.0
        """
        self._check_compatibility(value)
        self._items.insert(index, value)
        self._wakeup_next()

    async def get_wait(self) -> Playable:
        """キューにトラックがあれば先頭を返し、なければ追加されるまで非同期で待機するメソッド

        Returns
        -------
        :class:`wavelink.Playable`
            取得したトラック
        """

        while not self:
            loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
            waiter: asyncio.Future[None] = loop.create_future()

            self._waiters.append(waiter)

            try:
                await waiter
            except:
                waiter.cancel()

                try:
                    self._waiters.remove(waiter)
                except ValueError:  # pragma: no branch
                    pass

                if self and not waiter.cancelled():  # pragma: no cover
                    # something went wrong with this waiter, move on to next
                    self._wakeup_next()
                raise

        return self.get()

    def put(self, item: list[Playable] | Playable | Playlist, /, *, atomic: bool = True) -> int:
        """キューの末尾にアイテムを追加するメソッド

        :class:`wavelink.Playable`、:class:`wavelink.Playlist`、list[:class:`wavelink.Playable`] を受け付ける

        Parameters
        ----------
        item: :class:`wavelink.Playable` | :class:`wavelink.Playlist` | list[:class:`wavelink.Playable`]
            追加するアイテム
        atomic: bool
            アイテムをアトミックに追加するかどうか。Trueの場合、途中でエラーが発生したら何も追加しない。デフォルトはTrue

        Returns
        -------
        int
            追加されたトラック数
        """

        added = 0

        if isinstance(item, Iterable):
            if atomic:
                self._check_atomic(item)
                self._items.extend(item)
                added = len(item)
            else:

                def try_compatibility(track: object) -> bool:
                    try:
                        return self._check_compatibility(track)
                    except TypeError:
                        return False

                passing_items = [track for track in item if try_compatibility(track)]
                self._items.extend(passing_items)
                added = len(passing_items)
        else:
            self._check_compatibility(item)
            self._items.append(item)
            added = 1

        self._wakeup_next()
        return added

    async def put_wait(self, item: list[Playable] | Playable | Playlist, /, *, atomic: bool = True) -> int:
        """キューの末尾にアイテムを非同期で追加するメソッド

        :class:`wavelink.Playable`、:class:`wavelink.Playlist`、list[:class:`wavelink.Playable`] を受け付ける

        .. note::
            挿入順を保証するためロックを実装

        Parameters
        ----------
        item: :class:`wavelink.Playable` | :class:`wavelink.Playlist` | list[:class:`wavelink.Playable`]
            追加するアイテム
        atomic: bool
            アイテムをアトミックに追加するかどうか。Trueの場合、途中でエラーが発生したら何も追加しない。デフォルトはTrue

        Returns
        -------
        int
            追加されたトラック数
        """

        added: int = 0

        async with self._lock:
            if isinstance(item, Iterable):
                if atomic:
                    self._check_atomic(item)
                    self._items.extend(item)
                    self._wakeup_next()
                    return len(item)

                for track in item:
                    try:
                        self._check_compatibility(track)
                    except TypeError:
                        pass
                    else:
                        self._items.append(track)
                        added += 1

                    await asyncio.sleep(0)

            else:
                self._check_compatibility(item)
                self._items.append(item)
                added += 1
                await asyncio.sleep(0)

        self._wakeup_next()
        return added

    def delete(self, index: int, /) -> None:
        """指定インデックスのアイテムをキューから削除するメソッド

        Raises
        ------
        IndexError
            指定インデックスにトラックが存在しない場合に発生

        Examples
        --------
        .. code:: python3
            # インデックス1（2番目）のトラックを削除
            queue.delete(1)

        .. versionchanged:: 3.2.0
            このメソッドはコルーチンではなくなった
        """

        del self._items[index]

    def peek(self, index: int = 0, /) -> Playable:
        """指定インデックスのアイテムを参照するメソッド（キューの状態は変化しない）

        .. note::
            このメソッドはキューを変更せず、アイテムも削除しない

        Parameters
        ----------
        index: int
            参照したいインデックス。デフォルトは0（次に再生されるアイテム）

        Returns
        -------
        :class:`wavelink.Playable`
            指定インデックスのトラック

        Raises
        ------
        QueueEmpty
            キューが空の場合に発生
        IndexError
            指定インデックスにトラックが存在しない場合に発生


        .. versionadded:: 3.2.0
        """
        if not self:
            raise QueueEmpty("There are no items currently in this queue.")

        return self[index]

    def swap(self, first: int, second: int, /) -> None:
        """指定インデックス同士のアイテムを入れ替えるメソッド

        Parameters
        ----------
        first: int
            入れ替え元のインデックス
        second: int
            入れ替え先のインデックス

        Returns
        -------
        None

        Raises
        ------
        IndexError
            指定インデックスにトラックが存在しない場合に発生

        Example
        -------
        .. code:: python3
            # 1番目と2番目のトラックを入れ替え
            queue.swap(0, 1)

        .. versionadded:: 3.2.0
        """
        self[first], self[second] = self[second], self[first]

    def index(self, item: Playable, /) -> int:
        """指定した :class:`wavelink.Playable` の最初の出現インデックスを返すメソッド

        Parameters
        ----------
        item: :class:`wavelink.Playable`
            検索対象のアイテム

        Returns
        -------
        int
            アイテムのインデックス

        Raises
        ------
        ValueError
            アイテムがキューに存在しない場合に発生

        .. versionadded:: 3.2.0
        """
        return self._items.index(item)

    def shuffle(self) -> None:
        """キューをインプレースでシャッフルするメソッド（戻り値なし）

        Example
        -------
        .. code:: python3
            player.queue.shuffle()
            # キューがシャッフルされる

        Returns
        -------
        None
        """

        random.shuffle(self._items)

    def clear(self) -> None:
        """キュー内の全アイテムを削除するメソッド

        .. note::
            このメソッドはキュー自体や履歴はリセットしない。履歴を消すには queue.history に対してこのメソッドを使う

        Example
        -------
        .. code:: python3
            player.queue.clear()
            # キューが空になる

        Returns
        -------
        None
        """

        self._items.clear()

    def copy(self) -> Queue:
        """キューのシャローコピーを作成するメソッド

        Returns
        -------
        :class:`wavelink.Queue`
            キューのシャローコピー
        """

        copy_queue = Queue(history=self.history is not None)
        copy_queue._items = self._items.copy()
        return copy_queue

    def reset(self) -> None:
        """キューをデフォルト状態にリセットするメソッド。キューと履歴をクリア

        .. note::
            このメソッドはキューの待機中Futureも全てキャンセルする（例: :meth:`wavelink.Queue.get_wait`）

        Returns
        -------
        None
        """
        self.clear()
        if self.history is not None:
            self.history.clear()

        for waiter in self._waiters:
            waiter.cancel()

        self._waiters.clear()

        self._mode: QueueMode = QueueMode.normal
        self._loaded = None

    def remove(self, item: Playable, /, count: int | None = 1) -> int:
        """指定したトラックを最大count回または全てキューから削除するメソッド

        .. note::
            このメソッドはキューの左端（先頭）から探索

        .. warning::
            countを ``<= 0`` にすると ``1`` と同等

        Parameters
        ----------
        item: :class:`wavelink.Playable`
            削除対象のアイテム
        count: int
            削除回数。デフォルトは1。Noneで全て削除

        Returns
        -------
        int
            削除された回数

        Raises
        ------
        ValueError
            アイテムがキューに存在しない場合に発生


        .. versionadded:: 3.2.0
        """
        deleted_count: int = 0

        for track in self._items.copy():
            if track == item:
                self._items.remove(track)
                deleted_count += 1

                if count is not None and deleted_count >= count:
                    break

        return deleted_count

    @property
    def loaded(self) -> Playable | None:
        """キューが :attr:`wavelink.QueueMode.loop` の場合にリピートされる現在ロード中のトラック

        ループモード時は :meth:`wavelink.Queue.get` でこのトラックが返される
        このプロパティを ``None`` にするか :meth:`wavelink.Player.skip`（force=True）でアンロード可能

        新しい :class:`wavelink.Playable` を設定すると現在のロードトラックが置き換わるが、再生されるまでキューや履歴には追加されない

        Returns
        -------
        :class:`wavelink.Playable` | None
            現在リピート対象のトラック。なければNone

        Raises
        ------
        TypeError
            :class:`wavelink.Playable` または ``None`` 以外を設定した場合に発生


        .. versionadded:: 3.2.0
        """
        return self._loaded

    @loaded.setter
    def loaded(self, value: Playable | None) -> None:
        if value is not None:
            self._check_compatibility(value)

        self._loaded = value
