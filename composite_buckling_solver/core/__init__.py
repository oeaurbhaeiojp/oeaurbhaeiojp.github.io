"""Core classical-laminate-theory data models and stiffness computations."""

from .inputs import (
    LaminaProperties,
    Layup,
    Number,
    PlateGeometry,
)
from .laminate import (
    Classification,
    LaminateStiffness,
    classify_laminate,
    compute_ABD,
    reduced_stiffness_matrix,
    to_numpy,
    transformed_stiffness_matrix,
)

__all__ = [
    "LaminaProperties",
    "Layup",
    "Number",
    "PlateGeometry",
    "Classification",
    "LaminateStiffness",
    "classify_laminate",
    "compute_ABD",
    "reduced_stiffness_matrix",
    "transformed_stiffness_matrix",
    "to_numpy",
]
