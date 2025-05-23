import functools
import sys
from typing import Callable, Optional, TypeVar, Union, overload

from qtpy.QtWidgets import QApplication, QLabel

F = TypeVar("F", bound=Callable[[], None])


@overload
def entry_point(func: F) -> F: ...
@overload
def entry_point() -> Callable[[F], F]: ...


def entry_point(func: Optional[F] = None) -> Union[F, Callable[[F], F]]:
    def decorator(f: F) -> F:
        @functools.wraps(f)
        def wrapper() -> None:
            app = QApplication(sys.argv)
            f()
            app.exec_()

        return wrapper  # type: ignore[return-value]  # Because we're wrapping F but returning wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


@entry_point
def main():
    label = QLabel("Hello, World!")
    label.setWindowTitle("Simple App")
    label.setGeometry(100, 100, 200, 50)
    label.show()


if __name__ == "__main__":
    main()
