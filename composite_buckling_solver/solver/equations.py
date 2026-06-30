"""Symbolic buckling governing equation and Navier P_cr solution.

============================================================================
ASSUMPTIONS AND BOUNDARY CONDITIONS (read before trusting any result here)
============================================================================
The closed-form critical buckling load implemented in this module is derived
under the following explicit, standard classical-laminate-plate-buckling
assumptions.  They were *chosen* here (the task did not fully specify them) and
are flagged so they can be checked against the source theory:

1.  GEOMETRY / KINEMATICS
    * Thin rectangular plate, dimensions ``a`` (x) by ``b`` (y).
    * Kirchhoff-Love (classical) plate theory: transverse shear neglected.

2.  LOADING
    * In-plane UNIAXIAL compression: a uniform compressive force per unit
      length ``N_x`` applied on the edges normal to ``x``.  ``N_y = N_xy = 0``.
    * ``N_x`` is taken positive in compression.  Buckling occurs at the lowest
      ``N_x`` for which a non-trivial out-of-plane deflection exists.

3.  BOUNDARY CONDITIONS
    * SIMPLY SUPPORTED on all four edges (SSSS): ``w = 0`` and zero bending
      moment on every edge.  This is exactly the case for which the
      double-sine (Navier) series is the exact eigenfunction.

4.  LAMINATE TYPE for the EXACT closed form
    * SYMMETRIC laminate (B = 0, so in-plane and bending decouple) AND
    * SPECIALLY ORTHOTROPIC bending (D16 = D26 = 0), so the buckling mode is a
      single separable sine term and the eigenvalue is available in closed
      form.  Under these two conditions the Navier solution below is EXACT.

5.  HANDLING OF LAMINATES THAT VIOLATE (4)
    * If B != 0 (unsymmetric), the bending and stretching problems are coupled.
      We apply the well-known *reduced bending stiffness* approximation
      ``D* = D - B A^{-1} B`` and use ``D*`` in place of ``D``.  This is an
      APPROXIMATION (it is exact only in special cases) and is reported as such.
    * If D16, D26 are not negligible (symmetric but not specially orthotropic),
      the single-term Navier solution is APPROXIMATE; the bend-twist terms are
      neglected in the closed form and this is reported.

Governing equation (specially orthotropic plate, out-of-plane equilibrium):

    D11 w,xxxx + 4 D16 w,xxxy + 2(D12 + 2 D66) w,xxyy
        + 4 D26 w,xyyy + D22 w,yyyy + N_x w,xx = 0

With the SSSS Navier mode ``w = sin(m*pi*x/a) sin(n*pi*y/b)`` and the special
orthotropy simplification (D16 = D26 = 0), substitution gives the eigenvalue

    N_x(m,n) = pi^2 * [ D11 (m/a)^4 + 2(D12+2D66)(m/a)^2 (n/b)^2
                        + D22 (n/b)^4 ] / (m/a)^2

and the critical load is ``P_cr = min over (m,n) of N_x(m,n)`` (usually n = 1).
============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union

import sympy as sp

from core.inputs import Number, PlateGeometry
from core.laminate import Classification, LaminateStiffness


# ---------------------------------------------------------------------------
# Symbolic symbols used to write the governing equation in a readable form.
# ---------------------------------------------------------------------------
x, y = sp.symbols("x y", real=True)
a_sym, b_sym = sp.symbols("a b", positive=True)
m_sym, n_sym = sp.symbols("m n", positive=True, integer=True)
Nx_sym = sp.symbols("N_x", real=True)
D11, D12, D16, D22, D26, D66 = sp.symbols(
    "D11 D12 D16 D22 D26 D66", real=True
)


def governing_equation(w: sp.Function) -> sp.Expr:
    """Return the symbolic buckling governing PDE residual for ``w(x, y)``.

    Implements the classical (Kirchhoff) out-of-plane equilibrium equation for
    a symmetric laminate under uniaxial compression ``N_x`` (see the module
    docstring for the full assumption list)::

        D11 w,xxxx + 4 D16 w,xxxy + 2(D12+2D66) w,xxyy
            + 4 D26 w,xyyy + D22 w,yyyy + N_x w,xx = 0

    The bend-twist terms ``D16`` and ``D26`` are retained here so that the
    simplification step in :func:`simplify_for_classification` can be seen to
    drop them for a specially orthotropic laminate.

    Parameters
    ----------
    w:
        A sympy function ``w(x, y)`` representing the plate deflection.

    Returns
    -------
    sympy.Expr
        The left-hand side of the governing equation (equals zero at buckling).
    """
    wf = w(x, y)
    return (
        D11 * wf.diff(x, 4)
        + 4 * D16 * wf.diff(x, 3, y, 1)
        + 2 * (D12 + 2 * D66) * wf.diff(x, 2, y, 2)
        + 4 * D26 * wf.diff(x, 1, y, 3)
        + D22 * wf.diff(y, 4)
        + Nx_sym * wf.diff(x, 2)
    )


def simplify_for_classification(
    classification: Classification,
) -> sp.Expr:
    """Specialise the governing PDE according to the laminate classification.

    This is the "logic that simplifies the general symbolic equation based on
    the classification" required by the task.  Concretely:

    * For a **specially orthotropic** laminate (``D16 = D26 = 0``) the
      bend-twist derivative terms are removed, yielding the classic separable
      orthotropic plate buckling operator.
    * Otherwise the full operator (including ``D16``/``D26``) is returned, and
      the caller is expected to treat the Navier result as approximate.

    Parameters
    ----------
    classification:
        The matrix-driven classification from ``core.laminate``.

    Returns
    -------
    sympy.Expr
        The (possibly simplified) governing-equation residual, with the same
        symbolic ``w`` derivatives represented via an undefined function.
    """
    w = sp.Function("w")
    expr = governing_equation(w)

    if classification.is_specially_orthotropic:
        expr = expr.subs({D16: 0, D26: 0})
    return sp.simplify(expr)


def navier_Nx_expression() -> sp.Expr:
    """Return the symbolic uniaxial buckling load ``N_x(m, n)`` (SSSS plate).

    Derived by substituting the Navier mode
    ``w = sin(m*pi*x/a) sin(n*pi*y/b)`` into the specially orthotropic
    governing equation (see module docstring).  The returned expression is in
    terms of the symbols ``D11, D12, D22, D66, a, b, m, n``::

        N_x(m,n) = pi^2 [ D11 (m/a)^4 + 2(D12+2D66)(m/a)^2 (n/b)^2
                          + D22 (n/b)^4 ] / (m/a)^2

    Returns
    -------
    sympy.Expr
        The buckling load per unit length as a function of the mode numbers.
    """
    alpha = m_sym * sp.pi / a_sym
    beta = n_sym * sp.pi / b_sym
    numerator = (
        D11 * alpha**4
        + 2 * (D12 + 2 * D66) * alpha**2 * beta**2
        + D22 * beta**4
    )
    return sp.simplify(numerator / alpha**2)


def _reduced_bending_stiffness(
    stiffness: LaminateStiffness,
) -> sp.Matrix:
    """Return ``D* = D - B A^{-1} B`` (reduced bending stiffness, unsym. case).

    This standard approximation lets an unsymmetric laminate be analysed with
    the symmetric-laminate buckling formula by absorbing the membrane-bending
    coupling into an effective bending stiffness.  It is exact only in limited
    cases and is therefore reported as an approximation by the caller.
    """
    A = stiffness.A
    B = stiffness.B
    D = stiffness.D
    return sp.simplify(D - B * A.inv() * B)


@dataclass
class BucklingResult:
    """Outcome of a buckling computation.

    Attributes
    ----------
    Nx_cr:
        Critical buckling load per unit length ``N_x`` (force/length).  Symbolic
        or numeric depending on the inputs.
    P_cr_total:
        Total critical compressive force ``N_x_cr * b`` across the loaded edge.
    mode:
        ``(m, n)`` half-wave numbers at which the minimum occurred, or ``None``
        when the result is left symbolic (parametric study).
    Nx_symbolic:
        The symbolic ``N_x(m, n)`` expression actually used (after substituting
        the laminate's effective D values), for inspection / plotting.
    assumptions:
        Human-readable notes about approximations applied (e.g. reduced bending
        stiffness for an unsymmetric laminate).
    """

    Nx_cr: Number
    P_cr_total: Number
    mode: Optional[Tuple[int, int]]
    Nx_symbolic: sp.Expr
    assumptions: list


def _effective_D_values(
    stiffness: LaminateStiffness, classification: Classification
) -> Tuple[Dict[sp.Symbol, sp.Expr], list]:
    """Pick the D entries to substitute and note any approximation.

    Returns a substitution dict for ``D11, D12, D22, D66`` (the only ones that
    enter the specially orthotropic Navier formula) plus a list of assumption
    strings describing what was done.
    """
    assumptions: list = []
    if classification.is_symmetric:
        D = stiffness.D
    else:
        D = _reduced_bending_stiffness(stiffness)
        assumptions.append(
            "Unsymmetric laminate (B != 0): used reduced bending stiffness "
            "D* = D - B A^{-1} B as an approximation."
        )

    if not classification.is_specially_orthotropic:
        assumptions.append(
            "D16/D26 not negligible: single-term Navier solution is "
            "approximate (bend-twist coupling neglected)."
        )

    subs = {
        D11: D[0, 0],
        D12: D[0, 1],
        D22: D[1, 1],
        D66: D[2, 2],
    }
    return subs, assumptions


def solve_Pcr_numeric(
    stiffness: LaminateStiffness,
    classification: Classification,
    geometry: PlateGeometry,
    m_max: int = 4,
    n_max: int = 4,
) -> BucklingResult:
    """Compute the numeric critical buckling load by minimising over modes.

    Substitutes the laminate's (effective) ``D`` values and the plate geometry
    into the Navier expression, evaluates ``N_x(m, n)`` over a grid of half-wave
    numbers ``1..m_max`` x ``1..n_max`` and returns the minimum (the physical
    buckling load).

    Parameters
    ----------
    stiffness:
        Computed ABD matrices (must be fully numeric).
    classification:
        Matrix-driven classification controlling which D values are used.
    geometry:
        Plate dimensions (must be fully numeric).
    m_max, n_max:
        Largest half-wave numbers to search in ``x`` and ``y``.

    Returns
    -------
    BucklingResult
        The critical load, total load, governing mode and assumptions.
    """
    subs, assumptions = _effective_D_values(stiffness, classification)
    Nx = navier_Nx_expression().subs(subs)
    Nx = Nx.subs({a_sym: geometry.a, b_sym: geometry.b})

    best_val: Optional[float] = None
    best_mode: Optional[Tuple[int, int]] = None
    for mm in range(1, m_max + 1):
        for nn in range(1, n_max + 1):
            val = float(Nx.subs({m_sym: mm, n_sym: nn}).evalf())
            if best_val is None or val < best_val:
                best_val = val
                best_mode = (mm, nn)

    assert best_val is not None and best_mode is not None
    total = best_val * float(sp.sympify(geometry.b))
    return BucklingResult(
        Nx_cr=best_val,
        P_cr_total=total,
        mode=best_mode,
        Nx_symbolic=Nx,
        assumptions=assumptions,
    )


def solve_Pcr_symbolic(
    stiffness: LaminateStiffness,
    classification: Classification,
    geometry: PlateGeometry,
    m: int = 1,
    n: int = 1,
) -> BucklingResult:
    """Return the symbolic critical buckling load for fixed mode ``(m, n)``.

    For parametric studies the governing mode is usually ``(1, 1)`` for a
    uniaxially compressed plate of moderate aspect ratio, so the lowest mode is
    fixed and the result is left symbolic in whatever free symbols the inputs
    carry (e.g. the aspect ratio or a ply angle).

    Parameters
    ----------
    stiffness:
        Computed ABD matrices (may be symbolic).
    classification:
        Matrix-driven classification controlling which D values are used.
    geometry:
        Plate dimensions (may be symbolic).
    m, n:
        Fixed half-wave numbers for the symbolic expression.

    Returns
    -------
    BucklingResult
        ``Nx_cr`` is the symbolic ``N_x(m, n)`` expression; ``mode`` is
        ``(m, n)``.
    """
    subs, assumptions = _effective_D_values(stiffness, classification)
    Nx = navier_Nx_expression().subs(subs)
    Nx = Nx.subs({a_sym: geometry.a, b_sym: geometry.b})
    Nx_mode = sp.simplify(Nx.subs({m_sym: m, n_sym: n}))

    total = sp.simplify(Nx_mode * sp.sympify(geometry.b))
    return BucklingResult(
        Nx_cr=Nx_mode,
        P_cr_total=total,
        mode=(m, n),
        Nx_symbolic=Nx,
        assumptions=assumptions,
    )
