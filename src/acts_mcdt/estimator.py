"""Estimators and reduced-model identification.

Two objects live here, both separated from ``physics.rollout`` so that the
truth field never reads the estimator:

``identify_two_node``
    Fit ``(R_ext, R_int, C_1, C_2)`` of the two-node reduction to a temperature
    history produced by the sixteen-cell field. This is the evidence that the
    contraction in chapter 3 is a contraction and not a second, unrelated
    model.

``DualEKF``
    Two-state extended Kalman filter on ``(T_cold, R_int)``. It replaces the
    scalar lag tracker in the display generation. The posterior covariance is
    updated continuously instead of being multiplied by a constant at the end
    of the probe window.

State and measurement conventions
---------------------------------
``T_cold`` is degrees Celsius, ``R_int`` is the dimensionless resistance the
kernel uses (prior 5.0, clipped to [0.8, 8.0]). The measurement vector is the
surface temperature (C) and the mean moisture (fraction). The cold spot is not
measured; it is the hidden state the whole exercise is about.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# ---------------------------------------------------------------------------
# Two-node identification
# ---------------------------------------------------------------------------


@dataclass
class TwoNodeParams:
    """Identified two-node reduction of one slab."""

    r_ext: float
    r_int: float
    c1: float
    c2: float
    rmse: float
    n_samples: int

    def as_dict(self) -> dict:
        return {
            "r_ext": round(self.r_ext, 6),
            "r_int": round(self.r_int, 6),
            "c1": round(self.c1, 6),
            "c2": round(self.c2, 6),
            "rmse": round(self.rmse, 6),
            "n_samples": self.n_samples,
        }


def two_node_rhs(t1: float, t2: float, params: TwoNodeParams,
                 t_inf: float, q_lat: float) -> tuple[float, float]:
    """Right-hand side of the two-node reduction.

    ``t_inf`` is the boundary air temperature, ``q_lat`` the latent flux. Both
    enter the surface node only, which is why the input matrix has rank one at
    equilibrium (proposition 4.2.2).
    """
    dt1 = ((t_inf - t1) / params.r_ext + (t2 - t1) / params.r_int + q_lat) / params.c1
    dt2 = ((t1 - t2) / params.r_int) / params.c2
    return dt1, dt2


def simulate_two_node(params: TwoNodeParams, t_inf: np.ndarray, q_lat: np.ndarray,
                      t1_0: float, t2_0: float, dt: float) -> tuple[np.ndarray, np.ndarray]:
    """Integrate the two-node reduction with the same explicit step as the field."""
    n = t_inf.shape[0]
    t1 = np.empty(n)
    t2 = np.empty(n)
    t1[0], t2[0] = t1_0, t2_0
    for i in range(1, n):
        d1, d2 = two_node_rhs(t1[i - 1], t2[i - 1], params, t_inf[i - 1], q_lat[i - 1])
        t1[i] = t1[i - 1] + dt * d1
        t2[i] = t2[i - 1] + dt * d2
    return t1, t2


def identify_two_node(
    surf: np.ndarray,
    core: np.ndarray,
    *,
    dt: float,
    length: float,
    t_inf: float = 190.0,
    q_lat: float = 0.0,
    iters: int = 400,
    lr: float = 0.02,
    init: tuple[float, float, float, float] = (1.0, 3.0, 1.0, 4.0),
) -> TwoNodeParams:
    """Least-squares fit of the two-node reduction to a field history.

    Gradients are computed by finite differences on the four scalars. The
    search is plain gradient descent with a decaying step, which is enough for
    four parameters and a few hundred samples. Returns the fit and its RMSE
    against the *core* trajectory, because the cold spot is the quantity the
    report scores.
    """
    surf = np.asarray(surf, dtype=float)
    core = np.asarray(core, dtype=float)
    n = surf.shape[0]
    if n < 10:
        raise ValueError("need at least 10 samples to identify a two-node model")
    t1_inf = np.full(n, t_inf)
    q = np.full(n, q_lat)

    def loss(par: np.ndarray) -> float:
        p = TwoNodeParams(par[0], par[1], par[2], par[3], 0.0, n)
        t1, t2 = simulate_two_node(p, t1_inf, q, float(surf[0]), float(core[0]), dt)
        # Fit surface and core together; the cold spot carries double weight
        # because it is the decision variable.
        return float(np.mean((t1 - surf) ** 2) + 2.0 * np.mean((t2 - core) ** 2))

    par = np.array(init, dtype=float)
    best = par.copy()
    best_loss = loss(par)
    step = lr
    for it in range(iters):
        grad = np.zeros(4)
        for j in range(4):
            probe = par.copy()
            probe[j] += max(1e-6, 1e-4 * abs(par[j]))
            grad[j] = (loss(probe) - best_loss) / (probe[j] - par[j])
        norm = np.linalg.norm(grad)
        if norm < 1e-9:
            break
        par = par - step * grad / (norm + 1e-12)
        # Keep the parameters physical.
        par[0] = float(np.clip(par[0], 0.05, 20.0))
        par[1] = float(np.clip(par[1], 0.05, 40.0))
        par[2] = float(np.clip(par[2], 0.05, 50.0))
        par[3] = float(np.clip(par[3], 0.05, 200.0))
        cur = loss(par)
        if cur < best_loss:
            best_loss = cur
            best = par.copy()
            step *= 1.02
        else:
            step *= 0.7
        if step < 1e-7:
            break

    p = TwoNodeParams(best[0], best[1], best[2], best[3], 0.0, n)
    t1, t2 = simulate_two_node(p, t1_inf, q, float(surf[0]), float(core[0]), dt)
    rmse = float(np.sqrt(np.mean((t2 - core) ** 2)))
    p.rmse = rmse
    return p


# ---------------------------------------------------------------------------
# Dual extended Kalman filter
# ---------------------------------------------------------------------------


@dataclass
class EKFDiagnostics:
    """Per-step trace kept for the figures."""

    t_cold: list[float] = field(default_factory=list)
    r_hat: list[float] = field(default_factory=list)
    var_r: list[float] = field(default_factory=list)
    innovation: list[float] = field(default_factory=list)


class DualEKF:
    """Two-state EKF on ``(T_cold, R_int)``.

    Observation model. The only channel the machine has is the surface
    temperature ``y_T``. The surface differs from the cold spot by the internal
    lag, and that lag is what carries the information about ``R_int``. The
    kernel already encodes the relation in its own resistance proxy::

        r = gap/8 + 1.2 + 2.5 S    =>    gap = 8 (r - 1.2 - 2.5 S)

    so the observation model the filter uses is::

        h(x) = T_cold + 8 (r - 1.2)          (crust term omitted)

    with ``dh/dT_cold = 1`` and ``dh/dr = 8``. This is a pseudo-measurement:
    the filter is not told the gap, it is told the surface temperature and must
    decide how much of the offset from its cold-spot estimate is "the core
    rose" and how much is "the resistance is larger than I thought". The 2x2
    covariance is what splits the two, which is precisely the piece the scalar
    tracker lacks.

    At equilibrium the gap is zero and ``r`` loses its column, matching the
    zero-sensitivity proposition. During a probe the gap opens, the column
    becomes non-zero, and the posterior contracts. That is the information
    action, expressed in the filter rather than added as a constant.

    Truth field never reads this: the filter sees only ``y_T``.
    """

    #: Slope of the kernel's own resistance proxy, ``d gap / d r``.
    GAP_PER_R = 8.0
    #: Intercept of the same proxy, in units of r.
    GAP_OFFSET = 1.2

    def __init__(
        self,
        *,
        t0: float,
        r_prior: float = 5.0,
        var_r_prior: float = 0.64,
        var_t_prior: float = 4.0,
        q_t: float = 0.05,
        q_r: float = 1.0e-3,
        r_obs: float = 0.16,
        r_min: float = 0.8,
        r_max: float = 8.0,
        var_r_cap: float = 0.64,
        scale_length: float = 0.03,
        tau_scale: float = 280.0,
        tau_ref_length: float = 0.03,
    ) -> None:
        self.t = float(t0)
        self.r = float(r_prior)
        self.P = np.diag([var_t_prior, var_r_prior])
        self.q_t = q_t
        self.q_r = q_r
        self.R = r_obs
        self.r_min = r_min
        self.r_max = r_max
        self.var_r_cap = var_r_cap
        self.scale_length = scale_length
        self.tau_scale = tau_scale
        self.tau_ref_length = tau_ref_length
        self.trace = EKFDiagnostics()

    # -- model pieces -------------------------------------------------------
    def tau(self, r: float, length: float) -> float:
        rc = float(np.clip(r, self.r_min, self.r_max))
        return rc * (length / self.tau_ref_length) ** 2 * self.tau_scale

    def observe(self, t_cold: float, r: float) -> float:
        """Predicted surface temperature from the two states."""
        return t_cold + self.GAP_PER_R * (r - self.GAP_OFFSET)

    # -- filter -------------------------------------------------------------
    def step(self, *, y_t: float, dt: float, boundary_moved: bool,
             length: float = 0.03) -> tuple[float, float, float]:
        """Advance one step. Returns ``(t_cold, r_hat, var_r)``."""
        # The resistance is a slowly varying parameter; its process noise is
        # raised only while the boundary is moving, which is when the gap is
        # informative.
        q_r = self.q_r * (30.0 if boundary_moved else 1.0)
        Q = np.diag([self.q_t, q_r])

        # Predict the cold spot through the same lag law the kernel uses.
        t_cold = self.t
        tau = self.tau(self.r, length)
        f_t = t_cold + dt * (y_t - t_cold) / tau
        F = np.array([[1.0, 0.0], [0.0, 1.0]])
        P = F @ self.P @ F.T + Q

        # Update with the pseudo-measurement.
        H = np.array([1.0, self.GAP_PER_R])
        S = float(H @ P @ H.T + self.R)
        K = (P @ H) / S
        innovation = y_t - self.observe(f_t, self.r)
        t_cold = f_t + float(K[0]) * innovation
        r = float(np.clip(self.r + float(K[1]) * innovation, self.r_min, self.r_max))
        P = P - np.outer(K, H @ P)
        P = 0.5 * (P + P.T)
        P = np.maximum(P, 0.0)
        # The prior box is the honest bound on this parameter; never report a
        # posterior wider than it.
        P[1, 1] = min(P[1, 1], self.var_r_cap)

        self.t = float(t_cold)
        self.r = r
        self.P = P
        self.trace.t_cold.append(float(t_cold))
        self.trace.r_hat.append(r)
        self.trace.var_r.append(float(P[1, 1]))
        self.trace.innovation.append(float(innovation))
        return float(t_cold), r, float(P[1, 1])
