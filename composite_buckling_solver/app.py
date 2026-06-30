"""Streamlit front-end for the composite plate buckling solver.

Run with::

    streamlit run app.py

from inside the ``composite_buckling_solver`` folder (or from anywhere — this
file inserts its own directory on ``sys.path`` so the ``core``/``solver``/
``utils`` packages import regardless of the working directory).

The app exposes the same solver used by ``main.py`` through a simple UI:

* enter the lamina properties, the stacking sequence and the plate geometry;
* a *Numeric* tab prints the A/B/D matrices, the matrix-driven classification
  and the critical buckling load ``N_x,cr`` / total ``P_cr``;
* a *Parametric* tab keeps one quantity symbolic (aspect ratio or ply angle),
  shows the closed-form ``N_x,cr`` expression and plots it over a sweep.

No solver logic lives here — this module is purely a presentation layer.
"""

from __future__ import annotations

import os
import sys
from typing import List

# Make the package importable no matter where streamlit is launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import sympy as sp
import streamlit as st

from core.inputs import LaminaProperties, Layup, PlateGeometry
from core.laminate import classify_laminate, compute_ABD, to_numpy
from solver.equations import (
    governing_equation,
    simplify_for_classification,
    solve_Pcr_numeric,
    solve_Pcr_symbolic,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def parse_angles(text: str) -> List[float]:
    """Parse a comma/space separated angle list, e.g. ``"0, 90, 90, 0"``."""
    raw = text.replace(";", ",").replace(" ", ",")
    return [float(tok) for tok in raw.split(",") if tok.strip() != ""]


def matrix_to_dataframe(M: sp.Matrix):
    """Convert a numeric 3x3 sympy matrix to a labelled numpy array for display."""
    arr = to_numpy(M)
    return arr


# ---------------------------------------------------------------------------
# Sidebar: shared inputs
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Composite Buckling Solver", layout="wide")
st.title("Composite Plate Buckling Solver")
st.caption(
    "Classical laminate theory · simply-supported edges (SSSS) · uniaxial "
    "compression · Navier double-sine solution"
)

with st.sidebar:
    st.header("Lamina properties")
    E1 = st.number_input("E1 [Pa]", value=138e9, format="%.3e")
    E2 = st.number_input("E2 [Pa]", value=9.0e9, format="%.3e")
    G12 = st.number_input("G12 [Pa]", value=6.9e9, format="%.3e")
    nu12 = st.number_input("nu12 [-]", value=0.30, min_value=0.0, max_value=0.49)

    st.header("Layup")
    layup_text = st.text_input("Ply angles [deg]", value="0, 90, 90, 0")
    symmetric_mirror = st.checkbox("Mirror as symmetric  [..]s", value=False)
    ply_t_mm = st.number_input("Ply thickness [mm]", value=1.0, min_value=1e-3)

    st.header("Plate geometry")
    a_mm = st.number_input("Length a [mm]", value=500.0, min_value=1.0)
    b_mm = st.number_input("Width b [mm]", value=250.0, min_value=1.0)

# Build the shared data objects from the sidebar inputs.
lamina = LaminaProperties(E1=E1, E2=E2, G12=G12, nu12=nu12)
try:
    angles = parse_angles(layup_text)
    if not angles:
        raise ValueError("empty")
except ValueError:
    st.error("Could not parse the ply angles. Use e.g. `0, 90, 90, 0`.")
    st.stop()

ply_t = ply_t_mm * 1e-3
if symmetric_mirror:
    layup = Layup.from_symmetric(angles, ply_thickness=ply_t)
else:
    layup = Layup(angles=angles, ply_thickness=ply_t)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_numeric, tab_parametric = st.tabs(["Numeric solution", "Parametric study"])


with tab_numeric:
    geometry = PlateGeometry(a=a_mm * 1e-3, b=b_mm * 1e-3)
    stiffness = compute_ABD(lamina, layup)
    classification = classify_laminate(stiffness, layup)

    st.subheader("Laminate")
    c1, c2, c3 = st.columns(3)
    c1.metric("Expanded plies", layup.n_plies)
    c2.metric("Total thickness", f"{float(layup.total_thickness)*1e3:.3f} mm")
    c3.metric("Aspect ratio a/b", f"{float(geometry.aspect_ratio):.3f}")
    st.write("**Expanded layup:**", layup.angles)

    st.subheader("Classification (from the computed matrices)")
    st.write(" · ".join(classification.labels))
    cc1, cc2, cc3 = st.columns(3)
    cc1.write(f"symmetric (B≈0): **{classification.is_symmetric}**")
    cc2.write(f"balanced (A16=A26=0): **{classification.is_balanced}**")
    cc3.write(
        f"specially orthotropic: **{classification.is_specially_orthotropic}**"
    )

    st.subheader("Stiffness matrices")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown("**A [N/m]**")
        st.dataframe(matrix_to_dataframe(stiffness.A))
    with m2:
        st.markdown("**B [N]**")
        st.dataframe(matrix_to_dataframe(stiffness.B))
    with m3:
        st.markdown("**D [N·m]**")
        st.dataframe(matrix_to_dataframe(stiffness.D))

    # Sanity checks (same as main.py).
    D_np = to_numpy(stiffness.D)
    B_np = to_numpy(stiffness.B)
    st.caption(
        f"Sanity: max|D − Dᵀ| = {float(abs(D_np - D_np.T).max()):.2e} (≈0), "
        f"max|B| = {float(abs(B_np).max()):.2e} "
        f"({'≈0, symmetric' if classification.is_symmetric else 'B≠0, unsymmetric'})"
    )

    st.subheader("Critical buckling load")
    result = solve_Pcr_numeric(stiffness, classification, geometry)
    r1, r2, r3 = st.columns(3)
    r1.metric("N_x,cr [N/m]", f"{result.Nx_cr:.4e}")
    r2.metric("P_cr total [N]", f"{result.P_cr_total:.4e}")
    r3.metric("Mode (m, n)", f"{result.mode}")
    for note in result.assumptions:
        st.warning(note)


with tab_parametric:
    st.subheader("Parametric study")
    param = st.selectbox(
        "Sweep parameter",
        ["aspect ratio a/b", "ply angle θ (for ±θ angle-ply)"],
    )
    cstart, cend, cnum = st.columns(3)

    # xs/ys for the plot, plus an optional closed-form expression to display.
    expr = None  # symbolic N_x,cr expression (aspect-ratio case only)
    cls_for_eq = None  # classification used for the governing-eq expander

    if param.startswith("aspect"):
        # Aspect-ratio sweep: only the plate length 'a' is symbolic, so the
        # closed-form N_x,cr is a cheap rational polynomial -> solve once.
        lo = cstart.number_input("from", value=0.5, key="ar_lo")
        hi = cend.number_input("to", value=2.5, key="ar_hi")
        npts = int(cnum.number_input("points", value=40, min_value=5, key="ar_n"))

        a_sym = sp.Symbol("a", positive=True)
        b_val = b_mm * 1e-3
        geom_s = PlateGeometry(a=a_sym, b=b_val)
        stiff_s = compute_ABD(lamina, layup)
        cls_for_eq = classify_laminate(stiff_s, layup)
        res_s = solve_Pcr_symbolic(stiff_s, cls_for_eq, geom_s, m=1, n=1)

        R = sp.Symbol("R", positive=True)
        expr = sp.simplify(res_s.Nx_cr.subs(a_sym, R * b_val))
        assumptions = res_s.assumptions

        f = sp.lambdify(R, expr, modules="numpy")
        xs = np.linspace(lo, hi, npts)
        ys = np.array([float(f(v)) for v in xs])
        xlabel = "aspect ratio a/b"
        xname = "a/b"
    else:
        # Angle sweep: a symbolic ply angle makes the trig stiffness terms
        # explode, so we evaluate NUMERICALLY at each angle (recompute ABD)
        # instead of carrying a giant symbolic expression.
        lo = cstart.number_input("from [deg]", value=0.0, key="th_lo")
        hi = cend.number_input("to [deg]", value=90.0, key="th_hi")
        npts = int(cnum.number_input("points", value=37, min_value=5, key="th_n"))
        geom_s = PlateGeometry(a=a_mm * 1e-3, b=b_mm * 1e-3)

        xs = np.linspace(lo, hi, npts)
        ys = np.empty_like(xs)
        assumptions_set = set()
        for i, ang in enumerate(xs):
            lp = Layup.from_symmetric([float(ang), -float(ang)], ply_thickness=ply_t)
            stf = compute_ABD(lamina, lp)
            cl = classify_laminate(stf, lp)
            r = solve_Pcr_numeric(stf, cl, geom_s)
            ys[i] = r.Nx_cr
            assumptions_set.update(r.assumptions)
            if i == len(xs) // 2:
                cls_for_eq = cl  # representative classification for the expander
        assumptions = sorted(assumptions_set)
        xlabel = "ply angle θ [deg]  (layup [+θ/−θ]s)"
        xname = "θ [deg]"
        st.info("Angle-ply [±θ]s is generally not specially orthotropic, so "
                "this curve is evaluated numerically at each angle (bend-twist "
                "D16/D26 terms neglected in the single-term Navier load).")

    # Governing-equation simplification (before vs after) for this laminate.
    with st.expander("Governing equation simplification (before vs after)"):
        w = sp.Function("w")
        st.write("**General:**")
        st.latex(sp.latex(governing_equation(w)))
        st.write("**Specialised to classification:**")
        st.latex(sp.latex(simplify_for_classification(cls_for_eq)))

    if expr is not None:
        st.write("**Closed-form N_x,cr (mode m=n=1):**")
        st.latex(sp.latex(expr) + r"\;\;[\mathrm{N/m}]")
    for note in assumptions:
        st.warning(note)

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(xs, ys, lw=2, color="#c0504d")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("N_x,cr  [N/m]")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    st.pyplot(fig)

    imin = int(np.argmin(ys))
    st.caption(
        f"Minimum N_x,cr ≈ {ys[imin]:.4e} N/m at {xname} = {xs[imin]:.3f}"
    )
