"""Classical laminate theory: A, B, D stiffness matrices and classification.

This module implements the core of classical laminate theory (CLT):

1. The plane-stress *reduced* stiffness matrix ``Q`` of an orthotropic lamina
   in its principal material axes.
2. The *transformed* reduced stiffness ``Qbar`` of a ply rotated by an angle
   ``theta`` into the laminate (structural) axes.
3. The laminate extensional ``A``, coupling ``B`` and bending ``D`` stiffness
   matrices obtained by integrating ``Qbar`` through the thickness.
4. A *classification* routine that inspects the actual computed matrices (not
   the layup string) to label the laminate.

All quantities are built with ``sympy`` so that either numeric or symbolic
inputs flow through unchanged.  A helper is provided to convert a fully numeric
laminate's matrices to ``numpy`` arrays for convenient inspection.

Sign / coordinate conventions
------------------------------
* Ply angle ``theta`` is measured from the laminate ``x`` axis to the fibre
  ``1`` direction, positive counter-clockwise, in degrees on input.
* The engineering (Voigt) shear convention is used, so ``Q`` and ``Qbar`` are
  3x3 matrices acting on ``[eps_x, eps_y, gamma_xy]``.  This is the standard
  convention in Jones' *Mechanics of Composite Materials*.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Union

import numpy as np
import sympy as sp

from .inputs import LaminaProperties, Layup, Number


def reduced_stiffness_matrix(lamina: LaminaProperties) -> sp.Matrix:
    """Return the lamina plane-stress reduced stiffness matrix ``Q`` (3x3).

    For an orthotropic lamina under plane stress the reduced stiffnesses are

    ``Q11 = E1 / (1 - nu12 nu21)``
    ``Q22 = E2 / (1 - nu12 nu21)``
    ``Q12 = nu12 E2 / (1 - nu12 nu21)``
    ``Q66 = G12``

    with ``nu21 = nu12 E2 / E1``.  ``Q`` relates in-plane stress to in-plane
    strain in the *principal material* coordinate system.

    Parameters
    ----------
    lamina:
        The lamina elastic constants (float or symbolic).

    Returns
    -------
    sympy.Matrix
        The symmetric 3x3 ``Q`` matrix in the (1, 2, 6) Voigt ordering.
    """
    E1, E2, G12, nu12 = lamina.E1, lamina.E2, lamina.G12, lamina.nu12
    nu21 = lamina.nu21
    denom = 1 - nu12 * nu21

    Q11 = E1 / denom
    Q22 = E2 / denom
    Q12 = nu12 * E2 / denom
    Q66 = G12

    return sp.Matrix([[Q11, Q12, 0], [Q12, Q22, 0], [0, 0, Q66]])


def transformed_stiffness_matrix(Q: sp.Matrix, theta_deg: Number) -> sp.Matrix:
    """Transform ``Q`` from material axes to laminate axes (``Qbar``).

    Applies the standard tensor rotation for a ply oriented at ``theta_deg``
    (degrees) about the plate normal.  The result ``Qbar`` is the 3x3
    transformed reduced stiffness used directly in the CLT thickness integrals.

    The transformation uses ``Qbar = T^{-1} Q R T R^{-1}`` in Jones' notation;
    here it is implemented through the explicit invariant/trigonometric form,
    which is robust for both numeric and symbolic ``theta``.

    Parameters
    ----------
    Q:
        Lamina reduced stiffness in material axes (from
        :func:`reduced_stiffness_matrix`).
    theta_deg:
        Ply orientation in degrees (float or sympy symbol/expression).

    Returns
    -------
    sympy.Matrix
        The symmetric 3x3 transformed stiffness ``Qbar`` in laminate axes.
    """
    theta = theta_deg * sp.pi / 180
    c = sp.cos(theta)
    s = sp.sin(theta)

    Q11, Q12, Q22, Q66 = Q[0, 0], Q[0, 1], Q[1, 1], Q[2, 2]

    Qb11 = Q11 * c**4 + 2 * (Q12 + 2 * Q66) * s**2 * c**2 + Q22 * s**4
    Qb12 = (Q11 + Q22 - 4 * Q66) * s**2 * c**2 + Q12 * (c**4 + s**4)
    Qb22 = Q11 * s**4 + 2 * (Q12 + 2 * Q66) * s**2 * c**2 + Q22 * c**4
    Qb16 = (Q11 - Q12 - 2 * Q66) * s * c**3 + (Q12 - Q22 + 2 * Q66) * s**3 * c
    Qb26 = (Q11 - Q12 - 2 * Q66) * s**3 * c + (Q12 - Q22 + 2 * Q66) * s * c**3
    Qb66 = (Q11 + Q22 - 2 * Q12 - 2 * Q66) * s**2 * c**2 + Q66 * (s**4 + c**4)

    return sp.Matrix(
        [[Qb11, Qb12, Qb16], [Qb12, Qb22, Qb26], [Qb16, Qb26, Qb66]]
    )


@dataclass
class LaminateStiffness:
    """Container for the laminate ABD stiffness matrices and metadata.

    Attributes
    ----------
    A:
        Extensional stiffness matrix (3x3).  Relates in-plane forces to
        mid-plane strains.
    B:
        Bending-extension coupling matrix (3x3).  Couples in-plane forces to
        curvatures; vanishes for laminates symmetric about the mid-plane.
    D:
        Bending stiffness matrix (3x3).  Relates moments to curvatures and
        governs the plate buckling behaviour.
    Qbars:
        The per-ply transformed stiffness matrices (useful for inspection).
    """

    A: sp.Matrix
    B: sp.Matrix
    D: sp.Matrix
    Qbars: List[sp.Matrix]


def compute_ABD(
    lamina: LaminaProperties, layup: Layup
) -> LaminateStiffness:
    """Compute the laminate ``A``, ``B`` and ``D`` matrices from CLT.

    The classical laminate theory definitions are

    ``A_ij = sum_k Qbar_ij^(k) (z_k - z_{k-1})``
    ``B_ij = (1/2) sum_k Qbar_ij^(k) (z_k^2 - z_{k-1}^2)``
    ``D_ij = (1/3) sum_k Qbar_ij^(k) (z_k^3 - z_{k-1}^3)``

    where ``z_k`` are the ply interface coordinates measured from the laminate
    mid-plane.  These are obtained by integrating the per-ply ``Qbar`` over the
    ply thickness in ``z^0``, ``z^1`` and ``z^2`` respectively.

    Parameters
    ----------
    lamina:
        Lamina elastic constants (assumed identical for every ply, the usual
        single-material idealisation).
    layup:
        The stacking sequence and ply thickness.

    Returns
    -------
    LaminateStiffness
        The ``A``, ``B``, ``D`` matrices plus the per-ply ``Qbar`` matrices.
        Everything is symbolic (``sympy.Matrix``); fully numeric inputs yield
        matrices that evaluate to numbers.
    """
    Q = reduced_stiffness_matrix(lamina)
    z = layup.z_coordinates()

    A = sp.zeros(3, 3)
    B = sp.zeros(3, 3)
    D = sp.zeros(3, 3)
    qbars: List[sp.Matrix] = []

    for k, theta in enumerate(layup.angles):
        Qbar = transformed_stiffness_matrix(Q, theta)
        qbars.append(Qbar)
        zk = z[k + 1]
        zkm1 = z[k]
        A += Qbar * (zk - zkm1)
        B += Qbar * (zk**2 - zkm1**2) / 2
        D += Qbar * (zk**3 - zkm1**3) / 3

    return LaminateStiffness(
        A=_finalize(A), B=_finalize(B), D=_finalize(D), Qbars=qbars
    )


def _finalize(matrix: sp.Matrix) -> sp.Matrix:
    """Tidy an assembled stiffness matrix for fast, clean downstream use.

    The per-ply ``Qbar`` integrals carry symbolic trigonometry (``cos(pi/4)``
    etc.) even when every input is numeric, because the ply angle is multiplied
    by the exact symbol ``pi``.  Running ``sympy.simplify`` on those mixed
    trig expressions is correct but extremely slow (seconds per laminate), so:

    * if the matrix has **no free symbols** (a fully numeric laminate, the
      common case) it is collapsed to floating point with ``evalf(chop=True)``,
      which is exact-enough and orders of magnitude faster; tiny rounding
      residuals (e.g. ``cos(pi/2)``) are chopped to zero, and
    * if the matrix is **genuinely symbolic** (e.g. a symbolic ply angle or
      modulus) it is simplified so the result stays readable.

    Note: symbolic *ply-angle* sweeps remain expensive; prefer evaluating those
    numerically at each angle.
    """
    if matrix.free_symbols:
        return sp.simplify(matrix)
    return matrix.evalf(chop=True)


def _is_negligible(matrix: sp.Matrix, tol: float = 1e-6) -> bool:
    """Return ``True`` if every entry of ``matrix`` is (approximately) zero.

    For symbolic entries the test is exact symbolic simplification to zero; for
    numeric entries the absolute value is compared against ``tol``.  The two
    are mixed gracefully: a symbolic-but-constant entry is evaluated.
    """
    for entry in matrix:
        simplified = sp.simplify(entry)
        if simplified.free_symbols:
            # Genuinely symbolic and not identically zero -> not negligible.
            if simplified != 0:
                return False
        else:
            if abs(float(simplified)) > tol:
                return False
    return True


def _is_negligible_entries(
    entries: List[sp.Expr], tol: float = 1e-6
) -> bool:
    """Same negligibility test as :func:`_is_negligible` for a list of scalars."""
    for entry in entries:
        simplified = sp.simplify(entry)
        if simplified.free_symbols:
            if simplified != 0:
                return False
        else:
            if abs(float(simplified)) > tol:
                return False
    return True


@dataclass
class Classification:
    """Result of inspecting the ABD matrices to label the laminate.

    Attributes
    ----------
    is_symmetric:
        ``True`` when the coupling matrix ``B`` is (approximately) zero, i.e.
        there is no bending-extension coupling.  This is the property that lets
        the buckling equation drop the ``B`` terms.
    is_balanced:
        ``True`` when ``A16 = A26 = 0`` (no extension-shear coupling), the
        defining property of a *balanced* laminate.
    is_specially_orthotropic:
        ``True`` when, in addition to symmetry, the bending twist coupling
        terms vanish (``D16 = D26 = 0``).  This is the condition under which the
        closed-form Navier buckling solution implemented in ``solver`` is
        exact.
    layup_family:
        A coarse human-readable family label inferred from the angle set
        (``"cross-ply"``, ``"angle-ply"``, ``"quasi-isotropic/general"`` ...).
        This is descriptive only; the *mechanical* decisions in the solver use
        the boolean flags above, which come from the matrices themselves.
    labels:
        A list of all applicable descriptive labels, for printing.
    """

    is_symmetric: bool
    is_balanced: bool
    is_specially_orthotropic: bool
    layup_family: str
    labels: List[str]


def _layup_family(angles: List[Number]) -> str:
    """Best-effort descriptive family from the angle multiset.

    Purely informational.  Only inspects angles that are concrete numbers; if
    angles are symbolic the family is reported as ``"parametric"``.
    """
    numeric_angles = []
    for a in angles:
        expr = sp.sympify(a)
        if expr.free_symbols:
            return "parametric"
        numeric_angles.append(float(expr) % 180.0)

    unique = set(round(a, 6) for a in numeric_angles)
    only_0_90 = unique <= {0.0, 90.0}
    if only_0_90 and len(unique) > 0:
        return "cross-ply"

    # angle-ply: composed of +theta / -theta pairs (theta not 0 or 90)
    signed = set(round(a % 180.0, 6) for a in (float(sp.sympify(x)) for x in angles))
    has_pos_neg = any(
        round((a) % 180.0, 6) != 0.0 and round((a) % 180.0, 6) != 90.0
        for a in numeric_angles
    )
    if has_pos_neg and unique <= {
        round(v % 180.0, 6) for v in numeric_angles
    }:
        # crude: if every off-axis angle has a sign-mate it's angle-ply
        base = set(abs(((a + 90) % 180) - 90) for a in numeric_angles)
        if len(base) <= 2:
            return "angle-ply"

    return "quasi-isotropic/general"


def classify_laminate(
    stiffness: LaminateStiffness, layup: Layup
) -> Classification:
    """Classify a laminate from its *computed* ABD matrices.

    The classification is matrix-driven, as required: symmetry is decided by
    testing whether ``B`` is negligible, balance by testing ``A16``/``A26``,
    and special-orthotropy by testing the bending-twist terms ``D16``/``D26``.
    This keeps the labels correct for arbitrary stacking sequences instead of
    pattern-matching the layup string.

    Parameters
    ----------
    stiffness:
        The computed ABD matrices.
    layup:
        The stacking sequence (used only for the descriptive family label).

    Returns
    -------
    Classification
        The boolean flags, a descriptive family, and a list of labels.
    """
    is_symmetric = _is_negligible(stiffness.B)
    is_balanced = _is_negligible_entries(
        [stiffness.A[0, 2], stiffness.A[1, 2]]
    )
    bending_twist_zero = _is_negligible_entries(
        [stiffness.D[0, 2], stiffness.D[1, 2]]
    )
    is_specially_orthotropic = is_symmetric and bending_twist_zero

    family = _layup_family(layup.angles)

    labels: List[str] = []
    labels.append("symmetric" if is_symmetric else "unsymmetric")
    if is_balanced:
        labels.append("balanced")
    if is_specially_orthotropic:
        labels.append("specially orthotropic (D16=D26=0)")
    elif is_symmetric:
        labels.append("symmetric with bend-twist coupling (D16,D26 != 0)")
    labels.append(family)

    return Classification(
        is_symmetric=is_symmetric,
        is_balanced=is_balanced,
        is_specially_orthotropic=is_specially_orthotropic,
        layup_family=family,
        labels=labels,
    )


def to_numpy(matrix: sp.Matrix) -> np.ndarray:
    """Convert a fully numeric ``sympy.Matrix`` to a float ``numpy.ndarray``.

    Raises a clear error if the matrix still contains free symbols, since that
    cannot be represented as a float array.

    Parameters
    ----------
    matrix:
        A 3x3 (or any) sympy matrix with no free symbols.

    Returns
    -------
    numpy.ndarray
        The same matrix as a ``float`` numpy array.
    """
    if matrix.free_symbols:
        raise ValueError(
            "Matrix still contains free symbols; cannot convert to numpy: "
            f"{matrix.free_symbols}"
        )
    return np.array(matrix.evalf().tolist(), dtype=float)
