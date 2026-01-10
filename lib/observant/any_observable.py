"""Type alias for all observable types."""

from typing import Any

from .observable import Observable
from .observable_dict import ObservableDict
from .observable_list import ObservableList
from .observable_proxy import ObservableProxy
from .observable_set import ObservableSet

type AnyObservable[T] = Observable[T] | ObservableList[T] | ObservableDict[Any, T] | ObservableSet[T] | ObservableProxy[T]
