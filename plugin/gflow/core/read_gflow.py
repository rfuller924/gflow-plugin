from typing import NamedTuple
import numpy as np


class SurferGrid(NamedTuple):
    data: np.ndarray
    xmin: float
    xmax: float
    ymin: float
    ymax: float


def read_surfer_grid(path: str) -> SurferGrid:
    with open(path) as f:
        f.readline()  # skip header
        ncol, nrow = map(int, f.readline().strip().split())
        xmin, xmax = map(float, f.readline().strip().split())
        ymin, ymax = map(float, f.readline().strip().split())
        f.readine().strip()  # skip zmin, zmax
        data = np.fromfile(f, dtype=float, sep=" ", count=ncol * nrow)
    return SurferGrid(
        data=data.reshape((nrow, ncol)),
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
    )  
