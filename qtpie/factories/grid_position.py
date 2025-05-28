from dataclasses import dataclass


@dataclass(frozen=True)
class GridPosition:
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
