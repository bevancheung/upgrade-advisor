# -*- coding: utf-8 -*-
"""The validated upgrade decision policy (UpgradeBench §6, Table 6).

Pure python, no GPU. Inputs are measurements; output is an Action with the
evidence chain attached. Margins and gate structure follow the paper's
prospectively specified settings: epsilon = 1pp for classification, 2pp for
structured generation; copy is gated on documented short-distance
continuation plus a regression gate; every gate reads a validation (gate)
set that is disjoint from the reporting set.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

EPS_CLASSIFICATION = 0.01
EPS_STRUCTURED = 0.02

# Continuation distance above which copying is not licensed. The paper
# measured retention 0.88-0.99 at 46B tokens and ~0 at 2.9T; the boundary
# between those endpoints is unmeasured, so the default is conservative.
COPY_MAX_CONTINUATION_TOKENS = 100e9


class Action(str, Enum):
    FREEZE = "freeze"
    COPY = "copy"
    REFRESH = "refresh"
    RETRAIN = "retrain"
    INCONCLUSIVE = "inconclusive"   # gate set cannot resolve epsilon (fix #2)


# Relative-error-reduction gate (theory-review fix #1): near the accuracy
# ceiling, absolute pp compress real gains; a reference that removes >=30%
# of the frozen specialist's errors (with enough error mass to be meaningful)
# also opens the upgrade waterfall.
RER_THRESHOLD = 0.30
RER_MIN_ERRORS = 10
# Fewer frozen errors than this on the gate set means the eval itself no
# longer discriminates (fix #3).
SATURATION_MIN_ERRORS = 20


@dataclass
class Measurements:
    """Everything the policy may consult. Scores in [0,1] on the GATE set.

    Required: freeze_score, adopt_floor. The rest unlock branches:
    reference_score (measured or beta-estimated), copy_score, refresh_score.
    """
    task_kind: str                      # "classification" | "structured"
    freeze_score: float                 # current specialist, gate set
    adopt_floor: float                  # target base zero/few-shot, gate set
    reference_score: Optional[float] = None
    reference_is_estimate: bool = False  # True if beta-projected, not trained
    copy_score: Optional[float] = None
    copy_negative_flip_rate: Optional[float] = None
    refresh_score: Optional[float] = None
    refresh_negative_flip_rate: Optional[float] = None
    inputs_retained: bool = False
    gold_labels_retained: bool = False
    gate_set_size: int = 0
    # genealogy verdict for the (source, target) pair
    shape_compatible: bool = False
    documented_continuation: bool = False
    continuation_tokens: Optional[float] = None
    # power layer (fix #2): freeze-vs-reference disagreement rate on the
    # gate set, when the reference is measured (None for estimates)
    discordant_rate: Optional[float] = None


@dataclass
class Recommendation:
    action: Action
    epsilon: float
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    evidence: dict = field(default_factory=dict)


def _eps(task_kind: str) -> float:
    return EPS_CLASSIFICATION if task_kind == "classification" else EPS_STRUCTURED


def recommend(m: Measurements, flip_budget: Optional[float] = None) -> Recommendation:
    eps = _eps(m.task_kind)
    r = Recommendation(action=Action.FREEZE, epsilon=eps)
    r.evidence = {
        "freeze_score": m.freeze_score,
        "adopt_floor": m.adopt_floor,
        "reference_score": m.reference_score,
        "gate_set_size": m.gate_set_size,
    }
    if m.gate_set_size and m.gate_set_size < 500:
        r.warnings.append(
            f"gate set has only {m.gate_set_size} items; gate sampling error "
            "at this size caused the worst episode in the paper's replay -- "
            "treat marginal verdicts as ties")

    # ---- Step 1: opportunity gate ----------------------------------------
    if m.reference_score is None:
        r.reasons.append(
            "no reference score (measured or beta-estimated); without an "
            "upgrade-opportunity estimate the default is FREEZE, revisit "
            "after logging one more release")
        return r
    gain = m.reference_score - m.freeze_score
    r.evidence["opportunity_pp"] = round(gain * 100, 2)

    # ---- error-scale view (fix #1) ----
    err_f = 1.0 - m.freeze_score
    err_r = 1.0 - m.reference_score
    freeze_errors = round(err_f * m.gate_set_size) if m.gate_set_size else None
    rer = (err_f - err_r) / err_f if err_f > 1e-12 else None
    if rer is not None:
        r.evidence["opportunity_rer"] = round(rer, 3)
    if freeze_errors is not None:
        r.evidence["freeze_errors_on_gate"] = freeze_errors

    # ---- saturation flag (fix #3) ----
    saturated = (freeze_errors is not None
                 and freeze_errors < SATURATION_MIN_ERRORS)
    if saturated:
        r.warnings.append(
            f"EVAL-SATURATED: the frozen specialist makes only "
            f"{freeze_errors} error(s) on the gate set -- any upgrade "
            "comparison rests on that many items. Harvest hard/tail "
            "examples (e.g. production misroutes) before trusting an "
            "upgrade verdict here")

    # ---- opportunity decision: absolute-pp OR relative-error gate ----
    rer_opens = (rer is not None and rer >= RER_THRESHOLD and gain > 0
                 and freeze_errors is not None
                 and freeze_errors >= RER_MIN_ERRORS)
    if rer_opens and gain <= eps + 1e-9:
        r.reasons.append(
            f"absolute gain {gain*100:.2f}pp is within epsilon, but the "
            f"reference removes {rer:.0%} of the frozen specialist's errors "
            f"({freeze_errors} errors on the gate set) -- near the accuracy "
            "ceiling the error-rate scale is the decision-relevant one "
            "(bounded-metric compression), so the upgrade waterfall opens")
    if gain <= eps + 1e-9 and not rer_opens:
        # ---- power check before declaring a null (fix #2) ----
        if (not m.reference_is_estimate and m.discordant_rate is not None
                and m.gate_set_size):
            from . import stats as _S
            mde_pp = _S.mde(m.discordant_rate, m.gate_set_size)
            r.evidence["mde_pp"] = round(mde_pp * 100, 2)
            if mde_pp > eps and abs(gain) < mde_pp:
                n_req = _S.required_n(m.discordant_rate, eps)
                r.action = Action.INCONCLUSIVE
                r.reasons.append(
                    f"the gate set cannot resolve this decision: minimal "
                    f"detectable difference at n={m.gate_set_size} is "
                    f"{mde_pp*100:.1f}pp (> epsilon {eps*100:.0f}pp) and the "
                    f"observed gain {gain*100:.2f}pp is inside that noise "
                    f"floor. Resolving epsilon needs roughly n={n_req}. "
                    "Operational stance until then: keep serving the frozen "
                    "specialist, and grow the gate set")
                return r
        r.reasons.append(
            f"retraining reference beats the frozen specialist by "
            f"{gain*100:.2f}pp <= epsilon ({eps*100:.0f}pp)"
            + (f" with relative error reduction {rer:.0%} below the "
               f"{RER_THRESHOLD:.0%} gate" if rer is not None else "")
            + ": upgrading buys nothing measurable on this task")
        if m.reference_is_estimate:
            r.warnings.append("reference was beta-estimated, not trained; "
                              "log the trained reference when convenient")
        return r

    # ---- Step 2: copy gate (genealogy + distance + regression) -----------
    if m.shape_compatible and m.copy_score is not None:
        licensed = (m.documented_continuation
                    and m.continuation_tokens is not None
                    and m.continuation_tokens <= COPY_MAX_CONTINUATION_TOKENS)
        passes_quality = m.copy_score >= m.reference_score - eps
        passes_flips = (flip_budget is None
                        or m.copy_negative_flip_rate is None
                        or m.copy_negative_flip_rate <= flip_budget)
        r.evidence["copy_score"] = m.copy_score
        r.evidence["copy_licensed_by_genealogy"] = licensed
        if licensed and passes_quality and passes_flips:
            r.action = Action.COPY
            r.reasons.append(
                "target is a documented short continuation "
                f"({m.continuation_tokens/1e9:.0f}B tokens) of the source "
                "weights and the copied adapter passes the quality and "
                "flip gates: copying is near-free here")
            return r
        if not licensed:
            r.reasons.append(
                "copy not licensed: shape compatibility alone does not "
                "license copying (independent-run copies collapsed below "
                "the no-adapter floor in the paper); requires documented "
                f"continuation <= {COPY_MAX_CONTINUATION_TOKENS/1e9:.0f}B tokens")
        elif not passes_quality:
            r.reasons.append(
                f"copy fails the quality gate ({m.copy_score:.4f} vs "
                f"reference {m.reference_score:.4f} - eps)")
        else:
            r.reasons.append(
                f"copy fails the flip gate (NFR {m.copy_negative_flip_rate:.2%} "
                f"> budget {flip_budget:.2%})")

    # ---- Step 3: refresh (annotation-free, input-retaining) --------------
    if m.inputs_retained and m.refresh_score is not None:
        passes_quality = m.refresh_score >= m.reference_score - eps
        passes_flips = (flip_budget is None
                        or m.refresh_negative_flip_rate is None
                        or m.refresh_negative_flip_rate <= flip_budget)
        r.evidence["refresh_score"] = m.refresh_score
        if passes_quality and passes_flips:
            r.action = Action.REFRESH
            r.reasons.append(
                "refresh student passes the gates; saves gold annotation "
                "(paper: retention 0.96-1.05 vs gold retraining). Note: if "
                "you still hold the original gold labels, plain retraining "
                "dominates refresh on compute")
            if m.gold_labels_retained:
                r.warnings.append(
                    "gold labels are retained -- RETRAIN costs less compute "
                    "than teacher-relabel refresh; refresh chosen only if "
                    "annotation-freshness matters to you")
            return r
        r.reasons.append("refresh measured but fails a gate")
    elif m.inputs_retained and m.refresh_score is None:
        r.reasons.append(
            "inputs are retained but no refresh student was trained/measured; "
            "RETRAIN recommended now, or run `upgrade-advisor refresh` first")

    # ---- Step 4: retrain --------------------------------------------------
    r.action = Action.RETRAIN
    r.reasons.append(
        f"upgrade opportunity is {gain*100:.2f}pp > epsilon and no cheaper "
        "path passed its gates: retrain on gold labels with the fixed recipe")
    if m.task_kind == "structured":
        r.warnings.append(
            "structured tasks showed no benefit from small label budgets in "
            "the paper (256 labels bought nothing on text-to-SQL; 95% of the "
            "gain needed >4096) -- budget labels accordingly")
    return r
