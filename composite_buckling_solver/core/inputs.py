"""Input data models for the composite plate buckling solver.

This module defines the data structures used to describe a laminate:

* the *lamina* (single ply) elastic properties expressed in the material
  (principal) coordinate system, and
* the *layup* (stacking sequence) together with the ply thickness.

Every numeric field is annotated with the alias :data:`Number`, which is the
union of a Python ``float`` (and ``int``) and a ``sympy`` symbolic expression.
This is the key design decision that lets *one* data model drive both
workflows required by the task:

* a **numeric** workflow, where ``E1 = 138e9`` (Pa) etc. and the laminate
  stiffness matrices come out as floating point numbers, and
* a **symbolic / parametric** workflow, where e.g. ``E1 = sympy.Symbol('E1')``
  or a ply angle is a free symbol, so the resulting ``A``, ``B``, ``D`` and the
  critical buckling load ``P_cr`` are returned as symbolic expressions suitable
  for parametric studies.

No mechanics is performed here; this module is purely the *ingestion* layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence, Union

import sympy as sp

# A field may be a concrete number (float/int) or a symbolic sympy object.
# ``sp.Expr`` covers Symbol, Float, Mul, Add, ... so a single alias suffices.
Number = Union[float, int, sp.Expr]


@dataclass
class LaminaProperties:
    """Orthotropic elastic constants of a single lamina (ply).

    The constants are defined in the lamina *principal material* coordinate
    system, where direction ``1`` is along the fibres and direction ``2`` is
    transverse to the fibres (in the plane of the ply).  These four
    independent constants fully define the in-plane behaviour of a transversely
    isotropic / orthotropic lamina under plane-stress, which is the standard
    assumption of classical laminate theory (CLT).

    Attributes
    ----------
    E1:
        Longitudinal Young's modulus (fibre direction), consistent units (Pa).
    E2:
        Transverse Young's modulus (in-plane, perpendicular to fibres).
    G12:
        In-plane shear modulus.
    nu12:
        Major Poisson's ratio (``-eps2/eps1`` under uniaxial stress in dir 1).
        The minor ratio ``nu21`` is *not* independent; it follows from the
        reciprocity relation ``nu21 = nu12 * E2 / E1`` and is provided as a
        convenience property.

    Notes
    -----
    Any attribute may be a ``float`` or a ``sympy.Symbol`` / expression, which
    is what enables symbolic parametric studies through the same code path.
    """

    E1: Number
    E2: Number
    G12: Number
    nu12: Number

    @property
    def nu21(self) -> Number:
        """Minor Poisson's ratio from the orthotropic reciprocity relation.

        ``nu21 = nu12 * E2 / E1``.  Returned in whatever domain the inputs
        live in (float or symbolic).
        """
        return self.nu12 * self.E2 / self.E1


@dataclass
class Layup:
    """A laminate stacking sequence and its (per-ply) thickness.

    Parameters
    ----------
    angles:
        Ordered list of ply orientations in **degrees**, listed from one face
        of the laminate to the other.  Example: ``[0, 90, 0]`` is a 3-ply
        cross-ply, ``[45, -45]`` is a 2-ply angle-ply.  Angles may be floats
        or sympy symbols (e.g. ``theta`` for a parametric angle sweep).
    ply_thickness:
        Thickness of a single ply (consistent length units, e.g. metres).
        Assumed identical for every ply, which is the usual textbook
        idealisation.  May be float or symbolic.

    Notes
    -----
    Use :meth:`from_symmetric` to expand a half-stack written with the ``s``
    (symmetric) shorthand, e.g. ``[45, -45]s`` -> ``[45, -45, -45, 45]``.
    """

    angles: List[Number]
    ply_thickness: Number

    @property
    def n_plies(self) -> int:
        """Number of plies in the (fully expanded) stacking sequence."""
        return len(self.angles)

    @property
    def total_thickness(self) -> Number:
        """Total laminate thickness ``h = n_plies * ply_thickness``."""
        return self.n_plies * self.ply_thickness

    def z_coordinates(self) -> List[Number]:
        """Ply interface ``z`` coordinates measured from the laminate midplane.

        Returns ``n_plies + 1`` values ``[z0, z1, ..., zN]`` where ``z0`` is the
        bottom face at ``-h/2`` and ``zN`` is the top face at ``+h/2``.  These
        are the ``z_k`` used in the CLT integrals for the ``A``, ``B`` and ``D``
        matrices (which integrate ``Qbar`` over ``z^0``, ``z^1`` and ``z^2``).
        """
        h = self.total_thickness
        z0 = -h / 2
        return [z0 + k * self.ply_thickness for k in range(self.n_plies + 1)]

    @classmethod
    def from_symmetric(
        cls, half_angles: Sequence[Number], ply_thickness: Number
    ) -> "Layup":
        """Build a symmetric laminate from its half-stack.

        Mirrors ``half_angles`` about the midplane, reproducing the common
        ``[...]s`` notation.  For example ``from_symmetric([45, -45], t)``
        yields the stack ``[45, -45, -45, 45]``.

        Parameters
        ----------
        half_angles:
            The stacking sequence of the lower half of the laminate.
        ply_thickness:
            Single-ply thickness.
        """
        seq = list(half_angles) + list(reversed(half_angles))
        return cls(angles=seq, ply_thickness=ply_thickness)


@dataclass
class PlateGeometry:
    """In-plane dimensions of a rectangular plate.

    Attributes
    ----------
    a:
        Plate length along the ``x`` axis (loaded edge direction for uniaxial
        compression in the test cases).
    b:
        Plate width along the ``y`` axis.

    Both may be floats or symbolic; the aspect ratio ``a/b`` is a natural
    parameter for the parametric buckling study.
    """

    a: Number
    b: Number

    @property
    def aspect_ratio(self) -> Number:
        """Plate aspect ratio ``a / b``."""
        return self.a / self.b
