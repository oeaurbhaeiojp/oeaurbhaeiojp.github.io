"""Driver wiring the composite buckling solver modules into two test cases.

Run with::

    python main.py

Test case 1 (numeric)
    A thick symmetric cross-ply laminate (representative of a structural panel,
    e.g. a marine / leaf-spring style plate).  Prints the A, B, D matrices and
    the numeric critical buckling load.  Sanity checks: D symmetric and B ~ 0.

Test case 2 (parametric / symbolic)
    A symmetric angle-ply laminate analysed with a symbolic plate length so the
    critical load comes out as a closed-form expression in the aspect ratio.
    Prints the simplified symbolic P_cr and plots it against the aspect ratio.

This module is a *consumer* of the package only; nothing imports from here, in
keeping with the modularity requirement.
"""

from __future__ import annotations

import sympy as sp

from core.inputs import LaminaProperties, Layup, PlateGeometry
from core.laminate import classify_laminate, compute_ABD, to_numpy
from solver.equations import (
    governing_equation,
    simplify_for_classification,
    solve_Pcr_numeric,
    solve_Pcr_symbolic,
)
from utils.visualization import plot_Pcr_vs_parameter


def _print_matrix(name: str, M: sp.Matrix) -> None:
    """Pretty-print a (possibly numeric) 3x3 sympy matrix with aligned cols."""
    print(f"  {name} =")
    for i in range(M.rows):
        row = []
        for j in range(M.cols):
            entry = M[i, j]
            if entry.free_symbols:
                row.append(f"{sp.simplify(entry)!s:>22}")
            else:
                row.append(f"{float(entry):>22.6e}")
        print("    [" + " ".join(row) + "]")


def numeric_case() -> None:
    """Test case 1: fully numeric symmetric angle-ply laminate.

    A thick symmetric balanced angle-ply ``[+45/-45]s`` is representative of
    marine / leaf-spring style panels that rely on off-axis plies for shear and
    torsional stiffness.  Being symmetric it has ``B ~ 0`` (checked below) but
    it is NOT specially orthotropic (``D16, D26 != 0``), so the solver applies
    and reports the single-term Navier bend-twist approximation.
    """
    print("=" * 74)
    print("TEST CASE 1 — Numeric symmetric angle-ply laminate (uniaxial, SSSS)")
    print("=" * 74)

    # E-glass/epoxy-like unidirectional lamina properties (SI units, Pa / -),
    # a typical marine-structural material system.
    lamina = LaminaProperties(
        E1=138e9,    # longitudinal modulus [Pa]
        E2=9.0e9,    # transverse modulus [Pa]
        G12=6.9e9,   # in-plane shear modulus [Pa]
        nu12=0.30,   # major Poisson ratio [-]
    )

    # Thick symmetric angle-ply: [45/-45/-45/45], 1.0 mm per ply -> 4 mm total.
    layup = Layup.from_symmetric([45.0, -45.0], ply_thickness=1.0e-3)
    geometry = PlateGeometry(a=0.5, b=0.25)  # 500 x 250 mm plate

    print(f"\nLayup (expanded): {layup.angles}")
    print(f"Ply thickness   : {layup.ply_thickness*1e3:.3f} mm")
    print(f"Total thickness : {layup.total_thickness*1e3:.3f} mm")
    print(f"Plate a x b     : {geometry.a} x {geometry.b} m "
          f"(aspect a/b = {float(geometry.aspect_ratio):.3f})")

    stiffness = compute_ABD(lamina, layup)
    print("\nLaminate stiffness matrices (SI units):")
    _print_matrix("A [N/m]   ", stiffness.A)
    _print_matrix("B [N]     ", stiffness.B)
    _print_matrix("D [N*m]   ", stiffness.D)

    classification = classify_laminate(stiffness, layup)
    print("\nClassification (from the computed matrices):")
    print(f"  labels                  : {classification.labels}")
    print(f"  symmetric (B~0)         : {classification.is_symmetric}")
    print(f"  balanced (A16=A26=0)    : {classification.is_balanced}")
    print(f"  specially orthotropic   : {classification.is_specially_orthotropic}")

    # --- Sanity checks required by the task -------------------------------
    D_np = to_numpy(stiffness.D)
    B_np = to_numpy(stiffness.B)
    d_sym_err = float(abs(D_np - D_np.T).max())
    b_max = float(abs(B_np).max())
    print("\nSanity checks:")
    print(f"  D symmetry max|D - D^T| : {d_sym_err:.3e}  (expect ~0)")
    print(f"  B max|B_ij|             : {b_max:.3e}  (expect ~0 for symmetric)")

    result = solve_Pcr_numeric(stiffness, classification, geometry)
    print("\nBuckling result:")
    print(f"  governing mode (m,n)    : {result.mode}")
    print(f"  N_x,cr  (per unit width): {result.Nx_cr:.6e} N/m")
    print(f"  P_cr    (total, = N_x*b): {result.P_cr_total:.6e} N")
    if result.assumptions:
        print("  approximation notes:")
        for note in result.assumptions:
            print(f"    - {note}")


def symbolic_case() -> None:
    """Test case 2: parametric/symbolic symmetric cross-ply laminate.

    A symmetric cross-ply ``[0/90]s`` is *specially orthotropic*
    (``D16 = D26 = 0``), so the governing equation simplification visibly drops
    the bend-twist terms and the Navier critical load is an EXACT closed-form
    expression — ideal for a parametric study in the aspect ratio.
    """
    print("\n" + "=" * 74)
    print("TEST CASE 2 — Parametric symbolic cross-ply laminate (aspect sweep)")
    print("=" * 74)

    lamina = LaminaProperties(E1=138e9, E2=9.0e9, G12=6.9e9, nu12=0.30)

    # Symmetric cross-ply [0/90]s -> [0,90,90,0] (specially orthotropic).
    layup = Layup.from_symmetric([0.0, 90.0], ply_thickness=1.0e-3)

    # Keep the plate length 'a' symbolic so P_cr is parametric in aspect ratio.
    a = sp.Symbol("a", positive=True)
    b_val = 0.25
    geometry = PlateGeometry(a=a, b=b_val)

    print(f"\nLayup (expanded): {layup.angles}")
    print("Plate length 'a' kept symbolic; width b = "
          f"{b_val} m -> aspect ratio = a/{b_val}")

    stiffness = compute_ABD(lamina, layup)
    classification = classify_laminate(stiffness, layup)
    print("\nClassification (from the computed matrices):")
    print(f"  labels                : {classification.labels}")
    print(f"  symmetric (B~0)       : {classification.is_symmetric}")
    print(f"  specially orthotropic : {classification.is_specially_orthotropic}")

    # --- Show the symbolic simplification of the governing equation -------
    w = sp.Function("w")
    general_eq = governing_equation(w)
    simplified_eq = simplify_for_classification(classification)
    print("\nGoverning equation simplification (before vs after):")
    print(f"  BEFORE (general, keeps D16,D26 terms):\n    {general_eq}")
    print(f"  AFTER  (specialised to classification):\n    {simplified_eq}")
    dropped = general_eq.free_symbols - simplified_eq.free_symbols
    print(f"  symbols dropped by simplification: "
          f"{dropped if dropped else '(none)'}")

    # --- Symbolic P_cr expression -----------------------------------------
    result = solve_Pcr_symbolic(stiffness, classification, geometry, m=1, n=1)
    print("\nSymbolic critical load (mode m=n=1):")
    print(f"  N_x,cr(a) = {result.Nx_cr}")
    if result.assumptions:
        print("  approximation notes:")
        for note in result.assumptions:
            print(f"    - {note}")

    # --- Plot P_cr vs aspect ratio ----------------------------------------
    # Re-express in the aspect ratio R = a/b by substituting a = R*b.
    R = sp.Symbol("R", positive=True)
    Pcr_of_R = result.Nx_cr.subs(a, R * b_val)
    Pcr_of_R = sp.simplify(Pcr_of_R)
    print(f"\n  N_x,cr as a function of aspect ratio R=a/b:\n    {Pcr_of_R}")

    aspect_values = [0.5 + 0.05 * k for k in range(0, 41)]  # 0.5 .. 2.5
    out_path = plot_Pcr_vs_parameter(
        Pcr_of_R,
        parameter=R,
        values=aspect_values,
        xlabel="aspect ratio  a/b",
        title="[0/90]s plate: N_x,cr vs aspect ratio (mode m=n=1)",
        save_path="Pcr_vs_aspect_ratio.png",
    )
    print(f"\n  Saved plot -> {out_path}")


def main() -> None:
    """Run both demonstration cases."""
    numeric_case()
    symbolic_case()
    print("\nDone.")


if __name__ == "__main__":
    main()
