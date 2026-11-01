"""Rep segmentation (hysteresis state machine) and per-rep form scoring."""
from dataclasses import dataclass, field
import numpy as np
from app.exercises import EXERCISES  # noqa: F401  (re-exported for existing imports)


def smooth(x, w=5):
    x = np.asarray(x, float)
    return np.convolve(np.pad(x, w // 2, mode="edge"), np.ones(w) / w, mode="valid")


@dataclass
class Rep:
    start: int
    bottom: int
    end: int
    rom: float
    min_angle: float
    tempo_s: float
    flags: list = field(default_factory=list)
    form_score: int = 100


def segment_reps(angles, fps, ex, min_rep_s=0.5):
    """A rep = leave the top (above high), reach the bottom (below low), return above high.
    The gap between low and high is hysteresis, so jitter does not double-count.
    Reps shorter than min_rep_s are discarded as noise."""
    a = smooth(angles)
    reps, state, start, bottom, lo = [], "top", 0, 0, np.inf
    for i, v in enumerate(a):
        if state == "top":
            if v > ex["high"]:
                start = i
            elif v < ex["low"]:
                state, bottom, lo = "bottom", i, v
        else:
            if v < lo:
                lo, bottom = v, i
            if v > ex["high"]:
                if (i - start) / fps >= min_rep_s:
                    reps.append(Rep(start, bottom, i, rom=float(a[start:i + 1].max() - lo),
                                    min_angle=float(lo), tempo_s=(i - start) / fps))
                state, start, lo = "top", i, np.inf
    return reps


def score_rep(rep, ex, lean_window=None, lean_limit=None):
    """Score one rep. Penalties: incomplete depth -25, excess forward lean -20, too fast -10."""
    penalties = []
    if rep.min_angle > ex["depth_max"]:
        rep.flags.append("incomplete_depth"); penalties.append(25)
    if (ex.get("lean_check") and lean_window is not None and lean_limit is not None
            and np.nanmax(lean_window) > lean_limit):
        rep.flags.append("excess_forward_lean"); penalties.append(20)
    if rep.tempo_s < 0.8:
        rep.flags.append("too_fast"); penalties.append(10)
    rep.form_score = max(0, 100 - sum(penalties))
    return rep


def attribute_cause(reps, heel_lift=False):
    """Likely cause of form breakdown: mobility (heel lift), technique (from rep 1),
    or strength/fatigue (breakdown only in late reps)."""
    bad = [i for i, r in enumerate(reps) if r.flags]
    if not bad:
        return "none"
    if heel_lift:
        return "mobility (ankle restriction)"
    first = bad[0]
    if first == 0:
        return "technique"
    return "strength/fatigue" if first >= len(reps) * 0.6 else "unclear"
