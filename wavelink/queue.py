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
        self._items: list[Playable | Playlist] = []

        self._history: Queue | None = Queue(history=False) if history else None
        self._mode: QueueMode = QueueMode.normal
        self._loaded: Playable | None = None
        
        self._loop_playlist_cache: Playlist | None = None

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

    @property
    def groups(self) -> list[Playable | Playlist]:
        """キューの内容のリストを返すプロパティ

        Returns
        -------
        list[:class:`wavelink.Playable` | :class:`wavelink.Playlist`]

        .. versionadded:: 3.5.0
        """
        return self._items.copy()

    def __call__(self, item: Playable) -> None:
        self.put(item)

    def __bool__(self) -> bool:
        return bool(self._items)

    @overload
    def __getitem__(self, __index: SupportsIndex, /) -> Playable: ...

    @overload
    def __getitem__(self, __index: slice, /) -> list[Playable]: ...

    def __getitem__(self, __index: SupportsIndex | slice, /) -> Playable | list[Playable]:
        if isinstance(__index, slice):
            return list(self)[__index]

        target: int = __index.__index__()
        if target < 0:
            target += len(self)

        current_len = 0
        for item in self._items:
            if isinstance(item, Playlist):
                tracks = item.tracks
                plen = len(tracks)
                if current_len <= target < current_len + plen:
                    return tracks[target - current_len]
                current_len += plen
            else:
                if current_len == target:
                    return item
                current_len += 1

        raise IndexError("queue index out of range")

    def __setitem__(self, __index: SupportsIndex, __value: Playable, /) -> None:
        self._check_compatibility(__value, include_playlist=False)
        
        # Determine the real index in _items by simulating flat indexing
        target: int = __index.__index__()
        if target < 0:
            target += len(self)
        
        if target < 0 or target >= len(self):
            raise IndexError("queue assignment index out of range")
            
        current_len = 0
        for i, item in enumerate(self._items):
            if isinstance(item, Playlist):
                if current_len <= target < current_len + len(item.tracks):
                    item.tracks[target - current_len] = __value
                    break
                current_len += len(item.tracks)
            else:
                if current_len == target:
                    self._items[i] = __value
                    break
                current_len += 1

        self._wakeup_next()

    def __delitem__(self, __index: int | slice, /) -> None:
        if isinstance(__index, slice):
            start, stop, step = __index.indices(len(self))
            for idx in sorted(range(start, stop, step), reverse=True):
                self.__delitem__(idx)
            return

        target: int = __index
        if target < 0:
            target += len(self)
            
        if target < 0 or target >= len(self):
            raise IndexError("queue assignment index out of range")
            
        current_len = 0
        for i, item in enumerate(self._items):
            if isinstance(item, Playlist):
                if current_len <= target < current_len + len(item.tracks):
                    del item.tracks[target - current_len]
                    if not item.tracks:
                        del self._items[i]
                    break
                current_len += len(item.tracks)
            else:
                if current_len == target:
                    del self._items[i]
                    break
                current_len += 1

    def __contains__(self, __other: Playable | Playlist) -> bool:
        if isinstance(__other, Playlist):
            return __other in self._items
        return __other in iter(self)

    def __len__(self) -> int:
        return sum(len(item.tracks) if isinstance(item, Playlist) else 1 for item in self._items)

    def __reversed__(self) -> Iterator[Playable]:
        for item in reversed(self._items):
            if isinstance(item, Playlist):
                yield from reversed(item.tracks)
            else:
                yield item

    def __iter__(self) -> Iterator[Playable]:
        for item in self._items:
            if isinstance(item, Playlist):
                yield from item.tracks
            else:
                yield item

    def _wakeup_next(self) -> None:
        while self._waiters:
            waiter = self._waiters.popleft()

            if not waiter.done():
                waiter.set_result(None)
                break
    
    @property
    def length(self) -> int:
        """キューの合計時間（ミリ秒）を返すプロパティ

        Returns
        -------
        int
            キューの合計時間
        """
        return sum(track.length for track in self)
    
    @property
    def length_sec(self) -> float:
        """キューの合計時間（秒）を返すプロパティ

        Returns
        -------
        float
            キューの合計時間
        """
        return sum(track.length_sec for track in self)
    
    @property
    def length_min(self) -> float:
        """キューの合計時間（分）を返すプロパティ

        Returns
        -------
        float
            キューの合計時間
        """
        return sum(track.length_min for track in self)
    
    @property
    def length_hour(self) -> float:
        """キューの合計時間（時間）を返すプロパティ

        Returns
        -------
        float
            キューの合計時間
        """
        return sum(track.length_hour for track in self)
    
    @property
    def length_formatted(self) -> str:
        """キューの合計時間（HH:MM:SS形式）を返すプロパティ

        Returns
        -------
        str
            キューの合計時間
        """
        total_seconds = int(self.length / 1000)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    @staticmethod
    def _check_compatibility(item: object, *, include_playlist: bool = True) -> TypeGuard[Playable | Playlist]:
        if include_playlist and isinstance(item, Playlist):
            return True
        if not isinstance(item, Playable):
            allow_msg = "Playable or Playlist objects" if include_playlist else "Playable objects"
            raise TypeError(f"This queue is restricted to {allow_msg}.")
        return True

    @classmethod
    def _check_atomic(cls, item: Iterable[object]) -> TypeGuard[Iterable[Playable]]:
        for track in item:
            cls._check_compatibility(track, include_playlist=False)
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

        if self.mode is not QueueMode.loop_playlist:
            self._loop_playlist_cache = None

        if not self:
            raise QueueEmpty("There are no items currently in this queue.")

        first_item = self._items[0]
        track: Playable
        if isinstance(first_item, Playlist):
            if self.mode is QueueMode.loop_playlist and self._loop_playlist_cache is None:
                self._loop_playlist_cache = Playlist(data=first_item._data)
                
                if hasattr(first_item, "_extras"):
                    self._loop_playlist_cache.extras = first_item._extras
                    
                standard_attrs = set(dir(Playable))
                
                for orig_t, cache_t in zip(first_item.tracks, self._loop_playlist_cache.tracks):
                    cache_t.extras = orig_t.extras
                    
                    custom_attrs = {
                        k: getattr(orig_t, k) 
                        for k in dir(orig_t) 
                        if k not in standard_attrs and not k.startswith('_')
                    }
                    for k, v in custom_attrs.items():
                        setattr(cache_t, k, v)
                
            track = first_item.tracks.pop(0)
            if not first_item.tracks:
                self._items.pop(0)
                
                if self.mode is QueueMode.loop_playlist and self._loop_playlist_cache:
                    cached_pl = self._loop_playlist_cache
                    restored_pl = Playlist(data=cached_pl._data)
                    
                    if hasattr(cached_pl, "_extras"):
                        restored_pl.extras = cached_pl._extras
                        
                    standard_attrs = set(dir(Playable))
                    
                    for cache_t, restored_t in zip(cached_pl.tracks, restored_pl.tracks):
                        restored_t.extras = cache_t.extras
                        
                        custom_attrs = {
                            k: getattr(cache_t, k) 
                            for k in dir(cache_t) 
                            if k not in standard_attrs and not k.startswith('_')
                        }
                        for k, v in custom_attrs.items():
                            setattr(restored_t, k, v)

                    self._items.insert(0, restored_pl)
        else:
            # We know it's not a Playlist here, but pyright can't infer it perfectly from _items.pop(0)
            track = self._items.pop(0) # type: ignore

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

        target: int = index
        if target < 0:
            target += len(self)
            
        if target < 0 or target >= len(self):
            raise IndexError("queue getting index out of range")
            
        current_len = 0
        track: Playable | None = None
        for i, item in enumerate(self._items):
            if isinstance(item, Playlist):
                if current_len <= target < current_len + len(item.tracks):
                    track = item.tracks.pop(target - current_len)
                    if not item.tracks:
                        self._items.pop(i)
                    break
                current_len += len(item.tracks)
            else:
                if current_len == target:
                    # Type ignore needed here as _items.pop returns Playable | Playlist, but we know it's a Playable
                    track = self._items.pop(i) # type: ignore
                    break
                current_len += 1

        assert track is not None

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
        self._check_compatibility(value, include_playlist=False)
        target: int = index
        if target < 0:
            target += len(self)
        
        target = max(0, min(target, len(self)))
        if target == len(self):
            self._items.append(value)
        else:
            current_len = 0
            for i, item in enumerate(self._items):
                if isinstance(item, Playlist):
                    if current_len <= target < current_len + len(item.tracks):
                        item.tracks.insert(target - current_len, value)
                        break
                    current_len += len(item.tracks)
                else:
                    if current_len == target:
                        self._items.insert(i, value)
                        break
                    current_len += 1
        
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

        if isinstance(item, Iterable) and not isinstance(item, Playlist):
            if atomic:
                items: list[Playable] = list(item)
                self._check_atomic(items)
                self._items.extend(items)
                added = len(items)
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
            added = len(item.tracks) if isinstance(item, Playlist) else 1

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
            if isinstance(item, Iterable) and not isinstance(item, Playlist):
                if atomic:
                    items: list[Playable] = list(item)
                    self._check_atomic(items)
                    self._items.extend(items)
                    self._wakeup_next()
                    return len(items)

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
                added += len(item.tracks) if isinstance(item, Playlist) else 1
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

        del self[index]

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
        try:
            return list(self).index(item)
        except ValueError:
            raise ValueError(f"{item!r} is not in queue")

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
        self._loop_playlist_cache = None

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
        self._loop_playlist_cache = None

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

        for i in range(len(self) - 1, -1, -1):
            if self[i] == item:
                del self[i]
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
