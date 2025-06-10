from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any


__all__ = (
    "Namespace",
    "ExtrasNamespace",
)


class Namespace(SimpleNamespace):
    def __iter__(self) -> Iterator[tuple[str, Any]]:
        return iter(self.__dict__.items())


class ExtrasNamespace(Namespace):
    """:class:`types.SimpleNameSpace` のサブクラス

    この名前空間は `str` キーと `Any` 値の :class:`dict`、キーワード引数、またはその両方で構築可能

    インスタンスに対して `dict()` を呼び出すことで辞書形式でアクセスできる

    Examples
    --------
        .. code:: python
            ns: ExtrasNamespace = ExtrasNamespace({"hello": "world!"}, stuff=1)

            print(ns.hello)
            print(ns.stuff)
            print(dict(ns))
    """

    def __init__(self, __dict: dict[str, Any] = {}, /, **kwargs: Any) -> None:
        updated = __dict | kwargs
        super().__init__(**updated)
