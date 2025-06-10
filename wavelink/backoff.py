from __future__ import annotations

import random
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable


class Backoff:
    """指数バックオフの実装。

    Parameters
    ----------
    base: int
        指数的に乗算される基準時間。デフォルトは1。
    maximum_time: float
        最大待機時間。デフォルトは30.0。
    maximum_tries: Optional[int]
        リセットするまでのバックオフ回数。デフォルトは5。Noneに設定すると無制限にバックオフします。
    """

    def __init__(self, *, base: int = 1, maximum_time: float = 30.0, maximum_tries: int | None = 5) -> None:
        self._base: int = base
        self._maximum_time: float = maximum_time
        self._maximum_tries: int | None = maximum_tries
        self._retries: int = 1

        rand = random.Random()
        rand.seed()

        self._rand: Callable[[float, float], float] = rand.uniform

        self._last_wait: float = 0

    def calculate(self) -> float:
        exponent = min((self._retries**2), self._maximum_time)
        wait = self._rand(0, (self._base * 2) * exponent)

        if wait <= self._last_wait:
            wait = self._last_wait * 2

        self._last_wait = wait

        if wait > self._maximum_time:
            wait = self._maximum_time
            self._retries = 0
            self._last_wait = 0

        if self._maximum_tries and self._retries >= self._maximum_tries:
            self._retries = 0
            self._last_wait = 0

        self._retries += 1

        return wait
    
    def reset(self) -> None:
        self._retries = 1
        self._last_wait = 0