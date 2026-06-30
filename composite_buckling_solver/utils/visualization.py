"""Plotting helpers for parametric buckling studies (matplotlib).

The single public function, :func:`plot_Pcr_vs_parameter`, takes a *symbolic*
critical-load expression and one free symbol to sweep, lambdifies the
expression, and plots ``P_cr`` against that parameter.  This supports the
parametric study required by the task, e.g. sweeping the plate aspect ratio
``a/b`` or a ply orientation angle.
"""

from __future__ import annotations

from typing import Iterable, Optional, Sequence

import numpy as np
import sympy as sp

import matplotlib

# Use a non-interactive backend so the module works in headless environments
# (CI, servers) where no display is available; figures are saved to file.
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (import after backend selection)


def plot_Pcr_vs_parameter(
    Pcr_expr: sp.Expr,
    parameter: sp.Symbol,
    values: Sequence[float],
    extra_subs: Optional[dict] = None,
    xlabel: Optional[str] = None,
    ylabel: str = "Critical buckling load  N_x,cr  [N/m]",
    title: str = "Composite plate buckling: P_cr vs parameter",
    save_path: Optional[str] = None,
    show: bool = False,
) -> str:
    """Plot a symbolic ``P_cr`` expression against one swept parameter.

    Parameters
    ----------
    Pcr_expr:
        A sympy expression for the critical load.  After applying
        ``extra_subs`` it must contain exactly the one free symbol
        ``parameter``.
    parameter:
        The sympy symbol to sweep along the x-axis (e.g. aspect ratio or angle).
    values:
        The numeric values of ``parameter`` to evaluate.
    extra_subs:
        Optional substitutions for any *other* symbols in ``Pcr_expr`` (e.g.
        fixing the laminate D values or plate width) so that only ``parameter``
        remains free.
    xlabel:
        Label for the x-axis; defaults to the parameter's name.
    ylabel, title:
        Axis label and figure title.
    save_path:
        Where to write the PNG.  Defaults to ``Pcr_vs_<param>.png`` in the cwd.
    show:
        If ``True`` attempt an interactive ``plt.show()`` (no-op under the Agg
        backend); the figure is always saved regardless.

    Returns
    -------
    str
        The path the figure was saved to.
    """
    expr = Pcr_expr.subs(extra_subs) if extra_subs else Pcr_expr

    remaining = expr.free_symbols - {parameter}
    if remaining:
        raise ValueError(
            "Expression still contains unsubstituted symbols besides the "
            f"swept parameter: {remaining}. Provide them via extra_subs."
        )

    # Lambdify to a fast numpy-callable for evaluation over the sweep.
    f = sp.lambdify(parameter, expr, modules="numpy")
    xs = np.asarray(list(values), dtype=float)
    ys = np.asarray([float(f(v)) for v in xs], dtype=float)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(xs, ys, lw=2, color="#c0504d")
    ax.set_xlabel(xlabel or str(parameter))
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    out = save_path or f"Pcr_vs_{parameter}.png"
    fig.savefig(out, dpi=130)
    if show:
        plt.show()
    plt.close(fig)
    return out
